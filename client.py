import socket
import threading
import msvcrt


HOST = '127.0.0.1'
PORT = 8080
BUFFER_SIZE = 1024
COMMANDS = {
    "chat": "1",
    "promote": "2",
    "kick": "3",
    "mute": "4",
    "private": "5",
    "quit": "6",
    "view-admins": "7",
}
exit_event = threading.Event()



my_username = input("Enter your username (maximum 99 characters, no spaces and can't start with '@' or '!' ")
while len(my_username) >= 99 or my_username.startswith("@") or my_username.startswith("!") or ' ' in my_username:
    print("username isn't valid")
    my_username = input("Enter your username (maximum 99 characters, no spaces and can't start with '@' or '!' ")



def help():
    help_text = """
    Available commands for everyone:
    /private user message   Sends a private message to user
    /help                   Show commands
    /view-admins            View all admins
    /quit                   Exit chat  
    ------------------------------------------------------------
    Available commands for admins only:
    /promote user           Promote a user to manager
    /kick user              Remove a user from the chat
    /mute user              Prevent a user from sending messages
    """
    print(help_text)


def pack_msg(username, command, content):
    username = username.encode()
    content = content.encode()
    username_length = f"{len(username):02}".encode()  # Username length (2 characters)
    content_length = f"{len(content):03}".encode()  # Message length (3 characters)
    return username_length + username + command.encode() + content_length + content


def send_msg(server_socket):
    welcome_msg = pack_msg(my_username, COMMANDS["chat"], "has joined the chat!")
    server_socket.send(welcome_msg)

    user_input = ""
    print("\nType /help to show available commands", flush=True)

    while not exit_event.is_set():
        if msvcrt.kbhit():
            char = msvcrt.getch().decode('utf-8')
            if char == '\r':
                if user_input.lower() == "/quit":
                    msg = pack_msg(my_username, COMMANDS["quit"], user_input)
                    server_socket.send(msg)
                    break

                if user_input.lower() == "/help":
                    help()
                    user_input = ""
                    print("\n> ", end='', flush=True)

                elif user_input.lower() == "/view-admins":
                    msg = pack_msg(my_username, COMMANDS["view-admins"], user_input)
                    server_socket.send(msg)

                elif user_input.startswith('/'):
                    msg_parts = user_input.split(' ', 2)
                    command = msg_parts[0].lower()
                    target_user = None

                    if len(msg_parts) > 1:
                        target_user = msg_parts[1]

                    if len(msg_parts) > 2 and command[1:].lower() == "private":
                        private_msg = msg_parts[2]
                        msg = pack_msg(my_username, COMMANDS["private"], f"{target_user} {private_msg}")
                        server_socket.send(msg)

                    elif target_user:
                        if command[1:].lower() in COMMANDS.keys():
                            msg = pack_msg(my_username, COMMANDS[command[1:].lower()], target_user)
                            server_socket.send(msg)
                    else:
                        print(f"\nInvalid command or missing username: {user_input}")

                else:
                    msg = pack_msg(my_username, COMMANDS["chat"], user_input)
                    server_socket.send(msg)

                user_input = ""
                print("\n> ", end='', flush=True)

            elif char == '\b':
                if user_input:
                    user_input = user_input[:-1]  # Remove last character from input buffer
                    print(f"\r> {user_input} ", end='', flush=True)
            else:
                user_input += char  # Append the typed character
                print(f"\r> {user_input}", end='', flush=True)
    server_socket.close()


def receive_msg(server_socket):
    while not exit_event.is_set():
        try:
            msg = server_socket.recv(BUFFER_SIZE).decode()
            if msg:
                print(f"\r{msg[3:]}\n> ", end='', flush=True)
                if msg[3:] == "You have been kicked from the chat!":
                    exit_event.set()
            '''else:
                print("ss")
                server_socket.close()
                break'''
        except OSError:
            break

    server_socket.close()


def start_client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        receive_thread = threading.Thread(target=receive_msg, args=(client_socket,))
        send_thread = threading.Thread(target=send_msg, args=(client_socket,))

        receive_thread.start()
        send_thread.start()

        receive_thread.join()
        send_thread.join()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    start_client()

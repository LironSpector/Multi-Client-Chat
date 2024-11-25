import socket
import datetime
import threading

# Server configuration
HOST = "127.0.0.1"
PORT = 8080
BUFFER_SIZE = 1024

admins = ['liron', 'admin', 'nadavmit']
muted_users = set()
clients = {}
address = {}


def socket_by_username(client_username):
    """
    Retrieves the socket associated with a given username.

    Args:
        client_username (str): The username to find.

    Returns:
        socket: The client's socket if found, None otherwise.
    """
    for client_socket, username in clients.items():
        if username == client_username:
            return client_socket
    return None


def remove_client(client_socket):
    """
    Removes a client from the chat, closes their socket, and notifies others.

    Args:
        client_socket (socket): The socket of the client to remove.
    """
    if client_socket in clients:
        client_username = clients.pop(client_socket)
        client_address = address.pop(client_socket)
        if client_username in muted_users:
            muted_users.remove(client_username)
        print(f"client disconnected: {client_address}")
        msg = f"{get_time()} {client_username} has left the chat!"
        broadcast_msg(msg)
        try:
            client_socket.close()
            print(f"connection closed {client_address}")
        except Exception:
            print(f"connection couldn't be closed {client_address}")


def send_msg(client_socket, msg, sender_username=None):
    """
    Sends a message to a specific client socket.

    Args:
        client_socket (socket): The target client's socket.
        msg (str): The message to send.
        sender_username (str, optional): The username of the sender. Defaults to None.
    """
    if sender_username is not None and sender_username in admins:
        sender_username = "@" + sender_username
    if sender_username is not None:
        time = get_time()
        msg = f"{time} {sender_username} {msg}"

    try:
        msg_len = str(len(msg)).zfill(3)
        msg = msg_len + msg
        client_socket.send(msg.encode())
    except Exception:
        remove_client(client_socket)


def broadcast_msg(msg, sender_username=None):
    """
    Broadcasts a message to all connected clients except the sender.

    Args:
        msg (str): The message to broadcast.
        sender_username (str, optional): The username of the sender. Defaults to None.
    """
    for client_socket, username in clients.items():
        if clients[client_socket] != sender_username:
            try:
                send_msg(client_socket, msg, sender_username)
            except Exception as e:
                print(e)
                remove_client(client_socket)


def private_msg(private_msg, address_username, sender_username):
    """
    Sends a private message from one user to another.

    Args:
        private_msg (str): The message content.
        address_username (str): The recipient's username.
        sender_username (str): The sender's username.
    """
    sender_socket = socket_by_username(sender_username)
    if address_username not in clients.values():
        msg = f"User {address_username} doesn't exist"
        send_msg(sender_socket, msg)
    else:
        address_socket = socket_by_username(address_username)
        send_msg(address_socket, private_msg, f"!{sender_username}")


def kick_user(kicked_username, kicker_username):
    """
    Removes a user from the chat.

    Args:
        kicked_username (str): The username of the user to remove.
        kicker_username (str): The username of the admin performing the kick.
    """
    if kicked_username not in clients.values():
        msg = f"User {kicked_username} doesn't exist"
        kicker_socket = socket_by_username(kicker_username)
        send_msg(kicker_socket, msg)
    else:
        kicked_socket = socket_by_username(kicked_username)
        send_msg(kicked_socket, "You have been kicked from the chat!")
        broadcast_msg(f"{kicked_username} has been kicked from the chat!")
        remove_client(kicked_socket)


def mute_user(muted_username, admin_username):
    """
    Mutes a user in the chat.

    Args:
        muted_username (str): The username of the user to mute.
        admin_username (str): The username of the admin performing the mute.
    """
    if muted_username not in clients.values():
        msg = f"User {muted_username} doesn't exist"
        admin_socket = socket_by_username(admin_username)
        send_msg(admin_socket, msg)
    elif muted_username in muted_users:
        msg = f"User {muted_username} is already muted"
        admin_socket = socket_by_username(admin_username)
        send_msg(admin_socket, msg)
    else:
        muted_users.add(muted_username)
        muted_socket = socket_by_username(muted_username)
        send_msg(muted_socket, f"You have been muted by @{admin_username}")
        broadcast_msg(f"{muted_username} has been muted!")


def promote_user(promoted_username, admin_username):
    """
    Promotes a user to admin.

    Args:
        promoted_username (str): The username of the user to promote.
        admin_username (str): The username of the admin performing the promotion.
    """
    if promoted_username not in clients.values():
        msg = f"User {promoted_username} doesn't exist"
        admin_socket = socket_by_username(admin_username)
        send_msg(admin_socket, msg)
    elif promoted_username in admins:
        msg = f"User {promoted_username} is already an admin"
        admin_socket = socket_by_username(admin_username)
        send_msg(admin_socket, msg)
    else:
        admins.append(promoted_username)
        promoted_socket = socket_by_username(promoted_username)
        send_msg(promoted_socket, f"You have been promoted by @{admin_username}")
        broadcast_msg(f"{promoted_username} has been promoted!")


def view_admins(client_username):
    """
    Displays the list of admins to a user.

    Args:
        client_username (str): The username of the client requesting the admin list.
    """
    msg = f"Managers List\n----------\n"
    for admin in admins:
        msg += (admin + "\n")
    msg += "----------\n"
    send_msg(socket_by_username(client_username), msg)


def is_admin(client_username):
    """
    Checks if a user is an admin.

    Args:
        client_username (str): The username to check.

    Returns:
        bool: True if the user is an admin, False otherwise.
    """
    if client_username not in admins:
        client_socket = socket_by_username(client_username)
        send_msg(client_socket, "Only admins can use this command")
        return False
    return True


def is_muted(client_username):
    """
    Checks if a user is muted.

    Args:
        client_username (str): The username to check.

    Returns:
        bool: True if the user is not muted, False otherwise.
    """
    if client_username in muted_users:
        client_socket = socket_by_username(client_username)
        send_msg(client_socket, "You are muted")
        return False
    return True


def get_time():
    """
    Gets the current time in HH:MM format.

    Returns:
        str: The current time.
    """
    return datetime.datetime.now().strftime("%H:%M")


def unpack_msg(msg):
    """
    Unpacks a received message into its components.

    Args:
        msg (bytes): The message to unpack.

    Returns:
        tuple: A tuple containing username, command, and content.
    """
    try:
        username_length = int(msg[:2].decode())
        username = msg[2:2 + username_length].decode()
        command = msg[2 + username_length:2 + username_length + 1].decode()
        content_length = int(msg[2 + username_length + 1:2 + username_length + 4].decode())
        content = msg[2 + username_length + 4:2 + username_length + 4 + content_length].decode()
        return username, command, content
    except (ValueError, IndexError):
        return None, None, None


def handle_commands(client_username, command, content, exit_event):
    """
    Handles commands sent by clients.

    Args:
        client_username (str): The username of the client sending the command.
        command (str): The command code.
        content (str): The content of the command.
        exit_event (threading.Event): An event to signal exit.
    """
    if command == "2" and is_admin(client_username):
        promote_user(content.strip(), client_username)
    elif command == "3" and is_admin(client_username):
        kick_user(content.strip(), client_username)
    elif command == "4" and is_admin(client_username):
        mute_user(content.strip(), client_username)
    elif command == "5" and is_muted(client_username):
        address_username, msg = content.split(maxsplit=1)
        private_msg(msg, address_username, client_username)
    elif command == "6":
        exit_event.set()
        remove_client(client_username)
    elif command == "7":
        view_admins(client_username)
    elif command == "1" and is_muted(client_username):
        broadcast_msg(content, client_username)


def handle_client(client_socket, exit_event):
    """
    Handles communication with a single client.

    Args:
        client_socket (socket): The client's socket.
        exit_event (threading.Event): An event to signal exit.
    """
    while not exit_event.is_set():
        try:
            msg = client_socket.recv(BUFFER_SIZE)
            client_username, command, content = unpack_msg(msg)
            if client_socket not in clients.keys():
                clients[client_socket] = client_username
            handle_commands(client_username, command, content, exit_event)
        except Exception:
            exit_event.set()
            remove_client(client_socket)

    remove_client(client_socket)


def start_server():
    """
    Starts the chat server and listens for incoming connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"started server on {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"new connection {client_address}")
        address[client_socket] = client_address

        exit_event = threading.Event()
        threading.Thread(target=handle_client, args=(client_socket, exit_event)).start()


if __name__ == "__main__":
    start_server()

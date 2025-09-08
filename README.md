# Multi-Client Chat (Python Sockets)

A multi‑client chat written in **Python**. A threaded **server** accepts many **clients**: each client can chat publicly, send private messages, and (if admin) manage users.

## Features
- **Multi‑client** text chat over TCP (localhost by default).
- **Roles**: admins can `/promote`, `/kick`, `/mute`.
- **Private messages**: `/private <user> <message>`.
- **Protocol**: length‑prefixed frames (the message format is this: [2-digit username length][username][1-char command][3-digit content length][content])

## Quick Start
```bash
# 1) Start the server (terminal 1)
python server.py

# 2) Start one or more clients (terminal 2+)
python client.py
```
Defaults: `HOST=127.0.0.1`, `PORT=8080`. Change these in both `server.py` and `client.py` if needed.

> **Note:** The client uses `msvcrt` for non‑blocking input, so it works on **Windows** only. On Linux/macOS, replace the input loop with a cross‑platform approach (e.g., `select`/`tty`/`curses`) or fall back to a blocking `input()` loop.

## Commands
For everyone:
```
/private <user> <message>   # Direct Message to a user
/help                       # Show available commands for help
/view-admins                # List current admins
/quit                       # Exit
```
Admins only:
```
/promote <user>             # Make user admin
/kick <user>                # Remove user
/mute <user>                # Prevent user from sending messages
```

## Structure
```
server.py   # Threaded TCP server, user management, broadcasting & direct messages
client.py   # Console client with non‑blocking input (Windows), command parser
```

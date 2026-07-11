# ____________________________________________GUI Based TCP Chat Application____________________________________________________

## Objective:
The objective of this assignment is to develop a GUI-based TCP Chat Application by integrating the networking concepts implemented in Assignment 5 with a user-friendly graphical interface using Python Tkinter and ttkbootstrap. The application allows multiple clients to communicate through a TCP server using both broadcast and private messaging while providing an intuitive chat interface.

### Software Requirements:
- Arch Linux / Linux (Recommended)
- Python 3.10+
- Mininet
- Wireshark
- Tkinter
- ttkbootstrap
- Git

### Python Libraries:
- socket
- threading
- tkinter
- ttkbootstrap
- csv
- datetime
- os

Install ttkbootstrap using:
```bash
pip install ttkbootstrap
```

## Network Topology:
The application uses a **Single Switch Topology** in Mininet.

```
                     +-----------+
                     |  Server   |
                     |    h1     |
                     +-----------+
                            |
                         Switch
          __________________|__________________
         |             |           |           |
       Client1       Client2     Client3    Client4
         h2              h3        h4          h5
```
- **Server:** h1
- **Clients:** h2, h3, h4, h5
- **Protocol:** TCP
- **Port:** 5000


## Execution Steps:

### Step 1 – Start Mininet
```bash
sudo mn --topo single,4
```

### Step 2 – Open Server Terminal
```bash
xterm h1
```
Run:
```bash
python server.py
```

### Step 3 – Open Client Terminals
```bash
xterm h2 h3 h4 h5
```
Run on each client:
```bash
python client_gui.py
```

### Step 4 – Login
- Enter Username
- Click **Connect**
- 
### Step 5 – Chat
Features available:
- Broadcast Messages
- Private Messages
- Online Users List
- Chat History
- Join Notifications
- Leave Notifications
- Disconnect Button


## Sample Screenshots:

The screenshots are available in the **screenshots/** folder.
|     Screenshot   |     Description     |
|------------------|---------------------|
| login_window.png | Login Window |
| login_window_with_password.png | Login Interface |
| chat_interface.png | Main Chat Window |
| broadcast.png | Broadcast Messaging |
| private_message.png | Private Messaging |
| join_notification.png | User Joined Notification |
| leave_notification.png | User Left Notification |
| multiple_clients.png | Multiple Clients Connected |
| wireshark_connection.png | TCP Connection Capture |
| wireshark_messages.png | Message Transmission |


## -------------------------------Brief Description of the Implementation--------------------------------------------------
The project follows the Client–Server architecture.

### Server
The server is responsible for:
- Accepting multiple client connections.
- Maintaining the online user list.
- Broadcasting messages.
- Handling private messages.
- Saving chat history.
- Logging performance statistics.
- Sending the last five chat messages to newly connected clients.

### Client
The client application provides a graphical user interface developed using Tkinter and ttkbootstrap.
Features include:
- Login Window
- Chat Window
- Online Users Panel
- Conversation Panel
- Broadcast Messaging
- Private Messaging
- Dynamic Online User Updates
- Enter Key Support
- Send Button
- Disconnect Button

### Communication
Communication between clients and the server is performed using **TCP sockets**.
A dedicated receiving thread continuously listens for incoming messages while keeping the GUI responsive.

### Performance Features
- Multi-threaded Server
- Multi-threaded Client
- Online User Synchronization
- Chat History (CSV)
- Performance Logging
- Graceful Client Disconnect

## Folder Structure
```
Assignment-06-GUI-Based-TCP-Chat-Application
│
├── client_gui.py
├── server.py
├── requirements.txt
├── README.md
├── report.pdf
│
└── screenshots
    ├── login_window.png
    ├── login_window_with_password.png
    ├── chat_interface.png
    ├── broadcast.png
    ├── private_message.png
    ├── join_notification.png
    ├── leave_notification.png
    ├── multiple_clients.png
    ├── wireshark_connection.png
    └── wireshark_messages.png
```

## Features
- GUI-based Chat Application
- TCP Client-Server Communication
- Multiple Client Support
- Broadcast Messaging
- Private Messaging
- Dynamic Online User List
- Chat History
- Disconnect Support
- Responsive GUI using Threads

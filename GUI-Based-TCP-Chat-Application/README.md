# Secured GUI Based TCP Chat Application

## Objective:
The objective of this assignment is to enhance the GUI-based TCP Chat Application developed in Assignment 6 by integrating fundamental cybersecurity concepts. The application now supports secure user authentication, password hashing, duplicate login prevention, account lockout after multiple failed login attempts, automatic session timeout, and security event logging while maintaining real-time TCP communication through a graphical interface.

### Software Requirements:
- Arch Linux / Linux (Recommended)
- Python 3.10+
- Mininet
- Wireshark
- Tkinter
- ttkbootstrap
- Git
- hashlib

### Python Libraries:
- socket
- threading
- tkinter
- ttkbootstrap
- csv
- datetime
- os
- hashlib
- time

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
- Enter Username and Password
- Click Connect
- Only authenticated users are allowed to access the chat window.
- Duplicate logins are rejected.
- Invalid credentials are denied.
- Accounts are temporarily blocked after five consecutive failed login attempts.

### Step 5 - Security Features
The following security mechanisms have been implemented:
- Username and Password Authentication
- SHA-256 Password Hashing
- Secure Password Storage in users.csv
- Duplicate Login Prevention
- Maximum 5 Failed Login Attempts
- Temporary Account Lock for 30 Seconds
- Automatic Session Timeout after Inactivity
- Security Event Logging
- User Registration Utility (create_users.py)

### Step 6 – Chat
Features available:
- Broadcast Messages
- Private Messages
- Online Users List
- Chat History
- Join Notifications
- Leave Notifications
- Disconnect Button
- Automatic Logout after Session Timeout
- Login Authentication
- Duplicate Login Detection


## Sample Screenshots:

The screenshots are available in the **screenshots/** folder.
|     Screenshot   |     Description     |
|------------------|---------------------|
| chat_interface.png | Main Chat Window |
| broadcast.png | Broadcast Messaging |
| private_message.png | Private Messaging |
| join_notification.png | User Joined Notification |
| leave_notification.png | User Left Notification |
| multiple_clients.png | Multiple Clients Connected |
| successful_login.png | Successful Login |
| invalid_password.png | Invalid Password |
| duplicate_login_fail.png | Duplicate Login Prevention |
| empty_passwd_error.png | Empty Password Validation |
| logout.png | Manual Logout |
| session_out.png | Automatic Session Timeout |
| successful_login_wireshark.png | Wireshark Capture of Successful Login |
| invalid_password_wireshark.png | Wireshark Capture of Failed Login |
| logout_wireshark.png | Wireshark Capture of Logout |
| session_out_wireshark.png | Wireshark Capture of Session Timeout |


## --------------Brief Description of the Implementation--------------
The project follows the Client–Server architecture.

### Server
The server is responsible for:
- Accepting multiple client connections
- User Authentication
- Password Verification using SHA-256
- Duplicate Login Detection
- Failed Login Tracking
- Temporary Account Blocking
- Session Timeout Monitoring
- Security Event Logging
- Maintaining Online Users
- Broadcast Messaging
- Private Messaging
- Chat History Storage
- Performance Logging

## Authentication Workflow

1. User enters username and password.
2. Client sends login request to the server.
3. Server verifies SHA-256 password hash.
4. If credentials are valid:
   - Login Successful
   - Chat window opens.
5. If credentials are invalid:
   - Login rejected.
6. After five failed attempts:
   - Account is blocked for 30 seconds.
7. Duplicate login attempts are rejected.
8. If the user remains inactive beyond the timeout period:
   - The server logs out the user automatically.

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
├── create_users.py
├── users.csv
├── security_log.txt
├── README.md
│
└── screenshots
    ├── chat_interface.png
    ├── broadcast.png
    ├── private_message.png
    ├── join_notification.png
    ├── leave_notification.png
    ├── multiple_clients.png
    ├── successful_login.png
    ├── successful_login_wireshark.png
    ├── invalid_password.png
    ├── invalid_password_wireshark.png
    ├── empty_passwd_error.png
    ├── empty_passwd_error_wireshark.png
    ├── duplicate_login_fail.png
    ├── logout.png
    ├── logout_wireshark.png
    ├── session_out.png
    └── session_out_wireshark.png
    
  
```

## Features

### Networking

- TCP Client-Server Communication
- Multiple Client Support
- Broadcast Messaging
- Private Messaging
- Online User Synchronization
- Chat History

### GUI

- Tkinter + ttkbootstrap Interface
- Login Window
- Chat Window
- Online Users Panel
- Conversation Panel
- Disconnect Button

### Security

- User Authentication
- SHA-256 Password Hashing
- Duplicate Login Prevention
- Failed Login Tracking
- Temporary Account Blocking
- Session Timeout
- Security Logging
- User Registration Utility

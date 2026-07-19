import socket
import threading
import csv
import time
from datetime import datetime
import os
import hashlib
import json

with open("config.json", "r") as file:
    config = json.load(file)

HOST = config["HOST"]
PORT = config["PORT"]
BUFFER_SIZE = config["BUFFER_SIZE"]

clients = []
usernames = {}
client_ips = {}
client_ports = {}
login_times = {}
status = {}

clients_lock = threading.Lock()

message_count = 0
broadcast_count = 0
private_count = 0
start_time = None
end_time = None
stats_lock = threading.Lock()

# -----------------------------
# Failed Login Protection
# -----------------------------
MAX_FAILED_ATTEMPTS = config["MAX_FAILED_ATTEMPTS"]
BLOCK_DURATION = config["BLOCK_DURATION"]
SESSION_TIMEOUT = config["SESSION_TIMEOUT"]

failed_attempts = {}
blocked_until = {}

#---------------------------------

HISTORY_FILE = "chat_history.csv"
RESULT_FILE = "performance_results.csv"
USER_FILE = "users.csv"
SECURITY_LOG_FILE = "security_log.txt"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
    
def load_users():
    users = {}
    try:
        with open(USER_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                username = row["username"]
                password_hash = row["password_hash"]
                users[username] = password_hash

    except FileNotFoundError:
        print("ERROR: users.csv not found!")

    return users
    
users_db = load_users()


def authenticate_user(username, password):
    if username not in users_db:
        return False

    entered_password_hash = hash_password(password)
    stored_password_hash = users_db[username]

    return entered_password_hash == stored_password_hash

def is_user_blocked(username):
    if username not in blocked_until:
        return False
    return time.time() < blocked_until[username]

def record_failed_attempt(username):
    failed_attempts[username] = (failed_attempts.get(username, 0) + 1)
    if failed_attempts[username] >= MAX_FAILED_ATTEMPTS:
        blocked_until[username] = (time.time() + BLOCK_DURATION)
        failed_attempts[username] = 0
        return True
    return False
    
def reset_failed_attempts(username):
    failed_attempts.pop(username, None)
    
def is_user_logged_in(username):
    with clients_lock:
        return username in usernames.values()

#-----file checking---------
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE,"w",newline="") as f:
        csv.writer(f).writerow(["time","sender","receiver","type","message"])
        
if not os.path.exists(SECURITY_LOG_FILE):
    open(SECURITY_LOG_FILE, "w").close()

if not os.path.exists(RESULT_FILE):
    with open(RESULT_FILE,"w",newline="") as f:
        csv.writer(f).writerow(["online_clients","total_messages","broadcast_messages","private_messages","average_delay_ms","throughput_msg_per_sec"])

def save_history(sender,receiver,msg_type,message):
    with open(HISTORY_FILE,"a",newline="") as f:
        csv.writer(f).writerow([datetime.now().strftime("%H:%M:%S"),sender,receiver,msg_type,message])
        
def security_log(event, username, ip):
    with open(SECURITY_LOG_FILE, "a") as file:
        file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "f"{event} | "f"User={username} | "f"IP={ip}\n")

def send_history(client):
    try:
        with open(HISTORY_FILE) as f:
            rows=f.readlines()[1:]
        client.send(b"\n--- Last 5 Messages ---\n")
        for r in rows[-5:]:
            client.send(r.strip().encode()+b"\n")
        client.send(b"------------------------\n")
    except:
        pass


def broadcast(message):
    disconnected = []
    with clients_lock:
        client_list = list(clients)
        
    for c in client_list:
        try:
            c.send((message + "\n").encode())
        except:
            disconnected.append(c)
    for c in disconnected:
        with clients_lock:
            username = usernames.get(c)
        cleanup_client(c, username)


def send_online_users():
    with clients_lock:
        names = ",".join(usernames[c] for c in clients)
        client_list = list(clients)
        
    message = f"[USERS]{names}\n"
    disconnected = []
    for c in client_list:
        try:
            c.send(message.encode())
        except:
            disconnected.append(c)
    for c in disconnected:
        with clients_lock:
            username = usernames.get(c)
        cleanup_client(c, username)


def send_private(sender_client,receiver,message):
    global private_count,message_count
    
    with clients_lock:
        sender = usernames.get(sender_client, "Unknown")
        client_list = list(clients)
        usernames_copy = dict(usernames)
        
    with stats_lock:
        message_count += 1
        current_msg_count = message_count
        
    if current_msg_count == 50:
        write_results()
        
    for c in client_list:
        if usernames_copy.get(c) == receiver:
            c.send(f"[PRIVATE] {sender}: {message}\n".encode())
            sender_client.send(f"[To {receiver}] {message}\n".encode())
            with stats_lock:
                private_count += 1
            save_history(sender,receiver,"Private",message)
            return
    sender_client.send(b"User not found.\n")
    
    

def write_results():
    global message_count
    global broadcast_count
    global private_count
    global start_time
    global end_time
    
    with stats_lock:
        if start_time is None or end_time is None or message_count == 0:
            return
            
        total = max(end_time - start_time, 0.001)
        avg = (total / message_count) * 1000
        throughput = message_count / total
        
        # Reset for next experiment
        current_mc = message_count
        current_bc = broadcast_count
        current_pc = private_count
        message_count = 0
        broadcast_count = 0
        private_count = 0
        start_time = None
        end_time = None
        
    with clients_lock:
        num_clients = len(clients)
        
    with open(RESULT_FILE, "a", newline="") as f:
        csv.writer(f).writerow([num_clients, current_mc, current_bc, current_pc, round(avg, 2), round(throughput, 2)])
        print("Performance Saved")
    
    

def cleanup_client(client, username=None):
    """Safely remove a disconnected client."""

    if username:
        broadcast(f"[SERVER] {username} left the chat.")

    with clients_lock:
        if client in clients:
            clients.remove(client)

        usernames.pop(client, None)
        client_ips.pop(client, None)
        client_ports.pop(client, None)
        login_times.pop(client, None)
        status.pop(client, None)
    
    try:
        client.shutdown(socket.SHUT_RDWR)
    except:
        pass
        
    try:
        client.close()
    except:
        pass
        
    send_online_users()



def handle_client(client, addr):
    global start_time
    global end_time
    global message_count
    global broadcast_count

    username = None
    try:
        # Receive login request
        login_data = client.recv(BUFFER_SIZE).decode()

        # Expected format:
        # LOGIN|username|password
        parts = login_data.split("|",2)
        
        if len(parts) != 3:
            client.send(b"LOGIN_FAILED")
            client.close()
            return

        command = parts[0]
        username = parts[1]
        password = parts[2]
        
        # Check if account is temporarily blocked
        if is_user_blocked(username):
            print(f"{username} is temporarily blocked.")
            security_log("ACCOUNT_BLOCKED",username,addr[0])
            client.send(b"ACCOUNT_BLOCKED")
            client.close()
            return

        if command != "LOGIN":
            client.send(b"LOGIN_FAILED")
            client.close()
            return

        # Authenticate user
        if not authenticate_user(username, password):
            print(f"Failed login attempt for {username} from {addr[0]}")
            security_log("LOGIN_FAILED",username,addr[0])
            blocked = record_failed_attempt(username)
            if blocked:
                print(f"{username} has been blocked.")
                client.send(b"ACCOUNT_BLOCKED")
            else:
                client.send(b"LOGIN_FAILED")
            client.close()
            return
            
        if is_user_logged_in(username):
            print(f"Duplicate login attempt for {username} from {addr[0]}")
            security_log("DUPLICATE_LOGIN",username,addr[0])
            client.send(b"DUPLICATE_LOGIN")
            client.close()
            return

        # Authentication successful
        reset_failed_attempts(username)
        client.send(b"LOGIN_SUCCESS")

        # Add authenticated client
        with clients_lock:
            clients.append(client)
            usernames[client] = username
            client_ips[client] = addr[0]
            client_ports[client] = addr[1]
            login_times[client] = (datetime.now().strftime("%H:%M:%S"))
            status[client] = "Online"
            
        last_activity = time.time()
        print(f"{username} authenticated and connected from {addr[0]}:{addr[1]}")
    
        security_log("LOGIN_SUCCESS",username,addr[0])
        
        
    except Exception as e:
        print("Authentication Error:",e)
        client.close()
        return
    #   login checked
#------------------------------------------
    send_history(client)
    broadcast(f"[SERVER] {username} joined the chat.")
    send_online_users()
    client.settimeout(1)

    while True:
        try:
            
            try:
                data = client.recv(BUFFER_SIZE).decode()

            except socket.timeout:
                # Check if user has been inactive for too long
                if time.time() - last_activity >= SESSION_TIMEOUT:
                    print(f"{username} session timed out.")
                    security_log(
                        "SESSION_TIMEOUT",
                        username,
                        addr[0]
                    )

                    break
                continue
            
            if not data:
                break
            
            last_activity = time.time()

            # Client requested logout
            if data == "LOGOUT":
                print(f"{username} logged out.")
                security_log(
                    "LOGOUT",
                    username,
                    addr[0])
                break

            with stats_lock:
                if start_time is None:
                    start_time = time.time()
                end_time = time.time()

            if data == "/list":
                send_online_users()

            elif data.startswith("/msg "):
                p = data.split(" ", 2)
                if len(p) == 3:
                    send_private(client, p[1], p[2])

            else:
                with stats_lock:
                    message_count += 1
                    broadcast_count += 1
                    current_msg_count = message_count
                    
                text = f"[{username}] {data}"
                print(text)
                broadcast(text)
                save_history(username, "ALL", "Broadcast", data)
                
                if current_msg_count == 50:
                    write_results()
            
        except ConnectionResetError:
            print(f"{username} disconnected unexpectedly.")
            security_log("CONNECTION_RESET", username, addr[0])
            break

        except ConnectionAbortedError:
            print(f"{username} aborted the connection.")
            security_log("CONNECTION_ABORTED", username, addr[0])
            break

        except Exception as e:
            print(f"Unexpected error with {username}: {e}")
            security_log("SERVER_ERROR", username, addr[0])
            break

    cleanup_client(client, username)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print("Server Started...")
print("Waiting for clients...")

try:
    while True:
        client, addr = server.accept()
        threading.Thread(
            target=handle_client,
            args=(client, addr),
            daemon=True
        ).start()

except KeyboardInterrupt:

    print("\nStopping server...")
    
    with clients_lock:
        client_list = list(clients)

    for c in client_list:

        try:
            c.send(b"[SERVER] Server shutting down.\n")
        except:
            pass
        
        with clients_lock:
            username = usernames.get(c)
        cleanup_client(c, username)

    server.close()

    print("Server stopped successfully.")

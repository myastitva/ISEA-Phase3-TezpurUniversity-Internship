import socket
import threading
import csv
import time
from datetime import datetime
import os
import hashlib

HOST = "10.0.0.1"
PORT = 5000

clients = []
usernames = {}
client_ips = {}
client_ports = {}
login_times = {}
status = {}

message_count = 0
broadcast_count = 0
private_count = 0
start_time = None
end_time = None

# -----------------------------
# Failed Login Protection
# -----------------------------
MAX_FAILED_ATTEMPTS = 5
BLOCK_DURATION = 30 # seconds (change to 60 before submission)
SESSION_TIMEOUT = 20     # seconds

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
    for c in clients:
        try:
            c.send((message+"\n").encode())
        except:
            pass

def send_online_users():
    names = ",".join(usernames[c] for c in clients)
    message = f"[USERS]{names}\n"
    for c in clients:
        try:
            c.send(message.encode())
        except:
            pass

def send_private(sender_client,receiver,message):
    global private_count,message_count
    sender=usernames[sender_client]
    message_count += 1
    if message_count==50:
        write_results()
    for c in clients:
        if usernames[c]==receiver:
            c.send(f"[PRIVATE] {sender}: {message}\n".encode())
            sender_client.send(f"[To {receiver}] {message}\n".encode())
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
    if start_time is None or end_time is None or message_count==0:
        return
    total=max(end_time-start_time,0.001)
    avg=(total/message_count)*1000
    throughput=message_count/total
    with open(RESULT_FILE,"a",newline="") as f:
        csv.writer(f).writerow([len(clients),message_count,broadcast_count,private_count,round(avg,2),round(throughput,2)])
        print("Performance Saved")

    # Reset for next experiment
    message_count = 0
    broadcast_count = 0
    private_count = 0
    start_time = None
    end_time = None

def handle_client(client, addr):
    global start_time
    global end_time
    global message_count
    global broadcast_count

    username = None
    try:
        # Receive login request
        login_data = client.recv(1024).decode()

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
                data = client.recv(1024).decode()

            except socket.timeout:
                # Check if user has been inactive for too long
                if time.time() - last_activity >= SESSION_TIMEOUT:
                    print(f"{username} session timed out.")
                    security_log("SESSION_TIMEOUT",username,addr[0])
                    break
                continue
            
            if not data:
                break
            
            last_activity = time.time()

            # Client requested logout
            if data == "LOGOUT":
                print(f"{username} logged out.")security_log("LOGOUT",username,addr[0])
                break

            if start_time is None:
                start_time=time.time()
                
            end_time=time.time()

            if data=="/list":
                send_online_users()

            elif data.startswith("/msg "):
                p=data.split(" ",2)
                if len(p)==3:
                    send_private(client,p[1],p[2])

            else:
                message_count += 1
                broadcast_count += 1
                text=f"[{username}] {data}"
                print(text)
                broadcast(text)
                save_history(username,"ALL","Broadcast",data)
                if message_count == 50:
                    write_results()

        except:
            break

    broadcast(f"[SERVER] {username} left the chat.")
    
    if client in clients:
        clients.remove(client)

    usernames.pop(client,None)
    send_online_users()
    client_ips.pop(client,None)
    client_ports.pop(client,None)
    login_times.pop(client,None)
    status.pop(client,None)
    client.close()

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.bind((HOST,PORT))
server.listen()

print("Server Started...")
print("Waiting for clients...")

while True:
    client,addr=server.accept()
    threading.Thread(target=handle_client,args=(client,addr),daemon=True).start()

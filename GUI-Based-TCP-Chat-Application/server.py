import socket
import threading
import csv
import time
from datetime import datetime
import os

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

HISTORY_FILE = "chat_history.csv"
RESULT_FILE = "performance_results.csv"

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE,"w",newline="") as f:
        csv.writer(f).writerow(["time","sender","receiver","type","message"])

if not os.path.exists(RESULT_FILE):
    with open(RESULT_FILE,"w",newline="") as f:
        csv.writer(f).writerow(["online_clients","total_messages","broadcast_messages","private_messages","average_delay_ms","throughput_msg_per_sec"])

def save_history(sender,receiver,msg_type,message):
    with open(HISTORY_FILE,"a",newline="") as f:
        csv.writer(f).writerow([datetime.now().strftime("%H:%M:%S"),sender,receiver,msg_type,message])

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

def handle_client(client,addr):
    global start_time,end_time,message_count,broadcast_count

    username=client.recv(1024).decode()
    clients.append(client)
    usernames[client]=username
    client_ips[client]=addr[0]
    client_ports[client]=addr[1]
    login_times[client]=datetime.now().strftime("%H:%M:%S")
    status[client]="Online"

    print(f"{username} connected from {addr[0]}:{addr[1]}")
    send_history(client)
    broadcast(f"[SERVER] {username} joined the chat.")
    send_online_users()

    while True:
        try:
            data=client.recv(1024).decode()
            if not data:
                break

            if start_time is None:
                start_time=time.time()
            end_time=time.time()

            if data=="/list":
                send_online_users(client)

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

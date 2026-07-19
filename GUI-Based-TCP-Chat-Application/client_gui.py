import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import socket
import threading
import time
import json

with open("config.json", "r") as file:
    config = json.load(file)

SERVER_IP = config["HOST"]
PORT = config["PORT"]
BUFFER_SIZE = config["BUFFER_SIZE"]

client = None
connected = False
reconnecting = False
current_username = ""
current_password = ""




def connect_to_server(username, password):
    global client
    global connected
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    login_data = f"LOGIN|{username}|{password}"
    client.send(login_data.encode())
    response = client.recv(BUFFER_SIZE).decode()
    if response == "LOGIN_SUCCESS":
        connected = True
    return response



def send_message():
    message = message_entry.get().strip()
    if not message:
        return
    receiver = recipient_box.get()
    try:
        if receiver == "Everyone":
            client.send(message.encode())
        else:
            client.send(
                f"/msg {receiver} {message}".encode()
            )
        message_entry.delete(0, tk.END)
    except (BrokenPipeError, ConnectionResetError, OSError):
        start_reconnect()

    except Exception as e:
        messagebox.showerror(
            "Send Error",
            str(e)
        )



def receive_messages():
    global connected

    buffer = ""

    while connected:
        try:
            data = client.recv(BUFFER_SIZE).decode()

            if not data:
                start_reconnect()
                break

            buffer += data

            while "\n" in buffer:

                message, buffer = buffer.split("\n", 1)
                message = message.strip()

                if not message:
                    continue

                # -------------------------------
                # Online Users
                # -------------------------------
                if message.startswith("[USERS]"):

                    names = message.replace("[USERS]", "").strip()

                    if names:
                        user_list = [
                            u.strip()
                            for u in names.split(",")
                            if u.strip()
                        ]
                    else:
                        user_list = []

                    def update_users(users=user_list):
                        try:
                            if not chat.winfo_exists():
                                return

                            users_list.delete(0, tk.END)

                            for user in users:
                                users_list.insert(tk.END, user)

                            recipient_box["values"] = ["Everyone"] + users
                            recipient_box.current(0)

                        except:
                            pass

                    try:
                        chat.after(0, update_users)
                    except:
                        pass

                # -------------------------------
                # Chat Messages
                # -------------------------------
                else:

                    def update_chat(msg=message):
                        try:
                            if not chat.winfo_exists():
                                return

                            chat_box.config(state="normal")
                            chat_box.insert(tk.END, msg + "\n")
                            
                            # Scalability enhancement: limit chat history to prevent memory issues
                            lines = int(chat_box.index('end-1c').split('.')[0])
                            if lines > 1000:
                                chat_box.delete('1.0', f'{lines-1000 + 1}.0')
                                
                            chat_box.see(tk.END)
                            chat_box.config(state="disabled")

                        except:
                            pass

                    try:
                        chat.after(0, update_chat)
                    except:
                        pass

        except (ConnectionResetError, ConnectionAbortedError, OSError):

            if connected:
                start_reconnect()

            break

        except Exception:
            break
            
    
# --------------------------------------------------
# Login Button Function
# --------------------------------------------------
def login(auto=False):
    global client
    global current_username
    global current_password
    
    if auto:
        username = current_username
        password = current_password
    else:
        username = username_entry.get().strip()
        password = password_entry.get()

        current_username = username
        current_password = password

    # Username validation
    if username == "":

        messagebox.showerror(
            "Login Error",
            "Username cannot be empty!"
        )

        return

    # Password validation
    if password == "":

        messagebox.showerror(
            "Login Error",
            "Password cannot be empty!"
        )

        return

    try:

        status_label.config(
            text="Status : Connecting...",
            bootstyle="warning"
        )

        if auto:
            response = "LOGIN_SUCCESS"
        else:
            response = connect_to_server(
                username,
                password
            )
            
        if response == "LOGIN_SUCCESS":
            app.withdraw()

            password_entry.delete(
                0,
                tk.END
            )

            app.withdraw()

            open_chat_window(
                username
            )
        
        elif response == "DUPLICATE_LOGIN":

            status_label.config(
                text="Status : Login Failed",
                bootstyle="danger"
            )

            messagebox.showerror(
                "Login Failed",
                "This user is already logged in."
            )

            if client:

                client.close()

                client = None
                
        elif response == "ACCOUNT_BLOCKED":

            status_label.config(
                text="Status : Account Blocked",
                bootstyle="danger"
            )

            messagebox.showerror(
                "Account Blocked",
                "Too many failed login attempts.\n"
                "Please try again after 30 seconds."
                        )
            if client:
                client.close()
                client = None

        else:
            status_label.config(
                text="Status : Login Failed",
                bootstyle="danger"
            )

            messagebox.showerror(
                "Login Failed",
                "Invalid username or password."
            )

            if client:
                client.close()
                client = None

    except Exception as e:

        status_label.config(
            text="Status : Connection Failed",
            bootstyle="danger"
        )

        messagebox.showerror(
            "Connection Error",
            str(e)
        )


def auto_reconnect():
    global reconnecting
    for attempt in range(1, 4):
        app.after(
            0,
            lambda a=attempt:
                status_label.config(
                    text=f"Reconnecting... ({a}/3)",
                    bootstyle="warning"
                )
        )
        try:
            response = connect_to_server(
                current_username,
                current_password
            )
            if response == "LOGIN_SUCCESS":
                reconnecting = False
                app.after(
                    0,
                    lambda: login(auto=True)
                )
                return
        except:
            pass

        time.sleep(5)
    reconnecting = False
    app.after(
        0,
        lambda: status_label.config(
            text="Unable to reconnect.",
            bootstyle="danger"
        )
    )    
        
        
        
        
def disconnect():
    global client
    global chat
    global connected
    
    if not connected:
        return
    try:
        if client:
            try:
                client.send(b"LOGOUT")
            except:
                pass
            try:
                client.shutdown(socket.SHUT_WR)
            except:
                pass
            connected = False
            client.close()
            client = None
    except:
        pass
    try:
        if chat and chat.winfo_exists():
            chat.destroy()
    except:
        pass
    username_entry.delete(0, tk.END)
    password_entry.delete(0, tk.END)
    status_label.config(
        text="Status : Ready",
        bootstyle="secondary"
    )
    if not reconnecting:
        app.deiconify()
    

def connection_lost():
    global client
    global connected
    connected = False
    try:
        if client:
            client.close()
    except:
        pass
    client = None
    try:
        if chat and chat.winfo_exists():
            chat.destroy()
    except:
        pass
    app.deiconify()

def start_reconnect():
    global reconnecting
    if reconnecting:
        return
    reconnecting = True
    connection_lost()
    threading.Thread(
        target=auto_reconnect,
        daemon=True
    ).start()
    


# --------------------------------------------------
#  Chat Window
# --------------------------------------------------
def open_chat_window(username):
    global chat
    global chat_box
    global users_list
    global message_entry
    global recipient_box

    chat = ttk.Window(themename="darkly")
    chat.protocol("WM_DELETE_WINDOW",disconnect)
    chat.title(f"TCP Chat - {username}")
    chat.geometry("1100x700")
    chat.minsize(900, 600)

    # -------------------------------
    # Main Frame
    # -------------------------------
    main_frame = ttk.Frame(chat)
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # -------------------------------------------------
    # Header Frame
    # -------------------------------------------------
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 10))
    
    header_frame.columnconfigure(0, weight=1)
    header_frame.columnconfigure(1, weight=1)
    header_frame.columnconfigure(2, weight=1)

    app_name = ttk.Label(
        header_frame,
        text="💬 TCP Chat",
        font=("Segoe UI", 16, "bold")
    )

    app_name.grid(
        row=0,
        column=0,
        sticky="w"
    )

    user_label = ttk.Label(
        header_frame,
        text=f"User : {username}",
        font=("Segoe UI", 15)
    )

    user_label.grid(
        row=0,
        column=1
    )

    status_header = ttk.Label(
        header_frame,
        text="🟢 Connected",
        bootstyle="success",
        font=("Segoe UI", 12)
    )

    status_header.grid(
        row=0,
        column=2,
        sticky="e"
    )
    
    disconnect_button = ttk.Button(
    header_frame,
    text="Disconnect",
    bootstyle="danger",
    command=disconnect,
    width=12
    )

    disconnect_button.grid(
        row=1,
        column=2,
        sticky="e",
        pady=(5,0)
    )

    ttk.Separator(
        main_frame,
        orient="horizontal"
    ).pack(fill="x", pady=(5, 15))
    
    # -------------------------------------------------
    # Main Content (25% / 75% Split)
    # -------------------------------------------------
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True)

    # 25% for Online Users
    content_frame.columnconfigure(0, weight=1)

    # 75% for Chat Area
    content_frame.columnconfigure(1, weight=3)

    # Stretch vertically
    content_frame.rowconfigure(0, weight=1)
    
    # -------------------------------------------------
    # Online Users Panel
    # -------------------------------------------------
    users_frame = ttk.Labelframe(
        content_frame,
        text=" Online Users "
    )

    users_frame.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0,10)
    )

    users_frame.grid_propagate(False)

    # -------------------------------------------------
    # Online Users List
    # -------------------------------------------------
    users_scroll = ttk.Scrollbar(
        users_frame,
        orient="vertical"
    )
    
    users_list = tk.Listbox(
        users_frame,
        font=("Segoe UI", 11),
        bg="#2b2b2b",
        fg="white",
        selectbackground="#0d6efd",
        selectforeground="white",
        borderwidth=0,
        highlightthickness=0,
        activestyle="none",
        exportselection=False,
        yscrollcommand=users_scroll.set
    )

    users_scroll.config(command=users_list.yview)

    users_list.pack(
        side="left",
        fill="both",
        expand=True,
        padx=5,
        pady=5
    )

    users_scroll.pack(
        side="right",
        fill="y",
        pady=5
    )

    # -------------------------------------------------
    # Conversation Panel
    # -------------------------------------------------
    chat_frame = ttk.Labelframe(
        content_frame,
        text=" Conversation ",
        height=500
    )

    chat_frame.grid(
        row=0,
        column=1,
        sticky="nsew"
    )
    
    chat_frame.grid_propagate(False)
    
    # -------------------------------------------------
    # Conversation Area
    # -------------------------------------------------
    chat_box = ScrolledText(chat_frame,wrap="word",font=("Segoe UI", 11),state="normal")
    chat_box.pack(fill="both",expand=True,padx=10,pady=10)
    chat_box.config(state="disabled")
    
    # -------------------------------------------------
    # Bottom Controls Frame
    # -------------------------------------------------
    bottom_frame = ttk.Frame(main_frame)
    bottom_frame.pack(fill="x", pady=(12,8),padx=5)

    ttk.Label(bottom_frame,text="Send To:").pack(side="left", padx=(0,5))

    recipient_box = ttk.Combobox(bottom_frame,values=["Everyone"],state="readonly",width=15)
    recipient_box.current(0)
    recipient_box.pack(side="left",padx=(0,10))
    
    #SEND BUTTON
    message_entry = ttk.Entry(bottom_frame,font=("Segoe UI",11))
    message_entry.pack(side="left",fill="x",expand=True,padx=(0,10),ipady=5)
    message_entry.bind("<Return>",lambda event: send_message())
    ttk.Button(bottom_frame,text="Send",bootstyle="success",width=10,command=send_message).pack(side="left")
    
    # Separator
    ttk.Separator(main_frame,orient="horizontal").pack(fill="x", pady=(8,5))

    # Status Bar
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill="x")

    status_label = ttk.Label(status_frame,text="Ready",bootstyle="success")
    status_label.pack(side="left")

    connection_label = ttk.Label(status_frame,text="Server : Connected",bootstyle="success")
    connection_label.pack(side="right")

    thread = threading.Thread(target=receive_messages)
    thread.daemon = True
    thread.start()

    chat.mainloop()


#**********************************************LOGIN*********************************************
# Login Window
app = ttk.Window(themename="darkly")
app.title("TCP Chat Application")
app.geometry("420x350")
app.resizable(False, False)

# Title
ttk.Label(app,text="TCP Chat Application",font=("Segoe UI", 20, "bold")).pack(pady=(25, 20))

# Username
ttk.Label(app,text="Username").pack(anchor="w", padx=50)
username_entry = ttk.Entry(app,width=38)
username_entry.pack(pady=(5, 15))

# Password
ttk.Label(app,text="Password").pack(anchor="w", padx=50)
password_entry = ttk.Entry(app,width=38,show="*")
password_entry.pack(pady=(5, 20))

# Connect Button
ttk.Button(app,text="Connect",command=login,bootstyle="success").pack()

# Status
status_label = ttk.Label(app,text="Status : Ready",font=("Segoe UI", 10))
status_label.pack(pady=20)

# Run----------
app.mainloop()

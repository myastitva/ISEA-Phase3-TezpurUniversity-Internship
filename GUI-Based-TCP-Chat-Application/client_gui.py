import ttkbootstrap as ttk
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import socket
import threading

SERVER_IP = "10.0.0.1"
PORT = 5000

client = None

def connect_to_server(username):
    global client
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    client.send(username.encode())
    
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

    except Exception as e:

        messagebox.showerror(
            "Send Error",
            str(e)
        )

def receive_messages():
    buffer = ""
    while True:
        try:
            data = client.recv(1024).decode()
            if not data:
                break

            # Add newly received data to buffer
            buffer += data
            # Process one complete line at a time
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                message = message.strip()
                if not message:
                    continue

                # -------------------------------
                # Online Users Update
                # -------------------------------
                if message.startswith("[USERS]"):
                    names = message.replace("[USERS]", "").strip()
                    user_list = []
                    if names:
                        user_list = [u.strip() for u in names.split(",") if u.strip()]

                    # Update Online Users List
                    users_list.delete(0, tk.END)
                    for user in user_list:
                        users_list.insert(tk.END, user)

                    # Update Send To Combobox
                    recipient_box["values"] = ["Everyone"] + user_list

                    # Keep "Everyone" selected by default
                    recipient_box.current(0)

                # -------------------------------
                # Normal Chat Messages
                # -------------------------------
                else:
                    chat_box.config(state="normal")
                    chat_box.insert(tk.END,message + "\n")
                    chat_box.see(tk.END)
                    chat_box.config(state="disabled")

        except Exception as e:
            print("Receive Error:", e)
            break
# --------------------------------------------------
# Login Button Function
# --------------------------------------------------
def login():
    username = username_entry.get().strip()

    if username == "":
        messagebox.showerror("Login Error","Username cannot be empty!")
        return

    # Password is optional for now
    password = password_entry.get().strip()
    status_label.config(text="Status : Ready",bootstyle="success")
    print(f"Username : {username}")

    try:
        connect_to_server(username)
        app.withdraw()
        open_chat_window(username)
    
    except Exception as e:
        messagebox.showerror("Connection Error",str(e))
        
        
def disconnect():

    global client
    global chat

    try:
        if client:
            client.close()

    except:
        pass

    chat.destroy()

    app.deiconify()

# --------------------------------------------------
# Temporary Chat Window
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
ttk.Label(app,text="Password (Optional)").pack(anchor="w", padx=50)
password_entry = ttk.Entry(app,width=38,show="*")
password_entry.pack(pady=(5, 20))

# Connect Button
ttk.Button(app,text="Connect",command=login,bootstyle="success").pack()

# Status
status_label = ttk.Label(app,text="Status : Ready",font=("Segoe UI", 10))
status_label.pack(pady=20)

# Run----------
app.mainloop()

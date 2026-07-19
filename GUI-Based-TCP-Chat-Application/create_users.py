import csv
import hashlib
import os

USER_FILE = "users.csv"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Create users.csv if it doesn't exist
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["username", "password_hash"])


# Load existing users
users = {}

with open(USER_FILE, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        users[row["username"]] = row["password_hash"]


print("========== User Registration ==========\n")

username = input("Enter username: ").strip()

if username == "":
    print("Username cannot be empty.")
    exit()

if username in users:
    print("Username already exists.")
    exit()

password = input("Enter password: ").strip()

if password == "":
    print("Password cannot be empty.")
    exit()

password_hash = hash_password(password)

with open(USER_FILE, "a", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([username, password_hash])

print(f"\nUser '{username}' registered successfully.")

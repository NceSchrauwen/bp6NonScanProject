# BP6 Non-Scan Project - Login Page
# Author: Nina Schrauwen

import tkinter as tk
from tkinter import messagebox
# Import the Database class for login functionality
from WorkerDB import Database
# Import the NfcScannerApp class to be able to scan and identify NFC codes
from NfcScanner import NfcScannerApp

worker_name = ""

class LoginApp:
    def __init__(self, master):
        # Initialize the window
        self.master = master
        self.master.title("Jumbo Login")
        self.master.geometry("300x200")

        # Create the database object
        self.db = Database()

        # Username label and entry
        self.label_username = tk.Label(self.master, text="Worker ID:")
        self.label_username.pack(pady=5)
        self.entry_username = tk.Entry(self.master)
        self.entry_username.pack(pady=5)

        # Password label and entry
        self.label_password = tk.Label(self.master, text="Password:")
        self.label_password.pack(pady=5)
        self.entry_password = tk.Entry(self.master, show="*") # Hide password while typing
        self.entry_password.pack(pady=5)

        # Login button
        self.button_login = tk.Button(self.master, text="Login", command=self.login)
        self.button_login.pack(pady=10)

        # Bind the Enter key to the login function
        self.master.bind("<Return>", lambda event: self.login())

        # Exit button
        self.button_exit = tk.Button(self.master, text="Exit", command=self.master.quit)
        self.button_exit.pack(pady=10)

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter a worker ID and password.")
            return

        worker_name = self.db.validate_user(username, password)

        if worker_name:
            self.open_scanner(worker_name)  # Open the scanner window, only if the login is successful
        else:
            messagebox.showerror("Error", "Invalid worker ID or password.")

    def open_scanner(self, worker_name):
        # Destroy the login window
        self.master.destroy()
        root = tk.Tk()
        scanner_app = NfcScannerApp(root, worker_name)
        root.mainloop()

    def __del__(self):
        # Ensure database connection is closed when the app is terminated
        self.db.close_connection()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
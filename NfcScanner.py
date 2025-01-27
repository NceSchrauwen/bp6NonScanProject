# BP6 Non-Scan Project - NFC Scanner Class
# Author: Nina Schrauwen

import tkinter as tk
import requests
from tkinter import messagebox

# Unified database for all NFC codes
items_db = {
    "0x466aca1": {"name": "So American", "price": 199.99},
    "0x238d5930": {"name": "Mirrorball", "price": 249.49},
    "0x11223344": {"name": "Snow On The Beach", "price": 399.79},
}

PI_API_URL = "http://192.168.2.34:5000/get-uid"

def get_uid_from_api():
    try:
        response = requests.get(PI_API_URL)
        response.raise_for_status()
        data = response.json()
        print(f"API Response: {data}")  # Debug log

        uid = data.get("uid")
        if uid and uid != "No UID detected":
            processed_uid = "0x" + "".join(part[2:] for part in uid)
            print(f"API Response: {data}")  # Debug log
            return processed_uid
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching UID from the API: {e}")
    return None

class NfcScannerApp:
    def __init__(self, master, worker_name):
        # Initialize the window
        self.master = master
        self.master.title("Jumbo NFC-Scanner")
        self.master.geometry("800x400")

        # Store the worker's name
        self.worker_name = worker_name
        self.cart = []
        self.total_price = 0.0
        self.last_uid = None

        # Welcome label with worker's name
        self.label_welcome = tk.Label(self.master, text=f"Welcome, {self.worker_name}!", font=("Arial", 16, "bold"))
        self.label_welcome.pack(pady=10)

        # Cart label
        self.label_cart = tk.Label(self.master, text="Cart: (empty)", justify="left", anchor="w")
        self.label_cart.pack(pady=10, fill="both", expand=True)

        # Total price label
        self.label_total = tk.Label(self.master, text=f"Total price: €{self.total_price}", font=("Arial", 16, "bold"))
        self.label_total.pack(pady=5)

        # Exit button
        self.button_exit = tk.Button(self.master, text="Exit", command=self.master.quit)
        self.button_exit.pack(pady=10)

        self.master.after(1000, self.auto_scan) # Schedule the first scan after 1 second

    # Function to retrieve and display the scanned item
    def scan_item(self):
        # Get the NFC code from the entry field
        uid = get_uid_from_api()
        if uid:
            if uid == self.last_uid:
                print(f"UID {uid} already scanned.")  # Debug log
                return # Skip adding the same item again

            self.last_uid = uid # Update the last scanned UID
            item = items_db.get(uid)
            if item:
                print(f"Item found: {item}") # Debug log
                self.cart.append({"id": uid, "details": item})
                self.total_price += item["price"]
                self.update_cart_label()
            else:
                print(f"Item not found for this UID: {uid}") # Debug log
                messagebox.showerror("Error", f"Item not found for UID: {uid}")
        else:
            print("No NFC code detected.") # Debug log

    # Function to automatically scan for NFC codes
    # TODO: Implement a button to stop the auto-scan? (To not overload the API)
    def auto_scan(self):
        self.scan_item()
        self.master.after(1000, self.auto_scan) # Schedule the next scan every next second

    # Function to update the cart label and total price
    def update_cart_label(self):
        # Generate cart text
        cart_content = "\n".join(
            [f"ID: {item['id']} - {item['details']['name']} - €{item['details']['price']:.2f}" for item in self.cart]
        )
        self.label_cart.config(text=f"Cart:\n{cart_content}")

        # Update total price label
        self.label_total.config(text=f"Total price: €{self.total_price:.2f}")
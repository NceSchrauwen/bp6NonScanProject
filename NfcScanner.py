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
        self.auto_scan_enabled = False  # Flag to control auto-scanning
        self.collected_items = 0

        # Welcome label with worker's name
        self.label_welcome = tk.Label(self.master, text=f"Welcome, {self.worker_name}!", font=("Arial", 16, "bold"))
        self.label_welcome.pack(pady=10)

        # Start auto-scan button
        self.button_start_scan = tk.Button(self.master, text="Start Auto-Scan", command=self.start_auto_scan)
        self.button_start_scan.pack(pady=5)

        # Stop auto-scan button
        self.button_stop_scan = tk.Button(self.master, text="Stop Auto-Scan", command=self.stop_auto_scan)
        self.button_stop_scan.pack(pady=5)

        # Manual scan button
        self.button_manual_scan = tk.Button(self.master, text="Manual Scan", command=self.scan_item)
        self.button_manual_scan.pack(pady=5)

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
        if self.auto_scan_enabled:
            print("Auto-scanning...")
            self.scan_item()
            self.master.after(2000, self.auto_scan) # Repeat scan every 2 seconds

    def start_auto_scan(self):
        if not self.auto_scan_enabled:
            print("Auto-Scan started.")  # Debug log
            self.auto_scan_enabled = True
            self.auto_scan()

    def stop_auto_scan(self):
        if self.auto_scan_enabled:
            print("Auto-Scan stopped.")
            self.auto_scan_enabled = False

    # Function to update the cart label and total price
    def update_cart_label(self):
        display_limit = 5  # Limit the number of items displayed in the cart
        total_items = len(self.cart)
        # collected_items = total_items

        if total_items > display_limit:
            cart_to_display = self.cart[-display_limit:]
            dots = "...\n"  # Indicate more items in the cart (not displayed)
            start_index = total_items - display_limit + 1 # Calculate the starting index
        else:
            cart_to_display = self.cart
            dots = "" # No dots needed
            start_index = 1 # Start from the first item

        # Generate cart content with proper enumeration
        cart_content = dots + "\n".join(
            [f"{start_index + idx}. ID: {item['id']} - {item['details']['name']} - €{item['details']['price']:.2f}"
            for idx, item in enumerate(reversed(cart_to_display))]
        )

        self.label_cart.config(text=f"Cart:\n{cart_content}")

        # Update total price label
        self.label_total.config(text=f"Total price: €{self.total_price:.2f}")
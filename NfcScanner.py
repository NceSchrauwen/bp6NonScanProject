# BP6 Non-Scan Project - NFC Scanner Class
# Author: Nina Schrauwen

import tkinter as tk
import requests
import socket
from tkinter import messagebox

# Unified database for all NFC codes
items_db = {
    "0x466aca1": {"name": "So American", "price": 199.99},
    "0x238d5930": {"name": "Mirrorball", "price": 249.49},
    "0x11223344": {"name": "Snow On The Beach", "price": 399.79},
}

PI_API_URL = "http://192.168.2.34:5000/get-uid"
HC05_MAC = "00:25:00:00:13:9F"  # Replace with your HC-05 MAC address
HC05_PORT = 1  # Default port for HC-05

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
        self.sock = None  # Initialize self.sock to None

        # Attempt to connect to the HC-05
        self.connect_to_hc05()

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

        self.master.after(500, self.receive_message)  # Start listening for responses from HC-05

    # Function to retrieve and display the scanned item
    def scan_item(self):
        # Get the NFC code from the API
        uid = get_uid_from_api()

        if uid:
            print(f"📡 Scanned UID: {uid}")  # Debugging

            # Check if UID was just scanned to avoid duplicate processing
            if uid == self.last_uid:
                print(f"⚠️ UID {uid} already scanned. Skipping duplicate.")
                return

            self.last_uid = uid  # Update last scanned UID

            if uid in items_db:
                # ✅ UID is recognized → Add item to cart
                item = items_db[uid]
                print(f"✅ Item found: {item}")  # Debugging
                self.cart.append({"id": uid, "details": item})
                self.total_price += item["price"]
                self.update_cart_label()

            elif uid not in items_db:
                # ❗ UID is NOT recognized → Request approval via HC-05
                print(f"❌ Item NOT found for UID: {uid}. Requesting approval...")
                self.request_approval(uid)

            else:
                # 🛑 Catch unexpected cases
                print(f"⚠️ Unhandled case for UID: {uid}")

        else:
            print("⚠️ No UID detected.")  # Debugging


    def connect_to_hc05(self):
        try:
            # Create an RFCOMM socket
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.sock.connect((HC05_MAC, HC05_PORT))
            print("Connected to HC-05!")
        except Exception as e:
            self.sock = None # Ensure the socket is None if the connection fails
            print(f"Failed to connect to HC-05: {e}")

    def request_approval(self, uid):
        if self.sock:
            try:
                message = f"Requesting approval for item with UID: {uid}"
                self.sock.send(message.encode())
                print(f"Following approval request sent: {message}")
            except Exception as e:
                print(f"Error sending approval request: {e}")
        else:
            print("HC-05 is not connected. Cannot send approval request.")

    def receive_message(self):
        if self.sock:
            try:
                self.sock.settimeout(10)  # Increase timeout
                raw_response = self.sock.recv(1024)  # Receive raw bytes

                # Debugging: Print raw bytes before decoding
                print(f"Raw Response from HC-05: {raw_response.hex()}")

                try:
                    # 🔍 Try decoding as UTF-8, replacing invalid bytes
                    response = raw_response.decode("utf-8", errors="replace").strip()
                except UnicodeDecodeError:
                    # ❌ UTF-8 failed, try ISO-8859-1 (Latin-1)
                    response = raw_response.decode("iso-8859-1", errors="replace").strip()

                if response:
                    print(f"Received response from HC-05: {response}")
                    if "Approval" in response:
                        messagebox.showinfo("HC-05 Response", response)
                else:
                    print("No response received within the timeout.")

            except socket.timeout:
                print("Socket timeout: No response received.")

            except Exception as e:
                print(f"Failed to receive message: {e}")

        else:
            print("HC-05 is not connected. Cannot receive messages.")

        self.master.after(1000, self.receive_message)  # Schedule the next message check

    # Function to automatically scan for NFC codes
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
# BP6 Non-Scan Project - NFC Scanner Class
# Author: Nina Schrauwen
import threading
import tkinter as tk
import requests
import socket
import time
from tkinter import messagebox
from HC05Communicator import HC05Communicator

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
        self.auto_scan_enabled = False  # Flag to control auto-scanning

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

        # Manual Connect to HC-05 button
        self.button_manual_scan = tk.Button(self.master, text="Connect to HC-05", command=self.connect_hc05)
        self.button_manual_scan.pack(pady=5)

        # Manual Send Command Non-Scan button
        self.button_manual_scan = tk.Button(self.master, text="Request Non-Scan", command=self.send_message)
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

    # Function to retrieve and display the scanned item
    def scan_item(self):
        # Get the NFC code from the API
        uid = get_uid_from_api()

        if uid:
            print(f"📡 Scanned UID: {uid}")  # Debugging

            if uid in items_db:
                # ✅ UID is recognized → Add item to cart
                item = items_db[uid]
                print(f"✅ Item found: {item}")  # Debugging
                self.cart.append({"id": uid, "details": item})
                self.total_price += item["price"]
                self.update_cart_label()

            elif uid not in items_db:
                # ❗ UID is NOT recognized → Request approval via HC-05
                print(f"❌ Item NOT found for UID: {uid}. Use Non-Scan button to request approval.")

            else:
                # 🛑 Catch unexpected cases
                print(f"⚠️ Unhandled case for UID: {uid}")

        else:
            print("⚠️ No UID detected.")  # Debugging

    def connect_hc05(self):
        """ Initialize HC-05 connection and listen for responses """
        if not hasattr(self, "hc05") or not self.hc05.sock:
            self.hc05 = HC05Communicator()
            self.hc05.connect()

            self.flush_old_buffer()  # Flush old buffer in case of leftover data

    def flush_old_buffer(self):
        """ Flush any old, unread data from the buffer before sending new messages. """
        if self.hc05.sock:
            self.hc05.sock.settimeout(0.5)
            try:
                while True:
                    leftover = self.hc05.sock.recv(1024)
                    if not leftover:
                        break
            except socket.timeout:
                pass  # ✅ Ignore timeout (it means the buffer is empty)
            print("🧹 Flushed old buffer data")

    def send_message(self):
        """ Send an approval request to HC-05 without reconnecting. """
        # If there is no HC-05 connection, exit the function
        if not hasattr(self, "hc05") or not self.hc05.sock:
            print("⚠️ HC-05 is not connected! Please connect first.")
            return

        # ✅ Ensure only ONE listening thread runs
        if not hasattr(self, "_listening_thread") or not self._listening_thread.is_alive():
            self._listening_thread = threading.Thread(target=self._listen_for_response, daemon=True)
            self._listening_thread.start()
            print("👂 Listening for responses...")

        time.sleep(0.2)  # ✅ Give HC-05 time to process

        message = "R"  # ✅ Single character request
        self.hc05.send_message(message)
        print(f"✅ Approval request sent: {message}")

    def _listen_for_response(self):
        """ Continuously listen for responses from HC-05 without blocking UI """
        print("Waiting for response...")  # Debug log

        buffer = ""  # Store incoming data

        while True:
            chunk = self.hc05.receive_message()

            if chunk:
                buffer += chunk # Append received data
                print(f"🛠 Raw HEX chunk response from HC-05: {chunk.encode().hex()}")  # Debugging

                # ✅ If buffer exceeds 1 character, show and reset it
                if not chunk.isprintable():
                    print(f"🚨 Ignoring non-printable chunk: {chunk.encode().hex()}")
                    continue  # Keep listening for a valid response

                # ✅ If buffer exceeds 1 character, show and reset it
                if len(buffer) > 1:
                    print(f"⚠️ Buffer overflow detected: '{buffer}' -> Flushing excess data")
                    buffer = ""  # Reset buffer when no valid response is found

                if buffer.strip() == "R":
                    response = buffer.strip()
                    print(f"✅ Received response from HC-05: {response}")

                    self.master.after(0, lambda: messagebox.showinfo("❗HC-05 Response", response))
                    buffer = ""  # Reset buffer after receiving a valid response
                else:
                    print(f"🚨 Ignoring invalid response: '{buffer.encode().hex()}'")
                    buffer = ""  # ✅ Reset buffer on invalid response

            time.sleep(0.1)  # Prevent high CPU usage

    def receive_message(self):
        """ Listen for incoming messages from HC-05 """
        while True:
            response = self.hc05.receive_message()
            if response:
                print(f"✅ Received response from HC-05: {response}")
                messagebox.showinfo("❗HC-05 Response", response)
            time.sleep(1)  # Avoid constant polling

    # Function to automatically scan for NFC codes
    def auto_scan(self):
        if self.auto_scan_enabled:
            print("Auto-scanning...")
            self.scan_item()
            self.master.after(2000, self.auto_scan) # Repeat scan every 2 seconds

    def initialize_hc05(self):
        """ Initialize HC-05 connection and listen for responses """
        if not hasattr(self, "hc05") or not self.hc05.sock:
            self.hc05 = HC05Communicator()
            self.hc05.connect()
            self.hc05.start_listening()  # Start listening for responses

            # ✅ Flush old buffer in case of leftover data
            self.hc05.sock.settimeout(0.5)
            try:
                while True:
                    leftover = self.hc05.sock.recv(1024)
                    if not leftover:
                        break
            except socket.timeout:
                pass  # Ignore if buffer is empty
            print("🧹 Flushed old buffer data")

    def start_auto_scan(self):
        if not self.auto_scan_enabled:
            print("Auto-Scan started.")  # Debug log
            self.auto_scan_enabled = True

            # TODO: Move this so it can be called without having to use the start_auto_scan button to start non-scan
            # # ✅ Start HC-05 connection ONLY when scanning starts
            # if not hasattr(self, "hc05") or not self.hc05.sock:
            #     self.hc05 = HC05Communicator()
            #     self.hc05.connect()
            #     threading.Thread(target=self.hc05.start_listening, daemon=True).start()  # Run in a background thread

            # self.initialize_hc05()  # Initialize HC-05 connection
            self.auto_scan()  # Start the auto-scan loop

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
# BP6 Non-Scan Project - Hc-05 Communicator Class
# Author: Nina Schrauwen
import threading
import socket
import time

HC05_MAC = "00:25:00:00:13:9F"  # Replace with your HC-05 MAC address
HC05_PORT = 1  # Default port for HC-05

class HC05Communicator:
    def __init__(self):
        self.sock = None  # Initialize self.sock to None
        self.running = False # Flag to control the thread
        self.listen_thread = None # Background thread for listening

    def connect(self):
        """ Establish Bluetooth connection to HC-05 """
        if self.sock:
            try:
                self.sock.close()  # Close the socket if it's open
                print("🔌 Disconnected from HC-05.")
            except Exception as e:
                print(f"🚨 Error closing socket: {e}")
                self.sock = None # Reset socket to None if closing fails

        try:
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM) # Create a Bluetooth socket
            self.sock.connect((HC05_MAC, HC05_PORT)) # Connect to HC-05
            print("✅ Connected to HC-05!")
        except Exception as e:
            print(f"🚨 Failed to connect: {e}")
            self.sock = None # Reset socket to None if connection fails

    def send_message(self, message):
        """ Send message to HC-05 """
        # If the socket is open, send the message
        if self.sock:
            try:
                # self.start_listening()  # Start listening for responses
                self.sock.sendall((message + "\n").encode())  # Send message with newline (`\n`)
                print(f"📡 Sent: {message}")
            except Exception as e:
                print(f"🚨 Error sending message: {e}")

    def receive_message(self):
        """ Keep listening for a valid response without resetting the connection. """
        buffer = b""  # Store incoming data

        while self.sock:  # ✅ Keep listening as long as the connection is active
            try:
                chunk = self.sock.recv(1)  # ✅ Receive 1 byte at a time
                if not chunk or chunk.strip(b'\x00') == b'':
                    continue  # Ignore empty messages

                buffer += chunk  # Append received data
                print(f"🛠 Raw HEX chunk response from Hc-05: {buffer.hex()}")

                # ✅ Stop listening only when we get meaningful data
                if len(buffer) == 1:
                    response = buffer.decode("utf-8", errors="ignore").strip()

                    # ✅ Only accept "R" (HEX 52)
                    if response == "R":
                        buffer = b""  # ✅ Reset buffer after receiving a valid response
                        print(f"✅ Received: {response}")
                        return response  # ✅ Successfully received!
                    else:
                        print(f"🚨 Ignoring invalid response: '{response}'")
                        buffer = b""  # ✅ Reset buffer on invalid response
                        continue  # ✅ Keep listening

            except socket.timeout:
                print("⏳ Timeout: No response received. Retrying...")
                # self.reconnect_hc05()  # ✅ Try to reconnect if needed
                continue  # ✅ Keep listening instead of disconnecting

            except socket.error as e:
                print(f"🚨 Error receiving message: {e}")
                # self.reconnect_hc05()  # ✅ Try to reconnect if needed
                return None

            time.sleep(0.1)  # ✅ Prevent high CPU usage while waiting

    def reconnect_hc05(self):
        """ Try to reconnect to HC-05 only when absolutely necessary. """
        try:
            if self.sock:
                self.sock.close()  # Close existing connection
            time.sleep(1)  # ✅ Allow Bluetooth module to recover before reconnecting
            self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.sock.connect((HC05_MAC, HC05_PORT))
            print("✅ Reconnected to HC-05!")
        except Exception as e:
            print(f"🚨 Reconnection failed: {e}")

    def start_listening(self):
        """ Start receiving messages in a separate thread """
        # If the receiver is not running, start the thread
        if self.listen_thread and self.listen_thread.is_alive():
            print("⚠️ Listening thread already running.")
            return  # ✅ Prevent multiple listeners

        self.running = True # Set the running flag to True
        self.listen_thread = threading.Thread(target=self.receive_message, daemon=True) # Create a new thread
        self.listen_thread.start() # Start the thread
        print("👂 Listening for messages...")

    def stop(self):
        """ Stop the receiver and close the connection """
        # Set the running flag to False and close the socket
        self.running = False
        if self.sock:
            try:
                self.sock.close()  # ✅ Ensure socket is closed before reconnecting
                print("🔌 Disconnected from HC-05.")
            except Exception as e:
                print(f"⚠️ Error while closing socket: {e}")
        self.sock = None  # ✅ Ensure the socket is reset
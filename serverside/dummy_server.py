
import socket
import threading
import time
import random

# Constants
HOST = '192.168.1.113'  # Localhost
PORT = 8266        # Port to listen on (non-privileged ports are > 1023)
KEEP_ALIVE_INTERVAL = 15  # seconds

# Function to handle client connections


def process_command():
    pass


def handle_client(conn, addr):
    print(f"Connected by {addr}")
    # Set timeout to handle keep-alive
    conn.settimeout(KEEP_ALIVE_INTERVAL + 5)

    last_received_time = time.time()

    led = 0
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')
            if "UABC:" in message or "ACK" in message or "NACK" in message:
                print(f"Received from {addr}: {message}")

            if "UABC:RRC:L:S:" in message.strip():
                conn.sendall(b"ACK")
            elif "UABC:RRC:K:S:" in message.strip():
                last_received_time = time.time()  # Reset the timer
                conn.sendall(b"ACK")
                comand = random.randint(0, 100)
                if (comand < 20):
                    if led == 0:
                        conn.sendall(b"UABC:RRC:W:L:1:Turned on LED")
                        led = 1
                    else:
                        conn.sendall(b"UABC:RRC:W:L:0:Turned off LED")
                        led = 0
                elif (comand < 40):
                    conn.sendall(b"UABC:RRC:R:A:0:Reading from ADC")

            elif "UABC" in message.strip():
                print(b"NACK")
            if time.time() - last_received_time > KEEP_ALIVE_INTERVAL:
                print("Keep-alive signal missed, closing connection.")
                break

        except socket.timeout:
            print("Keep-alive timeout, closing connection.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    conn.close()
    # prints connection closed and the socket
    print(f"Connection closed by {addr}")

# Main function to start the server


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(
                target=handle_client, args=(conn, addr))
            client_thread.start()


if __name__ == "__main__":
    start_server()

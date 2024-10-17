
import socket
import struct
import threading
import time
import random
import mariadb

# Constants
HOST = '192.168.1.200'  # Localhost
PORT = 8266        # Port to listen on (non-privileged ports are > 1023)
DATABASE = "arht_test"
TABLE = "study_1"
USER = "logger"
PREPARED_STATEMENT = "INSERT INTO study_1 VALUES (DEFAULT,?,?,?,?,?,?,?,?,?,?)"

# Function to handle client connections


def insert_data(data):
    #Connects to the mariadb local database
    try:
        conn = mariadb.connect(
            user=USER,
            password="NotARHTPass",
            host=HOST,
            port=3306,
            database=DATABASE
        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        return
    #Creates a cursor to interact with the database
    cur = conn.cursor()
    #Inserts data into the database
    cur.execute(PREPARED_STATEMENT, data)
    #Commits the data
    conn.commit()
    #error handling
    if cur.rowcount == 1:
        print(f"Data inserted successfully")
    else:
        print(f"Data not inserted")
    #Closes the connection
    conn.close()



def handle_client(conn, addr):
    print(f"Connected by {addr}")
    last_received_time = time.time()

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            # Receives 10 floats 4 bytes each. Turns them into a list of floats
            data = struct.unpack('10f', data)
            print(data)
            #inserts data into the database
            insert_data(data)
        except socket.timeout:
            print("Timing out, closing connection.")
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

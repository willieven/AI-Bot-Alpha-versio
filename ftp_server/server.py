import socket
import threading
import logging
from .session import ClientSession
from .commands import handle_command

class FTPServer(threading.Thread):
    def __init__(self, host, port, image_queue):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.image_queue = image_queue
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.active_sessions = {}
        self.session_lock = threading.Lock()

    def run(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        logging.info(f"FTP server listening on {self.host}:{self.port}")
        while True:
            try:
                conn, addr = self.sock.accept()
                logging.info(f"New connection from {addr[0]}:{addr[1]}")
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
            except Exception as e:
                logging.error(f"Failed to establish connection with client: {str(e)}")

    def handle_client(self, conn, addr):
        session = ClientSession(conn, addr, self)
        with self.session_lock:
            self.active_sessions[addr] = session
        try:
            while True:
                data = conn.recv(1024).decode('utf-8', errors='replace').strip()
                if not data:
                    break
                response = handle_command(data, session)
                conn.send(response.encode() + b'\r\n')
        except Exception as e:
            logging.error(f"Error handling client {addr}: {str(e)}")
        finally:
            with self.session_lock:
                del self.active_sessions[addr]
            conn.close()
            logging.info(f"Connection closed for {addr[0]}:{addr[1]}")
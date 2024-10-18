import time

class ClientSession:
    def __init__(self, conn, addr, server):
        self.conn = conn
        self.addr = addr
        self.server = server
        self.username = None
        self.authenticated = False
        self.current_directory = '/'
        self.data_socket = None
        self.pasv_socket = None
        self.transfer_type = 'I'
        self.utf8_enabled = False
        self.last_activity = time.time()

    def update_activity(self):
        self.last_activity = time.time()

    def send_response(self, response):
        self.conn.send(response.encode() + b'\r\n')
from .server import FTPServer
from config import FTP_HOST, FTP_PORT
import logging

def start_ftp_server(image_queue):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    server = FTPServer(FTP_HOST, FTP_PORT, image_queue)
    server.start()
    return server

if __name__ == "__main__":
    # This would typically be called from the main application,
    # but we can include a simple start here for testing
    start_ftp_server(None)
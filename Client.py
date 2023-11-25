import socket
import threading

class Client:
    def __init__(self, host = '127.0.0.1', port = 12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

    def send(self, msg):
        self.client.send(msg.encode('ascii'))

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message.startswith('send'):
                    _, lname, addr = message.split()
                    # fetch file from addr
                    pass
            except:
                print("An error occured!")
                self.client.close()
                break

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    while True:
        message = input('')
        client.send(message)

import socket
import threading

class Server:
    def __init__(self, host = '127.0.0.1', port = 12345):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = {}
        self.files = {}

    def handle(self, client):
        while True:
            msg = client.recv(1024).decode('ascii')
            if msg.startswith('publish'):
                _, lname, fname = msg.split()
                self.files[fname] = (lname, client)
            elif msg.startswith('fetch'):
                _, fname = msg.split()
                if fname in self.files:
                    lname, owner = self.files[fname]
                    owner.send(f'send {lname} to {client.getpeername()}'.encode('ascii'))

    def run(self):
        while True:
            client, addr = self.server.accept()
            self.clients[addr] = client
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

if __name__ == "__main__":
    server = Server()
    server.run()

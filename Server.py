import socket
import threading

class Server:
    def __init__(self, host = socket.gethostname(), port = 22236):
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

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd.startswith('discover'):
                _, hostname = cmd.split()
                if hostname in self.clients:
                    client = self.clients[hostname]
                    client.send('list'.encode('ascii'))
                else:
                    print(f'Host {hostname} not found.')
            elif cmd.startswith('ping'):
                _, hostname = cmd.split()
                if hostname in self.clients:
                    client = self.clients[hostname]
                    client.send('ping'.encode('ascii'))
                else:
                    print(f'Host {hostname} not found.')
            else:
                print('Invalid command.')

    def run(self):
        while True:
            client, addr = self.server.accept()
            print(f'New connection from {addr}')
            self.clients[addr] = client
            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()

            command_shell_thread = threading.Thread(target=self.command_shell)
            command_shell_thread.start()
   
if __name__ == "__main__":
    server = Server()
    server.run()
    

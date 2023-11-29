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
            try:
                data = client.recv(1024).decode('ascii')
                messages = data.split('\n')
                for msg in messages:
                    if msg.startswith('publish'):
                        command_lname, fname = msg.rsplit(' ', 1)   #split from the right to get fname
                        _, lname = command_lname.split(' ', 1)         #split normally with at most 2 parts to get the rest
                        if fname not in self.files:
                            self.files[fname] = []
                        self.files[fname].append((lname, client))
                    elif msg.startswith('fetch'):
                        _, fname = msg.split()
                        if fname in self.files:
                            for lname, owner in self.files[fname]:
                                ip, port = self.clients[owner]
                                client.send(f'owner {ip} {port} has {lname}'.encode('ascii'))
                        else:
                            client.send('File not available'.encode('ascii'))
                    elif msg.startswith('CLIENT_IP'):
                        _, ip, port = msg.split()
                        self.clients[client] = (ip, int(port))
                    elif msg.startswith('FILES:'):
                        print(f'Files in client {client.getpeername()}: {msg[6:]}')
                    elif msg.startswith('remove'):
                        _, fname = msg.split()
                        if fname in self.files:
                            self.files[fname] = [file for file in self.files[fname] if file[1] != client]
                            if not self.files[fname]:
                                del self.files[fname]
            except ConnectionResetError:
                print(f"Connection with client {client.getpeername()} was closed.")
                break

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd == 'exit' or cmd == 'stop':
                self.server.close()
                break
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
        print(f'Server is running on IP: {socket.gethostbyname(self.host)}')

        while True:
            try:
                client, addr = self.server.accept()
                try:
                    hostname, _, _ = socket.gethostbyaddr(addr[0])
                except socket.herror:
                    hostname = addr[0] # use the IP address if the hostname is not available
                print(f'New connection from {hostname}:{addr[1]}')

                self.clients[hostname] = client
                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()

                command_shell_thread = threading.Thread(target=self.command_shell)
                command_shell_thread.start()
            except OSError:
                print("Server has stopped.")
                break

if __name__ == "__main__":
    server = Server()
    server.run()

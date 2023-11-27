import socket
import threading
import os
import shutil
import inspect

src_file_path = inspect.getfile(lambda: None)

class Client:
    def __init__(self, host = input("Enter the server's IP address: "), port = 22236):
        self.host = '127.0.0.1'
        self.port = port + 1
        print(f"host {self.host} ,port {self.port}")
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((host, port))
        except socket.error as e:
            print(f"Couldn't connect to the server, recheck the IP address: {e}")
            return
        self.files = {}

        # Start the server to accept incoming connections
        self.start_server()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        thread = threading.Thread(target=self.accept_connections)
        thread.start()
    
    def accept_connections(self):
        client, addr = self.server_socket.accept()
        thread = threading.Thread(target=self.handle_client, args=(client,))
        thread.start()
    
    def handle_client(self, client):
        while True:
            msg = client.recv(1024).decode('ascii')
            if msg.startswith('request'):
                _, lname = msg.split()
                self.send_file(lname, client)

    def send(self, msg):
        self.client.send(msg.encode('ascii'))

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message.startswith('owner'):
                    _, ip, port, _, lname = message.split()
                    addr = (ip, int(port))
                    print(f'File {lname} is available at {addr}.')
                elif message.startswith('request'):
                    _, lname = message.split()
                    self.send_file(lname)
                elif message == 'list':
                    self.send('FILES: ' + ' '.join(self.files.keys()))
            except Exception as e:
                print("An error occured: ", str(e))
                self.client.close()
                break

    def fetch_file(self, lname, addr):
        # create a new socket connection to the client with the file
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.connect(addr)
            s.send(f'request {lname}'.encode('ascii'))
            with open(os.path.join('repo', lname), 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
            print(f'File {lname} has been downloaded.')

    def send_file(self, lname, client):
        if lname in self.files:
            with open(self.files[lname], 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    client.send(data)

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd == 'exit' or cmd == 'stop':
                self.client.close()
                self.server_socket.close()
                break
            if cmd.startswith('publish'):
                try:
                    _, lname, fname = cmd.split()
                    if os.path.isfile(lname):
                        repo_path = os.path.join(os.path.dirname(src_file_path), 'repo', fname)
                        # Copy the file to the local repository
                        shutil.copy(lname, repo_path)
                        # Add the file to self.files
                        self.files[fname] = repo_path
                        self.send(cmd)
                        print(f'File {lname} published successfully as {fname}.')
                    else:
                        print(f'File {lname} does not exist.')
                except ValueError:
                    print('Invalid command. The correct format is: publish [localname] [filename]')
            elif cmd.startswith('fetch'):
                try:
                    parts = cmd.split()
                    if len(parts) == 2:
                        _, fname = parts
                        if fname in self.files:
                            print(f'File {fname} is already in the local repository.')
                        else:
                            self.send(cmd)
                    elif len(parts) == 4:
                        _, fname, ip, port = parts
                        if fname in self.files:
                            print(f'File {fname} is already in the local repository.')
                        else:
                            addr = (ip, int(port))
                            self.fetch_file(fname, addr)
                    else:
                        print('Invalid command. The correct format is: fetch [filename] or fetch [filename] [ip] [port]')
                except ValueError:
                    print('Invalid command. The correct format is: fetch [filename] or fetch [filename] [ip] [port]')
            else:
                print('Invalid command.')

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()

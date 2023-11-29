import socket
import threading
import os
import shutil
import inspect

src_file_path = inspect.getfile(lambda: None)

class Client:
    def __init__(self, host = input("Enter the server's IP address: "), port = 22236):
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = port + 1
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((host, port))
        except socket.error as e:
            print(f"Couldn't connect to the server, recheck the IP address: {e}")
            return
        self.files = {}

        # Start the server to accept incoming connections
        self.start_server()
        
        # Publish all files in the repo folder
        self.publish_all_files()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        thread = threading.Thread(target=self.accept_connections)
        thread.start()
        self.send(f'CLIENT_IP {self.host} {self.port}')
    
    def accept_connections(self):
        while True:
            try:    
                client, addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client,))
                thread.start()
            except OSError:
                break

    def handle_client(self, client):
        while True:
            msg = client.recv(1024).decode('ascii')
            if msg.startswith('request'):
                _, lname = msg.split()
                self.send_file(lname, client)

    def send(self, msg):
        self.client.send((msg + '\n').encode('ascii'))

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message.startswith('owner'):
                    _, ip, port, _, lname = message.split(' ', 4)
                    addr = (ip, int(port))
                    print(f'File {lname} is available at {addr}.')
                elif message.startswith('request'):
                    _, lname = message.split()
                    self.send_file(lname)
                elif message == 'list':
                    self.send('FILES: ' + ' '.join(self.files.keys()))
                elif message == 'File not available':
                    print(message)
            except ConnectionResetError:
                print("Connection was closed by the server.")
                break
            except Exception as e:
                print("An error occured: ", str(e))
                self.client.close()
                break

    def publish_all_files(self):
        repo_path = os.path.join(os.path.dirname(src_file_path), 'repo')
        files_published = False
        for fname in os.listdir(repo_path):
            lname = os.path.join(repo_path, fname)
            if os.path.isfile(lname):
                self.files[fname] = lname
                self.send(f'publish {lname} {fname}')
                files_published = True
                print(f'File {lname} published successfully as {fname}.')
        if files_published:
            print("All files in the repository published successfully.")
            
    def fetch_file(self, lname, addr):
        # create a new socket connection to the client with the file
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(addr)
            print('Connected, fetching file...')
            s.send(f'request {lname}'.encode('ascii'))
            with open(os.path.join('repo', lname), 'wb') as f:
                try:
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                except Exception as e:
                    print(f"An error occurred while receiving data: {e}")    
            print(f'File {lname} has been downloaded.')

    def send_file(self, lname, client):
        if lname in self.files:
            with open(self.files[lname], 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    client.send(data)
            print('Sent ' + lname + ' to: ' + str(client.getpeername()))
            client.close()

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
            elif cmd.startswith('remove'):
                try:
                    _, fname = cmd.split()
                    if fname in self.files:
                        os.remove(self.files[fname])
                        del self.files[fname]
                        self.send(cmd)
                        print(f'File {fname} removed successfully from the local repository.')
                    else:
                        print(f'File {fname} does not exist in the local repository.')
                except ValueError:
                    print('Invalid command. The correct format is: remove [filename]')
            else:
                print('Invalid command.')

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()

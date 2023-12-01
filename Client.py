import socket
import threading
import os
import shutil
import sys
import time

#Get current location of the executable
if getattr(sys, 'frozen', False):
    src_file_path = sys.executable
else:
    src_file_path = os.path.dirname(os.path.abspath(__file__))

class Client:
    def __init__(self, host = input("Enter the server's IP address: "), port = 22236):
        self.host = socket.gethostbyname(socket.gethostname())
        self.port = get_open_port()
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
            try:
                msg = client.recv(1024).decode('utf-8')
                if msg.startswith('request'):
                    _, lname = msg.split()
                    self.send_file(lname, client)
            except OSError:
                break

    def send(self, msg):
        self.client.send((msg + '\n').encode('utf-8'))

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message.startswith('owner'):
                    _, ip, port, _, fname = message.split(' ', 4)
                    addr = (ip, int(port))
                    print(f'File {fname} is available at {addr}.')
                elif message.startswith('published'):
                    print(f'Server Response: Files published to the server')
                elif message.startswith('removed'):
                    print(f'Server Response: Files removed')
                elif message == 'list':
                    self.send('FILES: ' + ' '.join(self.files.keys()))
                elif message == 'File not available':
                    print(message)
                elif message == 'ping':
                    self.send('ping')
            except ConnectionResetError:
                print("Connection was closed by the server.")
                break
            except Exception as e:
                print("An error occured: ", str(e))
                self.client.close()
                break  
    
    def publish_all_files(self):
        repo_path = os.path.join(os.path.dirname(src_file_path), 'repo')

        # Create the 'repo' folder if it doesn't exist
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            print("Created repo folder")
            return

        for fname in os.listdir(repo_path):
            lname = os.path.join(repo_path, fname)
            if os.path.isfile(lname):
                self.files[fname] = lname
                self.send(f'publish {lname} {fname}')
       

    def fetch_file(self, fname, addr):
        # create a new socket connection to the client's server with the file
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(addr)
            print('Connected, fetching file...')
            s.send(f'request {fname}'.encode('utf-8'))
            start_time = time.time() # record start time
            with open(os.path.join('repo', fname), 'wb') as f:
                try:
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                except Exception as e:
                    print(f"An error occurred while receiving data: {e}") 
            end_time = time.time()   
            print(f'File {fname} has been downloaded. It took {end_time - start_time} seconds.')

            # After the file has been downloaded, publish it to the server
            self.send(f'publish {os.path.join("repo", fname)} {fname}')
            self.files[fname] = os.path.join('repo', fname)

    def send_file(self, fname, client):
        if fname in self.files:
            with open(self.files[fname], 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    client.send(data)
            print('\n' + 'Sent ' + fname + ' to: ' + str(client.getpeername()))
        client.close()

    def command_shell(self):
        # Publish all files in the repo folder
        self.publish_all_files()
        print('Client is connected to the server. Type "/help" for a list of available commands.')
        while True:
            cmd = input('\nEnter command: ')
            if cmd == 'exit' or cmd == 'stop':
                self.client.close()
                self.server_socket.close()
                break
            if cmd.startswith('publish'):
                try:
                    temp, fname = cmd.rsplit(' ', 1)
                    _, lname = temp.split(' ', 1)
                    if os.path.isfile(lname):
                        repo_path = os.path.join(os.path.dirname(src_file_path), 'repo', fname)
                        # Copy the file to the local repository
                        shutil.copy(lname, repo_path)
                        # Add the file to self.files
                        self.files[fname] = repo_path
                        print(f'File {lname} published successfully as {fname}.')
                        self.send(cmd)
                    else:
                        print(f'File {lname} does not exist.')
                except ValueError:
                    print('Invalid command. The correct format is: publish <localname> <filename>')
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
                        print('Invalid command. The correct format is: fetch <filename> or fetch <filename> <ip> <port>')
                except ValueError:
                    print('Invalid command. The correct format is: fetch <filename> or fetch <filename> <ip> <port>')
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
                    print('Invalid command. The correct format is: remove <filename>')
            elif cmd == '/help':
                print('Available commands:')
                print('  publish <localname> <filename> - Publish a file to the server')
                print('  fetch <filename> - Search whether a file is available to be fetched')
                print('  fetch <filename> <ip> <port> - Fetch a file from a specified client')
                print('  remove <filename> - Remove a file from the server')
                print('  exit, stop - Stop the program')
            else:
                print('Invalid command.')

def get_open_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('',0))
            return s.getsockname()[1]

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()

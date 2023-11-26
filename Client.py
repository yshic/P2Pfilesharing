import socket
import threading
import os
import shutil
import inspect
import sys

src_file_path = inspect.getfile(lambda: None)

class Client:
    def __init__(self, host = socket.gethostname(), port = 22236):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.files = {}

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
            s.connect(addr)
            s.send(f'request {lname}'.encode('ascii'))
            with open(os.path.join('repo', lname), 'wb') as f:
                while True:
                    data = s.recv(1024)
                    if not data:
                        break
                    f.write(data)
            print(f'File {lname} has been downloaded.')

    def send_file(self, lname):
        if lname in self.files:
            with open(self.files[lname], 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    self.client.send(data)

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd == 'exit' or cmd == 'stop':
                self.client.close()
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
                    _, fname = cmd.split()
                    if fname in self.files:
                        print(f'File {fname} is already in the local repository.')
                    else:
                        self.send(cmd)
                except ValueError:
                    print('Invalid command. The correct format is: fetch [filename]')
            elif cmd.startswith('address'):
                try:
                    _, addr = cmd.split()
                    for fname, addrs in self.available_files.items():
                        if addr in addrs:
                            self.fetch_file(fname, addr)
                            break
                    else:
                        print(f'No file available at {addr}.')
                except ValueError:
                    print('Invalid command. The correct format is: address [address]')
            else:
                print('Invalid command.')

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()

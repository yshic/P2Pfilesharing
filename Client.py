import socket
import threading
import os

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
                if message.startswith('send'):
                    _, lname, addr = message.split()
                    # fetch file from addr
                    self.fetch_file(lname, addr)
                elif message.startswith('request'):
                    _, lname = message.split()
                    self.send_file(lname)
            except:
                print("An error occured!")
                self.client.close()
                break

    def fetch_file(self, lname, addr):
        # create a new socket connection to the client with the file
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(addr)
            s.send(f'request {lname}'.encode('ascii'))
            data = s.recv(1024)
            # write data to a file
            with open(lname, 'wb') as f:
                f.write(data)

    def send_file(self, lname):
        if lname in self.files:
            with open(self.files[lname], 'rb') as f:
                data = f.read()
                self.client.send(data)

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd.startswith('publish'):
                try:
                    _, lname, fname = cmd.split()
                    if os.path.isfile(lname):
                        self.files[fname] = lname
                        self.send(cmd)
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
            else:
                print('Invalid command.')

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()


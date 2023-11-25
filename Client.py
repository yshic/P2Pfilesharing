import socket
import threading
import os

class Client:
    def __init__(self, host = '127.0.0.1', port = 12345):
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
                    pass
            except:
                print("An error occured!")
                self.client.close()
                break

    def command_shell(self):
        while True:
            cmd = input('Enter command: ')
            if cmd.startswith('publish'):
                _, lname, fname = cmd.split()
                if os.path.isfile(lname):
                    self.files[fname] = lname
                    self.send(cmd)
                else:
                    print(f'File {lname} does not exist.')
            elif cmd.startswith('fetch'):
                _, fname = cmd.split()
                if fname in self.files:
                    print(f'File {fname} is already in the local repository.')
                else:
                    self.send(cmd)
            else:
                print('Invalid command.')

if __name__ == "__main__":
    client = Client()
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()

    command_shell_thread = threading.Thread(target=client.command_shell)
    command_shell_thread.start()

import socket
import threading
import time

class Server:
    def __init__(self, host = socket.gethostname(), port = 22236):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = {}
        self.available_clients = {}
        self.files = {}
        self.ping_times = {}
        self.displayed = False

    def handle(self, client):
        while True:
            try:
                data = client.recv(1024).decode('utf-8')
                messages = data.split('\n')
                for msg in messages:
                    if msg.startswith('publish'):
                        command_lname, fname = msg.rsplit(' ', 1)   #split from the right to get fname
                        _, lname = command_lname.split(' ', 1)      #split normally with at most 2 parts to get the rest
                        if fname not in self.files:
                            self.files[fname] = []
                        self.files[fname].append((lname, client))
                        client.send(f'published'.encode('utf-8'))
                    elif msg.startswith('fetch'):
                        _, fname = msg.split()
                        if fname in self.files:
                            for lname, owner in self.files[fname]:
                                ip, port = self.clients[owner]
                                client.send(f'owner {ip} {port} has {fname}'.encode('utf-8'))
                        else:
                            client.send('File not available'.encode('utf-8'))
                    elif msg.startswith('CLIENT_IP'):
                        _, ip, port = msg.split()
                        self.clients[client] = (ip, int(port))
                        self.available_clients[client] = (ip, int(port))
                    elif msg.startswith('FILES:'):
                        print(f'Files in client {client.getpeername()}: {msg[6:]}')
                    elif msg.startswith('remove'):
                        _, fname = msg.split()
                        if fname in self.files:
                            self.files[fname] = [file for file in self.files[fname] if file[1] != client]
                            if not self.files[fname]:
                                del self.files[fname]
                        client.send('removed'.encode('utf-8'))
                    elif msg == 'ping':
                        receive_time = time.time()
                        round_trip_time = receive_time - self.ping_times[client]
                        print(f"Ping reply from {client.getpeername()} in {round_trip_time} seconds")
            except socket.timeout:
                print(f"Ping failed for {client.getpeername()}")
            except ConnectionResetError:
                print(f"Connection with client {client.getpeername()} was closed.")
                del self.available_clients[client.gethostname()]
                break

    def command_shell(self):
        if(not(self.displayed)):
            print('Server is ready to accept commands. Type "/help" for a list of available commands.')
            self.displayed = True
        while True:
            cmd = input('Enter command: ')
            if cmd == 'exit' or cmd == 'stop':
                self.server.close()
                break
            if cmd.startswith('discover'):
                try:
                    _, hostname = cmd.split()
                    if hostname in self.clients:
                        if hostname in self.available_clients:
                            try:
                                client = self.available_clients[hostname]
                                client.send('list'.encode('utf-8'))
                            except ConnectionResetError:
                                print(f"Connection with client {hostname} was already closed.")
                                del self.available_clients[hostname]
                        else:
                            print(f'Client {hostname} has already disconnected.')
                    else:
                        print(f'Host {hostname} not found.')
                except ValueError:
                    print('Invalid command. The correct format is: discover <hostname>')

            elif cmd.startswith('ping'):
                try:
                    _, hostname = cmd.split()
                    if hostname in self.clients:
                        if hostname in self.available_clients:
                            client = self.available_clients[hostname]
                            client.settimeout(5.0)      
                            self.ping_times[client] = time.time()
                            try:
                                client.send('ping'.encode('utf-8'))
                                client.settimeout(None) #Reset the timeout
                            except ConnectionResetError:
                                print('Pinging fail.')
                                del self.available_clients[hostname]
                        else:
                            print(f'Client {hostname} has already disconnected.')
                    else:
                        print(f'Host {hostname} not found.')
                except ValueError:
                    print('Invalid command. The correct format is: ping <hostname>')
            elif cmd == '/help':
                print('Available commands:')
                print('  discover <hostname> - Discover files on the specified host')
                print('  ping <hostname> - Ping the specified host')
                print('  exit, stop - Stop the server')
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
                print(f'\nNew connection from {hostname}:{addr[1]}')                

                self.clients[hostname] = client
                self.available_clients[hostname] = client
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

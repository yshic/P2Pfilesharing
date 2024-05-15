# P2Pfilesharing
A CLI application for easy peer-to-peer file-sharing, this project is part of the assignment for the course Computer Networks.

## Description
- A centralized server keeps track of which clients are connected and storing what files.
- A client informs the server as to what files are contained in its local repository but does not actually transmit file data to the server.
- File-transfering process will occur directly between clients without requiring any server intervention
- Simple command-line interface.
- Support multiple clients downloading different files from a target client simultaneously.

## User Manual
The application will have two executables: Client.exe and Server.exe.

To use the application, follow these steps:

1. Start the server: this can be done by simply open the server executable, the server must be started first before the client.
2. Start the client: this can be done by simply open the client executable. Remember to do this after the server has already been started
3. Input the server address on the client: The server will print its address to the command prompt, use this address to connect the client to the server.
4. Input the desired command on eithr the client or the server: The users can type /help for a list of available commands.

Available commands for the server:

- discover <hostname> - Discover files on the specified host'
- ping <hostname> - Ping the specified host'
- exit, stop - Stop the server'

Available commands for the client:

- publish <localname> <filename> - Publish a file to the server'
- fetch <filename> - Search whether a file is available to be fetched'
- fetch <filename> <ip> <port> - Fetch a file from a specified client'
- remove <filename> - Remove a file from the server'
- exit, stop - Stop the program'



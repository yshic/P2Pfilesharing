import tkinter as tk
from tkinter import scrolledtext
from Server import *

class ServerGUI:
    def __init__(self, server):
        self.server = server
        self.window = tk.Tk()
        self.window.title("Server")

        self.text_area = scrolledtext.ScrolledText(self.window)
        self.text_area.pack(expand=True, fill='both')

        self.command_entry = tk.Entry(self.window)
        self.command_entry.pack(side='bottom', fill='x')
        self.command_entry.bind('<Return>', self.send_command)

    def send_command(self, event):
        command = self.command_entry.get()
        self.command_entry.delete(0, 'end')
        self.text_area.insert('end', f'Command: {command}\n')
        # Add code here to handle the command

    def append_message(self, message):
        self.text_area.insert('end', message + '\n')

    def run(self):
        self.window.mainloop()

# Create the server and the GUI, then run the GUI
server = Server()
gui = ServerGUI(server)
gui.run()

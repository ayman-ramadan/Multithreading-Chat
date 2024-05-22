import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import socket
import threading
from queue import Queue

class MultithreadingChatGUI:
    def __init__(self, root, username, message_queue, on_close):
        self.root = root
        self.username = username
        self.on_close = on_close  # Store the on_close callback
        self.root.title(f"Multithreading Chat - {self.username}")
        self.root.geometry("400x300")

        self.chat_history = ScrolledText(root, state='disabled')
        self.chat_history.pack(fill=tk.BOTH, expand=True)

        self.message_entry = tk.Entry(root)
        self.message_entry.pack(fill=tk.X, padx=5, pady=5)

        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack(pady=5)

        self.label_username = tk.Label(root, text=f"Username: {self.username}")
        self.label_username.pack(pady=5)

        self.label_message = tk.Label(root, text="Message:")
        self.label_message.pack(pady=5)

        self.message_queue = message_queue

    def send_message(self):
        message = self.message_entry.get()
        if message:
            try:
                self.message_queue.put((self.username, message))
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Error sending message: {e}")

    def close_window(self, event=None):  
        self.root.withdraw()  # Hide the window
        self.on_close(self.root)  # Call the on_close callback with root as argument

def on_close(root):
    roots.remove(root)  # Remove the closed root window from the list

def start_server(message_queue, clients):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 1000))
    server_socket.listen(5)
    print("Server started and listening for connections...")

    while True:
        client_socket, _ = server_socket.accept()
        print("New client connected.")
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, message_queue, clients))
        client_thread.start()

def handle_client(client_socket, message_queue, clients):
    try:
        while True:
            message = client_socket.recv(1024).decode()
            if message:
                message_queue.put(message)
                # Broadcast the message to all other clients
                for other_client in clients:
                    if other_client != client_socket:
                        try:
                            other_client.send(message.encode())
                        except Exception as e:
                            print(f"Error broadcasting message: {e}")
    except Exception as e:
        print("Client disconnected.")
    finally:
        client_socket.close()
        clients.remove(client_socket)

def append_message(root, chat_history, message):
    if isinstance(message, tuple):  # Check if message is a tuple
        username, content = message
        chat_history.config(state='normal')
        chat_history.insert(tk.END, f"{username}: {content}\n")
        chat_history.config(state='disabled')
        chat_history.see(tk.END)

def update_gui(root, chat_histories, message_queue):
    def update():
        if not message_queue.empty():
            message = message_queue.get()
            for chat_history in chat_histories:
                append_message(root, chat_history, message)
        root.after(100, update)  # Schedule the next update after 100 milliseconds

    update()  # Start the initial update

def main():
    message_queue = Queue()
    clients = []
    global roots
    roots = []  # Define roots as a global variable
    global chat_histories
    chat_histories = []  # Define chat_histories as a global variable

    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(message_queue, clients))
    server_thread.daemon = True
    server_thread.start()

    for i in range(3):
        root = tk.Tk()
        roots.append(root)
        app = MultithreadingChatGUI(root, f"User {i+1}", message_queue, on_close)
        app.root.protocol("WM_DELETE_WINDOW", app.close_window)  # Handle window closing
        chat_histories.append(app.chat_history)

    # Start a single GUI update thread
    gui_thread = threading.Thread(target=update_gui, args=(roots[0], chat_histories, message_queue))
    gui_thread.daemon = True
    gui_thread.start()

    for root in roots:
        root.mainloop()

if __name__ == "__main__":
    main()


import socket
import pyaudio
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import numpy as np

# Audio parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Network configuration
partner_ip = "192.168.182.212"  # Replace with the IP address of the other PC
port = 50007

# Initialize PyAudio
p = pyaudio.PyAudio()

# Global variables for streams and threads
input_stream = None
output_stream = None
sock = None
receive_thread = None
send_thread = None
running = False
volume_scale = 1.0  # Default volume

# Function to start the audio communication
def start_audio():
    global sock, input_stream, output_stream, receive_thread, send_thread, running
    
    if running:
        messagebox.showwarning("Warning", "Audio communication is already running!")
        return

    # Setup socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    # Setup audio streams
    input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

    # Set running flag and update status
    running = True
    status_label.config(text="Status: Connected")

    # Start receive and send threads
    receive_thread = threading.Thread(target=receive_audio)
    send_thread = threading.Thread(target=send_audio)

    receive_thread.start()
    send_thread.start()

# Function to stop the audio communication
def stop_audio():
    global running

    if not running:
        messagebox.showwarning("Warning", "Audio communication is not running!")
        return
    
    running = False
    status_label.config(text="Status: Disconnected")

    # Close audio streams and socket
    if input_stream:
        input_stream.stop_stream()
        input_stream.close()
    if output_stream:
        output_stream.stop_stream()
        output_stream.close()
    if sock:
        sock.close()

# Function to receive audio and play it
def receive_audio():
    global running
    while running:
        try:
            data, _ = sock.recvfrom(CHUNK * 2)
            # Apply volume scaling
            audio_data = np.frombuffer(data, dtype=np.int16) * volume_scale
            output_stream.write(audio_data.astype(np.int16).tobytes())
        except Exception as e:
            print(f"Error receiving audio: {e}")
            break

# Function to capture audio and send it
def send_audio():
    global running
    while running:
        try:
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            sock.sendto(data, (partner_ip, port))
        except Exception as e:
            print(f"Error sending audio: {e}")
            break

# Function to adjust volume
def adjust_volume(value):
    global volume_scale
    volume_scale = float(value)

# Initialize the Tkinter GUI
root = tk.Tk()
root.title("Audio Call UI")

# Configure the grid layout
root.geometry("400x200")
root.resizable(False, False)

# Start Button
start_button = ttk.Button(root, text="Start Call", command=start_audio)
start_button.grid(row=0, column=0, padx=20, pady=20)

# Stop Button
stop_button = ttk.Button(root, text="Stop Call", command=stop_audio)
stop_button.grid(row=0, column=1, padx=20, pady=20)

# Volume Slider
volume_label = ttk.Label(root, text="Volume:")
volume_label.grid(row=1, column=0, padx=10, pady=10)
volume_slider = ttk.Scale(root, from_=0.0, to=2.0, orient="horizontal", command=adjust_volume)
volume_slider.set(1.0)  # Default volume is 100%
volume_slider.grid(row=1, column=1, padx=10, pady=10)

# Status Label
status_label = ttk.Label(root, text="Status: Disconnected")
status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Function to handle closing the GUI and clean up
def on_closing():
    if running:
        stop_audio()
    root.destroy()

# Set the protocol for the window close button
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the Tkinter main loop
root.mainloop()

# Terminate PyAudio on exit
p.terminate()
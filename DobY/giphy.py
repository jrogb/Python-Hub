import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import time

class AnimatedGIF(tk.Label):
    def __init__(self, master, gif_path, delay=100):
        super().__init__(master)
        self.gif = Image.open(gif_path)
        self.frames = [ImageTk.PhotoImage(frame.copy().convert('RGBA')) for frame in ImageSequence.Iterator(self.gif)]
        self.delay = delay
        self.frame_index = 0
        self.running = False

    def start_animation(self):
        self.running = True
        self.animate()

    def stop_animation(self):
        self.running = False

    def animate(self):
        if self.running:
            self.config(image=self.frames[self.frame_index])
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.after(self.delay, self.animate)

def long_running_task(callback):
    # Simulate a long task
    time.sleep(5)
    callback()

def on_button_click():
    gif_label.start_animation()
    threading.Thread(target=long_running_task, args=(gif_label.stop_animation,)).start()

# GUI setup
root = tk.Tk()
root.title("GIF During Task")

gif_label = AnimatedGIF(root, "dobby.gif", delay=50)
gif_label.pack(pady=10)

start_button = tk.Button(root, text="Start Task", command=on_button_click)
start_button.pack(pady=10)

root.mainloop()

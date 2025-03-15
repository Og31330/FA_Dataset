import cv2
import tkinter as tk
from tkinter import filedialog, ttk
import threading
import time

class VideoAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Annotateur de vidéos de baby-foot")

        self.video_path = None
        self.cap = None
        self.playing = False
        self.frame_number = 0
        self.speed = 1.0

        self.create_widgets()

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X)

        open_button = tk.Button(control_frame, text="Ouvrir vidéo", command=self.open_video)
        open_button.grid(row=0, column=0)

        self.play_button = tk.Button(control_frame, text="▶", command=self.toggle_play)
        self.play_button.grid(row=0, column=1)

        prev_button = tk.Button(control_frame, text="◀", command=self.previous_frame)
        prev_button.grid(row=0, column=2)

        next_button = tk.Button(control_frame, text="▶", command=self.next_frame)
        next_button.grid(row=0, column=3)

        self.slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.slider.grid(row=0, column=4, sticky="ew")
        control_frame.columnconfigure(4, weight=1)

        self.frame_label = tk.Label(control_frame, text="Frame: 0")
        self.frame_label.grid(row=0, column=5)

        self.speed_combo = ttk.Combobox(control_frame, values=["x0.5", "x1", "x1.2", "x1.5", "x2", "x3", "x5", "x10"], state="readonly")
        self.speed_combo.current(1)
        self.speed_combo.bind("<<ComboboxSelected>>", self.change_speed)
        self.speed_combo.grid(row=0, column=6)

    def open_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4;*.avi;*.mov")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            self.slider.config(to=int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.playing = False
            self.frame_number = 0
            self.update_frame()

    def toggle_play(self):
        if not self.cap:
            return
        self.playing = not self.playing
        if self.playing:
            self.play_button.config(text="❚❚")
            threading.Thread(target=self.play_video, daemon=True).start()
        else:
            self.play_button.config(text="▶")

    def play_video(self):
        while self.playing and self.cap.isOpened():
            self.next_frame()
            #time.sleep(1 / (30 * self.speed))

    def next_frame(self):
        if self.cap and self.cap.isOpened():
            self.frame_number += (int)(1*self.speed)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def previous_frame(self):
        if self.cap and self.cap.isOpened() and self.frame_number > 0:
            self.frame_number -= 1
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def seek(self, value):
        if self.cap:
            self.frame_number = int(value)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def change_speed(self, event):
        speed_map = {"x0.5": 0.5, "x1": 1.0, "x1.2": 1.2, "x1.5": 1.5, "x2": 2.0, "x3": 3.0, "x5": 5.0, "x10": 10.0}
        self.speed = speed_map[self.speed_combo.get()]

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.slider.set(self.frame_number)
                self.frame_label.config(text=f"Frame: {self.frame_number}")
                img = cv2.resize(frame, (self.canvas.winfo_width(), self.canvas.winfo_height()))
                img = tk.PhotoImage(data=cv2.imencode('.ppm', img)[1].tobytes())
                self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
                self.canvas.image = img

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnnotator(root)
    root.mainloop()
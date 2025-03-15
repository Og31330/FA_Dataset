import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import threading
import os

class VideoAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Annotateur de vidéos de baby-foot")

        self.video_path = None
        self.cap = None
        self.playing = False
        self.frame_number = 0
        self.speed = 1.0
        self.output_dir = ""
        self.export_size = 224
        self.selected_class = ""

        self.create_widgets()
        self.create_preview_window()
        self.create_action_window()

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X)

        open_button = tk.Button(control_frame, text="Ouvrir vidéo", command=self.open_video)
        open_button.grid(row=0, column=0)

        self.play_button = tk.Button(control_frame, text="▶", command=self.toggle_play)
        self.play_button.grid(row=0, column=1)

        prev_button = tk.Button(control_frame, text="◀◀", command=self.previous_frame)
        prev_button.grid(row=0, column=2)

        next_button = tk.Button(control_frame, text="▶▶", command=self.next_frame)
        next_button.grid(row=0, column=3)

        self.slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.slider.grid(row=0, column=4, sticky="ew")
        control_frame.columnconfigure(4, weight=1)

        self.frame_label = tk.Label(control_frame, text="Frame: 0")
        self.frame_label.grid(row=0, column=5)

        self.speed_combo = ttk.Combobox(control_frame, values=["x0.5", "x1", "x1.2", "x1.5", "x2", "x3", "x5", "x10", "x30"], state="readonly")
        self.speed_combo.current(1)
        self.speed_combo.bind("<<ComboboxSelected>>", self.change_speed)
        self.speed_combo.grid(row=0, column=6)

        size_label = tk.Label(control_frame, text="Taille exportée:")
        size_label.grid(row=0, column=7)
        self.size_entry = tk.Entry(control_frame, width=5)
        self.size_entry.insert(0, str(self.export_size))
        self.size_entry.grid(row=0, column=8)

        output_button = tk.Button(control_frame, text="Répertoire de sortie", command=self.select_output_dir)
        output_button.grid(row=0, column=9)

        export_button = tk.Button(control_frame, text="Exporter", command=self.export_video)
        export_button.grid(row=0, column=10)

    def create_preview_window(self):
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Aperçu des prochaines frames")

        self.preview_canvas = tk.Canvas(self.preview_window)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas.images = []

        button_frame = tk.Frame(self.preview_window)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        prev_frame_button = tk.Button(button_frame, text="◀ Frame Précédente", command=self.previous_frame)
        prev_frame_button.pack(side=tk.LEFT, padx=10)

        next_frame_button = tk.Button(button_frame, text="▶ Frame Suivante", command=self.next_frame)
        next_frame_button.pack(side=tk.RIGHT, padx=10)

        radio_frame = tk.Frame(self.preview_window)
        radio_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.preview_window.bind("<Configure>", self.on_resize)

    def create_action_window(self):
        self.action_window = tk.Toplevel(self.root)
        self.action_window.title("Actions et Barres")

        action_frame = tk.Frame(self.action_window)
        action_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.action_buttons = {}
        actions = ["Control", "Shot_Goal", "Shot_Blocked", "Shot_Missed", "Shot_Unknown", "KickOff"]

        for action in actions:
            button = tk.Button(action_frame, text=action, command=lambda action=action: self.toggle_action(action))
            button.grid(row=actions.index(action), column=0, pady=5)
            self.action_buttons[action] = {"button": button, "state": False}

        bar_frame = tk.Frame(self.action_window)
        bar_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.bar_buttons = {}
        bars = ["Bar_2-1", "Bar_2-2", "Bar_1-3", "Bar_2-5", "Bar_1-5", "Bar_2-3", "Bar_1-2", "Bar_1-1", "None"]

        for bar in bars:
            button = tk.Button(bar_frame, text=bar, command=lambda bar=bar: self.toggle_bar(bar))
            button.grid(row=bars.index(bar), column=0, pady=5)
            self.bar_buttons[bar] = {"button": button, "state": False}

        self.action_label = tk.Label(self.action_window, text="Class: ")
        self.action_label.pack(pady=10)

    def toggle_action(self, action):
        for btn_action, btn_data in self.action_buttons.items():
            if btn_action != action:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

        if not self.action_buttons[action]["state"]:
            self.action_buttons[action]["button"].config(bg="yellow")
            self.action_buttons[action]["state"] = True
        else:
            self.action_buttons[action]["button"].config(bg="SystemButtonFace")
            self.action_buttons[action]["state"] = False

        if action == "KickOff":
            self.toggle_bar("None")

        self.update_action_class()

    def toggle_bar(self, bar):
        for btn_bar, btn_data in self.bar_buttons.items():
            if btn_bar != bar:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

        if not self.bar_buttons[bar]["state"]:
            self.bar_buttons[bar]["button"].config(bg="yellow")
            self.bar_buttons[bar]["state"] = True
        else:
            self.bar_buttons[bar]["button"].config(bg="SystemButtonFace")
            self.bar_buttons[bar]["state"] = False

        self.update_action_class()

    def update_action_class(self):
        action = None
        for action_name, btn_data in self.action_buttons.items():
            if btn_data["state"]:
                action = action_name
                break

        bar = None
        for bar_name, btn_data in self.bar_buttons.items():
            if btn_data["state"]:
                bar = bar_name
                break

        if action and bar:
            self.selected_class = f"{action}_{bar}"
            self.action_label.config(text=f"Class: {self.selected_class}")
        else:
            self.selected_class = ""
            self.action_label.config(text="Class: ")

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

    def next_frame(self):
        if self.cap and self.cap.isOpened():
            self.frame_number += int(1 * self.speed)
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
        speed_map = {"x0.5": 0.5, "x1": 1.0, "x1.2": 1.2, "x1.5": 1.5, "x2": 2.0, "x3": 3.0, "x5": 5.0, "x10": 10.0, "x30": 30.0}
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

                self.update_preview()

    def update_preview(self):
        preview_frames = []
        self.preview_canvas.delete("all")
        self.preview_canvas.images = []

        window_width = self.preview_window.winfo_width()
        window_height = self.preview_window.winfo_height()

        image_width = window_width // 4 - 10
        image_height = (window_height // 2) - 10

        for i in range(8):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number + i + 1)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (image_width, image_height))
                img = tk.PhotoImage(data=cv2.imencode('.ppm', frame)[1].tobytes())
                preview_frames.append(img)
                self.preview_canvas.images.append(img)

        spacing = 10

        for idx, img in enumerate(preview_frames):
            row = idx // 4
            col = idx % 4

            x_position = col * (image_width + spacing)
            y_position = row * (image_height + spacing)

            self.preview_canvas.create_image(x_position, y_position, anchor=tk.NW, image=img)
            self.preview_canvas.images[idx] = img

    def on_resize(self, event):
        self.update_preview()

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            print(f"Répertoire de sortie sélectionné: {self.output_dir}")

    def export_video(self):
        if not self.output_dir:
            print("Veuillez sélectionner un répertoire de sortie.")
            return

        if not self.selected_class:
            print("Veuillez sélectionner une classe.")
            return

        try:
            self.export_size = int(self.size_entry.get())
        except ValueError:
            print("Veuillez entrer une taille valide.")
            return

        class_output_dir = os.path.join(self.output_dir, self.selected_class)

        if not os.path.exists(class_output_dir):
            os.makedirs(class_output_dir)

        frames = []
        for i in range(8):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number + i + 1)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (self.export_size, self.export_size))
                frames.append(frame)

        video_name = os.path.splitext(os.path.basename(self.video_path))[0]
        output_file = os.path.join(class_output_dir, f"{video_name}_{self.selected_class}_{self.frame_number}.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_file, fourcc, 8.0, (self.export_size, self.export_size))

        for frame in frames:
            out.write(frame)

        out.release()
        print(f"Vidéo exportée vers {output_file}")

if __name__ == "__main__":
    root = tk.Tk()
    annotator = VideoAnnotator(root)
    root.mainloop()

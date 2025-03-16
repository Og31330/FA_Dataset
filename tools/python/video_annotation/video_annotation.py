import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import threading
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VideoAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title("Annotateur de vidéos de baby-foot")

        self.video_path = None
        self.cap = None
        self.playing = False
        self.frame_number = 0
        self.speed = 1.0
        self.export_size = 224
        self.selected_class = ""

        # Définir le répertoire par défaut
        self.default_output_dir = "D:\\FA_Dataset\\dataset\\train"
        if not os.path.exists(self.default_output_dir):
            print(f"Erreur: Le répertoire par défaut '{self.default_output_dir}' n'existe pas.")
        else:
            self.output_dir = self.default_output_dir

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

        prev_button = tk.Button(control_frame, text="◀◀◀", command=self.previous_frame)
        prev_button.grid(row=0, column=2)

        next_button = tk.Button(control_frame, text="▶▶▶", command=self.next_frame)
        next_button.grid(row=0, column=3)

        # Add buttons to navigate one frame at a time
        prev_single_button = tk.Button(control_frame, text="◀◀", command=self.previous_single_frame)
        prev_single_button.grid(row=0, column=4)

        next_single_button = tk.Button(control_frame, text="▶▶", command=self.next_single_frame)
        next_single_button.grid(row=0, column=5)

        self.slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.slider.grid(row=0, column=6, sticky="ew")
        control_frame.columnconfigure(6, weight=1)

        self.frame_label = tk.Label(control_frame, text="Frame: 0")
        self.frame_label.grid(row=0, column=7)

        self.speed_combo = ttk.Combobox(control_frame, values=["x1", "x2", "x3", "x5", "x10", "x30"], state="readonly")
        self.speed_combo.current(1)
        self.speed_combo.bind("<<ComboboxSelected>>", self.change_speed)
        self.speed_combo.grid(row=0, column=8)

        size_label = tk.Label(control_frame, text="Taille exportée:")
        size_label.grid(row=0, column=9)
        self.size_entry = tk.Entry(control_frame, width=5)
        self.size_entry.insert(0, str(self.export_size))
        self.size_entry.grid(row=0, column=10)

        output_button = tk.Button(control_frame, text="Répertoire de sortie", command=self.select_output_dir)
        output_button.grid(row=0, column=11)

        export_button = tk.Button(control_frame, text="Exporter", command=self.export_video)
        export_button.grid(row=0, column=12)

        analyze_button = tk.Button(control_frame, text="Analyser", command=self.analyze_and_display)
        analyze_button.grid(row=0, column=13)

    def previous_single_frame(self):
        if self.cap and self.cap.isOpened() and self.frame_number > 0:
            self.frame_number -= 1
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def next_single_frame(self):
        if self.cap and self.cap.isOpened():
            self.frame_number += 1
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def create_preview_window(self):
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Aperçu des prochaines frames")

        self.preview_canvas = tk.Canvas(self.preview_window)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        self.preview_canvas.images = []

        self.preview_window.bind("<Configure>", self.on_resize)

    def create_action_window(self):
        self.action_window = tk.Toplevel(self.root)

        self.action_label = tk.Label(self.action_window, text="Class: ")
        self.action_label.pack(pady=10)

        self.action_window.title("Actions")

        action_frame = tk.Frame(self.action_window)
        action_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.action_buttons = {}
        actions = ["Control", "Shot_Goal", "Shot_Blocked", "Shot_Missed", "Shot_Unknown", "KickOff"]

        for action in actions:
            button = tk.Button(action_frame, text=action, command=lambda action=action: self.toggle_action(action))
            button.grid(row=actions.index(action), column=0, pady=5)
            self.action_buttons[action] = {"button": button, "state": False}

        starter_frame = tk.Frame(self.action_window)
        starter_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.starter_buttons = {}
        starters = ["Bar_2-1", "Bar_2-2", "Bar_1-3", "Bar_2-5", "Bar_1-5", "Bar_2-3", "Bar_1-2", "Bar_1-1", "None"]

        for starter in starters:
            button = tk.Button(starter_frame, text=starter, command=lambda starter=starter: self.toggle_starter(starter))
            button.grid(row=starters.index(starter), column=0, pady=5)
            self.starter_buttons[starter] = {"button": button, "state": False}

        blocker_frame = tk.Frame(self.action_window)
        blocker_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.blocker_buttons = {}
        blockers = ["Bar_2-1", "Bar_2-2", "Bar_1-3", "Bar_2-5", "Bar_1-5", "Bar_2-3", "Bar_1-2", "Bar_1-1", "None"]

        for blocker in blockers:
            button = tk.Button(blocker_frame, text=blocker, command=lambda blocker=blocker: self.toggle_blocker(blocker))
            button.grid(row=blockers.index(blocker), column=0, pady=5)
            self.blocker_buttons[blocker] = {"button": button, "state": False}

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
            self.force_starter("None")
            self.force_blocker("None")

        if action in ["Control", "Shot_Goal", "Shot_Missed", "Shot_Unknown"]:
            self.force_blocker("None")

        self.update_action_class()

    def toggle_starter(self, starter):
        for btn_starter, btn_data in self.starter_buttons.items():
            if btn_starter != starter:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

        if not self.starter_buttons[starter]["state"]:
            self.starter_buttons[starter]["button"].config(bg="yellow")
            self.starter_buttons[starter]["state"] = True
        else:
            self.starter_buttons[starter]["button"].config(bg="SystemButtonFace")
            self.starter_buttons[starter]["state"] = False

        self.update_action_class()

    def toggle_blocker(self, blocker):
        for btn_blocker, btn_data in self.blocker_buttons.items():
            if btn_blocker != blocker:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

        if not self.blocker_buttons[blocker]["state"]:
            self.blocker_buttons[blocker]["button"].config(bg="yellow")
            self.blocker_buttons[blocker]["state"] = True
        else:
            self.blocker_buttons[blocker]["button"].config(bg="SystemButtonFace")
            self.blocker_buttons[blocker]["state"] = False

        self.update_action_class()

    def force_starter(self, starter):
        for btn_starter, btn_data in self.starter_buttons.items():
            if btn_starter == starter:
                btn_data["button"].config(bg="yellow")
                btn_data["state"] = True
            else:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

    def force_blocker(self, blocker):
        for btn_blocker, btn_data in self.blocker_buttons.items():
            if btn_blocker == blocker:
                btn_data["button"].config(bg="yellow")
                btn_data["state"] = True
            else:
                btn_data["button"].config(bg="SystemButtonFace")
                btn_data["state"] = False

    def update_action_class(self):
        action = None
        for action_name, btn_data in self.action_buttons.items():
            if btn_data["state"]:
                action = action_name
                break

        starter = None
        for starter_name, btn_data in self.starter_buttons.items():
            if btn_data["state"]:
                starter = starter_name
                break

        blocker = None
        for blocker_name, btn_data in self.blocker_buttons.items():
            if btn_data["state"]:
                blocker = blocker_name
                break

        if action and starter and blocker:
            self.selected_class = f"{action}_{starter}_{blocker}"
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
            self.frame_number -= int(1 * self.speed)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def seek(self, value):
        if self.cap:
            self.frame_number = int(value)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number)
            self.update_frame()

    def change_speed(self, event):
        speed_map = {"x1": 1.0, "x3": 3.0, "x5": 5.0, "x10": 10.0, "x30": 30.0}
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
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number + i )
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
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number + i )
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

    def analyze_and_display(self):
        if not self.output_dir:
            print("Veuillez sélectionner un répertoire de sortie.")
            return

        class_counts = self.count_videos_per_class(self.output_dir)
        self.display_graph(class_counts)

    def count_videos_per_class(self, directory):
        class_counts = {}
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".avi"):
                    class_name = os.path.basename(root)
                    if class_name not in class_counts:
                        class_counts[class_name] = 0
                    class_counts[class_name] += 1
        return class_counts
    
    def display_graph(self, class_counts):
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Graphique d'analyse des vidéos")
    
        fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figure size
        classes = list(class_counts.keys())
        counts = list(class_counts.values())
    
        ax.bar(classes, counts)
        ax.set_xlabel("Classes")
        ax.set_ylabel("Nombre de vidéos")
        ax.set_title("Nombre de vidéos extraites par classe")
    
        # Rotate class names by 90 degrees and adjust padding
        ax.set_xticklabels(classes, rotation=90, ha='right')
        fig.tight_layout()  # Adjust layout to make room for labels
    
        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    annotator = VideoAnnotator(root)
    root.mainloop()

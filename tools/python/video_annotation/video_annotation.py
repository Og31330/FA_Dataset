import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import threading

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
        self.create_preview_window()
        self.create_action_window()  # Nouvelle fenêtre pour les actions et les barres

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

        self.speed_combo = ttk.Combobox(control_frame, values=["x0.5", "x1", "x1.2", "x1.5", "x2", "x3", "x5", "x10"], state="readonly")
        self.speed_combo.current(1)
        self.speed_combo.bind("<<ComboboxSelected>>", self.change_speed)
        self.speed_combo.grid(row=0, column=6)

    def create_preview_window(self):
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.title("Aperçu des prochaines frames")

        self.preview_canvas = tk.Canvas(self.preview_window)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Création d'une liste vide pour stocker les images de l'aperçu
        self.preview_canvas.images = []

        # Bind à l'événement de redimensionnement de la fenêtre pour actualiser l'affichage
        self.preview_window.bind("<Configure>", self.on_resize)

    def create_action_window(self):
        self.action_window = tk.Toplevel(self.root)
        self.action_window.title("Actions et Barres")

        # Section Action
        action_frame = tk.Frame(self.action_window)
        action_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.action_buttons = {}
        actions = ["Control", "Shot_Goal", "Shot_Blocked", "Shot_Missed", "Shot_Unknown", "KickOff"]

        for action in actions:
            button = tk.Button(action_frame, text=action, command=lambda action=action: self.toggle_action(action))
            button.grid(row=actions.index(action), column=0, pady=5)
            self.action_buttons[action] = {"button": button, "state": False}

        # Section Bar
        bar_frame = tk.Frame(self.action_window)
        bar_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.bar_buttons = {}
        bars = ["Bar_2-1", "Bar_2-2", "Bar_1-3", "Bar_2-5", "Bar_1-5", "Bar_2-3", "Bar_1-2", "Bar_1-1", "None"]

        for bar in bars:
            button = tk.Button(bar_frame, text=bar, command=lambda bar=bar: self.toggle_bar(bar))
            button.grid(row=bars.index(bar), column=0, pady=5)
            self.bar_buttons[bar] = {"button": button, "state": False}

        # Affichage du nom de l'action
        self.action_label = tk.Label(self.action_window, text="Class: ")
        self.action_label.pack(pady=10)

    def toggle_action(self, action):
        # Réinitialise l'état de tous les boutons de la section Action
        for btn_action, btn_data in self.action_buttons.items():
            if btn_action != action:
                btn_data["button"].config(bg="SystemButtonFace")  # Réinitialiser la couleur
                btn_data["state"] = False

        # Change la couleur du bouton sélectionné
        if not self.action_buttons[action]["state"]:
            self.action_buttons[action]["button"].config(bg="yellow")
            self.action_buttons[action]["state"] = True
        else:
            self.action_buttons[action]["button"].config(bg="SystemButtonFace")
            self.action_buttons[action]["state"] = False

        # Si l'action "KickOff" est sélectionnée, automatiquement sélectionner "None"
        if action == "KickOff":
            self.toggle_bar("None")  # Sélectionne le bouton "None" dans la section Bar

        # Mettre à jour le nom de l'action
        self.update_action_class()

    def toggle_bar(self, bar):
        # Réinitialise l'état de tous les boutons de la section Bar
        for btn_bar, btn_data in self.bar_buttons.items():
            if btn_bar != bar:
                btn_data["button"].config(bg="SystemButtonFace")  # Réinitialiser la couleur
                btn_data["state"] = False

        # Change la couleur du bouton sélectionné
        if not self.bar_buttons[bar]["state"]:
            self.bar_buttons[bar]["button"].config(bg="yellow")
            self.bar_buttons[bar]["state"] = True
        else:
            self.bar_buttons[bar]["button"].config(bg="SystemButtonFace")
            self.bar_buttons[bar]["state"] = False

        # Mettre à jour le nom de l'action
        self.update_action_class()

    def update_action_class(self):
        # Vérifie si un bouton Control est sélectionné
        action = None
        for action_name, btn_data in self.action_buttons.items():
            if btn_data["state"]:
                action = action_name
                break

        # Vérifie si un bouton Bar est sélectionné
        bar = None
        for bar_name, btn_data in self.bar_buttons.items():
            if btn_data["state"]:
                bar = bar_name
                break

        # Affiche la classe si une action et une barre sont sélectionnées
        if action and bar:
            self.action_label.config(text=f"Class: {action}_{bar}")
        else:
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

                self.update_preview()

    def update_preview(self):
        preview_frames = []

        # Efface les anciennes images avant d'afficher les nouvelles
        self.preview_canvas.delete("all")

        # Crée une liste pour stocker les images de l'aperçu
        self.preview_canvas.images = []

        # Obtient la taille actuelle de la fenêtre
        window_width = self.preview_window.winfo_width()
        window_height = self.preview_window.winfo_height()

        # Calcul de la taille des images pour les adapter à la fenêtre
        image_width = window_width // 4 - 10  # 4 images par ligne
        image_height = (window_height // 2) - 10  # 2 lignes d'images

        # Modifié pour afficher 8 images sur 2 lignes, avec 4 images par ligne
        for i in range(8):  # Affiche 8 images
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_number + i + 1)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, (image_width, image_height))  # Redimensionner les images
                img = tk.PhotoImage(data=cv2.imencode('.ppm', frame)[1].tobytes())
                preview_frames.append(img)
                
                # Stocke chaque image dans la liste
                self.preview_canvas.images.append(img)

        # Affiche les images en 2 lignes, 4 images par ligne
        spacing = 10  # Espacement entre les images

        for idx, img in enumerate(preview_frames):
            row = idx // 4  # Déterminer la ligne (0 ou 1)
            col = idx % 4  # Déterminer la colonne (0 à 3)

            # Calculer la position des images
            x_position = col * (image_width + spacing)
            y_position = row * (image_height + spacing)

            self.preview_canvas.create_image(x_position, y_position, anchor=tk.NW, image=img)

            # Maintient la référence à chaque image
            self.preview_canvas.images[idx] = img

    def on_resize(self, event):
        """Met à jour l'affichage des images lorsque la fenêtre est redimensionnée."""
        self.update_preview()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnnotator(root)
    root.mainloop()

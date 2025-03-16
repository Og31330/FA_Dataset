import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def count_videos_per_class(directory):
    class_counts = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".avi"):  # Assuming the videos are in .avi format
                class_name = os.path.basename(root)
                if class_name not in class_counts:
                    class_counts[class_name] = 0
                class_counts[class_name] += 1
    return class_counts

def display_graph(class_counts):
    root = tk.Tk()
    root.title("Graphique d'analyse des vidéos")
    root.geometry("800x600")  # Set initial size
    root.resizable(True, True)  # Make window resizable

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

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    root.mainloop()

def main():
    # Specify the directory containing the exported videos
    directory = filedialog.askdirectory(title="Sélectionner le répertoire d'export")

    if not directory:
        print("Aucun répertoire sélectionné.")
        return

    if not os.path.exists(directory):
        print(f"Erreur: Le répertoire '{directory}' n'existe pas.")
        return

    class_counts = count_videos_per_class(directory)
    display_graph(class_counts)

if __name__ == "__main__":
    main()

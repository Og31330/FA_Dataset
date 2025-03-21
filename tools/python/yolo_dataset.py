import os
import cv2

# Chemins des répertoires
dataset_dir = "D:/FA_Dataset/dataset/train"
raw_video_dir = "D:/raw_videos"
output_dir = "D:/raw_videos/raw_frame"

# Créer le répertoire de sortie s'il n'existe pas
os.makedirs(output_dir, exist_ok=True)

# Parcourir les sous-répertoires de classes
for class_name in os.listdir(dataset_dir):
    class_dir = os.path.join(dataset_dir, class_name)

    # Vérifier si c'est un répertoire
    if os.path.isdir(class_dir):
        # Parcourir les vidéos dans le sous-répertoire
        for video_file in os.listdir(class_dir):
            # Extraire le nom de la vidéo originale et l'index de la frame de départ
            parts = video_file.rsplit('_', 3)
            video_name = parts[0]  # Prendre uniquement la partie avant le nom de la classe
            start_frame_index = int(parts[3].split('.')[0])  # Supposons que l'index est après le dernier '_'

            video_path = os.path.join(raw_video_dir, video_name + ".mp4")
            print(video_path)

            # Vérifier si la vidéo originale existe
            if os.path.exists(video_path):
                # Ouvrir la vidéo
                cap = cv2.VideoCapture(video_path)

                # Aller à la frame de départ
                cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_index)

                # Extraire 8 frames consécutives
                frame_count = 0
                success, frame = cap.read()
                while success and frame_count < 8:
                    # Redimensionner la frame à 640x640
                    frame = cv2.resize(frame, (640, 640))
                    # Sauvegarder la frame
                    frame_filename = f"{video_name}_frame{start_frame_index + frame_count}.jpg"
                    frame_path = os.path.join(output_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)

                    # Lire la frame suivante
                    success, frame = cap.read()
                    frame_count += 1

                # Libérer la vidéo
                cap.release()
            else:
                print(f"Vidéo originale non trouvée pour {video_name} (fichier attendu: {video_name}.mp4)")

print("Extraction des frames terminée.")

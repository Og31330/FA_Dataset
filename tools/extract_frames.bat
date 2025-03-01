@echo off
setlocal enabledelayedexpansion

:: Vérifier si un argument est fourni
if "%~1"=="" (
    echo Usage: %~nx0 "C:\chemin\vers\video.mp4"
    exit /b 1
)

:: Définir temporairement le chemin de FFmpeg
set "FFMPEG_PATH=D:\FA_Dataset\tools\ffmpeg-master-latest-win64-gpl-shared\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"

:: Récupérer le chemin complet et extraire le nom du fichier sans l'extension
set "video_path=%~1"
set "video_name=%~n1"
set "video_dir=%~dp1"
set "output_dir=%video_dir%%video_name%"

:: Créer le dossier de sortie si inexistant
if not exist "%output_dir%" mkdir "%output_dir%"

:: Extraire les frames redimensionnées en 128x128 avec FFmpeg
ffmpeg -i "%video_path%" -vf "scale=128:128" "%output_dir%/%video_name%_%%04d.png"

echo Extraction et redimensionnement terminés. Les frames sont dans: "%output_dir%"
exit /b 0

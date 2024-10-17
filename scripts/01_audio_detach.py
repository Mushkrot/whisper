# -*- coding: utf-8 -*-
import time
import os
from pathlib import Path
import subprocess

# Start time tracking
start_time = time.time()

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
video_dir = base_dir / 'data' / 'input'
audio_output_dir = base_dir / 'data' / 'input'

# Create the output directory for audio files if it doesn't exist
os.makedirs(audio_output_dir, exist_ok=True)

# Function to generate a unique filename
def get_unique_filename(base_name, extension, directory):
    counter = 1
    unique_name = f"{base_name}.{extension}"
    while os.path.exists(os.path.join(directory, unique_name)):
        unique_name = f"{base_name}_v{counter}.{extension}"
        counter += 1
    return unique_name

# List all video files (supporting multiple extensions)
supported_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')  # Add other formats as needed
video_files = [f for f in os.listdir(video_dir) if f.lower().endswith(supported_extensions)]

# Process each video file
for index, filename in enumerate(video_files):
    # Calculate progress percentage
    progress = (index + 1) / len(video_files) * 100

    # Full path to the video file
    video_path = os.path.join(video_dir, filename)

    # Determine the name of the output audio file
    base_name = os.path.splitext(filename)[0]
    output_filename = get_unique_filename(base_name, 'mp3', audio_output_dir)
    output_path = os.path.join(audio_output_dir, output_filename)

    # Extract audio using ffmpeg with noise reduction
    print(f"Extracting and cleaning audio from {filename}... ({progress:.2f}% completed)")

    # Build the ffmpeg command with the afftdn filter
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vn',
        '-ac', '1',
        '-ar', '24000',
        '-b:a', '192k',  # Set bitrate to 192kbps
        '-c:a', 'libmp3lame',  # MP3 encoding
        # '-c:a', 'pcm_s24le', #24-bit uncompressed PCM (Pulse Code Modulation)

        # Noise reduction filter with parameters:
        # nr: Noise reduction level in decibels (0-80)
        # nt: Noise threshold (0.0-1.0)
        # EQ adjustments for voice clarity:
        # High-pass filter to remove rumble below 100Hz
        # Low-pass filter to remove high frequencies above 8000Hz
        # Equalizer to boost frequencies around 3000Hz for speech intelligibility
        # '-af', 'afftdn=nr=20.0:nt=0.03,highpass=f=100,lowpass=f=8000,equalizer=f=3000:t=q:w=1:g=5',

        output_path
    ]

    try:
        # Run the ffmpeg command to extract and clean the audio
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Cleaned audio extracted and saved as: {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {filename}: {e.stderr.decode('utf-8')}")

    print(f"Progress: {progress:.2f}%")

print("\nAll video files have been processed.")

# End time tracking
end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"Time taken for processing: {int(minutes)} minutes and {seconds:.2f} seconds\n")

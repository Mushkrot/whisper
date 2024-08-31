import os
import subprocess

# Paths to input and output directories
input_dir = 'input/video'
output_dir = 'output/audio'

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Function to extract audio and save in LINEAR16 (PCM) format
def extract_audio(input_video_path, output_audio_path):
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-acodec', 'pcm_s16le',  # Use PCM 16-bit little-endian (LINEAR16)
        '-ac', '1',  # Set to mono
        '-ar', '16000',  # Set sample rate to 16 kHz
        output_audio_path
    ]
    subprocess.run(command, check=True)

# Process each video file in the input directory
for filename in os.listdir(input_dir):
    if not filename.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
        continue

    input_video_path = os.path.join(input_dir, filename)
    output_audio_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.wav')

    # Handle file name conflicts
    counter = 1
    while os.path.exists(output_audio_path):
        base_name = os.path.splitext(filename)[0]
        output_audio_path = os.path.join(output_dir, f"{base_name}_v{counter}.wav")
        counter += 1

    print(f"Extracting audio from {filename}...")
    extract_audio(input_video_path, output_audio_path)
    print(f"Saved audio to {output_audio_path}")

print("All video files have been processed.")

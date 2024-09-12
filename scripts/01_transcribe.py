# -*- coding: utf-8 -*-
import time
import os
import whisper
from pathlib import Path

# Print output to log file
import sys
class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()
logfile = open('output.log', 'a')  # Open log file
sys.stdout = Tee(sys.stdout, logfile)  # Redirect concole to log

# Start time tracking
start_time = time.time()

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
audio_dir = base_dir / 'data' / 'input'
srt_dir = base_dir / 'data' / 'output' / 'ru'  / 'srt'
txt_dir = base_dir / 'data' / 'output' / 'ru'  / 'txt'

# Ensure the output directories exist
os.makedirs(srt_dir, exist_ok=True)
os.makedirs(txt_dir, exist_ok=True)

# Load the Whisper model
model = whisper.load_model("large")  # You can choose "tiny", "base", "small", "medium", "large" based on your needs

context = (
    "Лекции, задачи и примеры по алгебре."
    "Алгебраические уравнения и неравенства"
    "Показательные, оинейные, не линейные и логарифмические функции"
    "Пример: 'y = lg tg x + lg ctg x' – это 'игрек равен лг тангенс икс плюс лг котангенс икс"
    "Пример: 'y = log x 1' – это 'игрек равен логарифм икс один"
)

# Function to generate a unique filename
def get_unique_filename(base_name, extension, directory):
    counter = 1
    unique_name = f"{base_name}.{extension}"
    while os.path.exists(os.path.join(directory, unique_name)):
        unique_name = f"{base_name}_v{counter}.{extension}"
        counter += 1
    return unique_name

# Custom function to convert results to SRT format
def result_to_srt(result):
    srt_content = []
    for i, segment in enumerate(result['segments']):
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        srt_content.append(f"{i + 1}")
        srt_content.append(f"{format_time(start)} --> {format_time(end)}")
        srt_content.append(text)
        srt_content.append("")
    return "\n".join(srt_content)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

# List all audio files (handling multiple extensions)
supported_extensions = ('.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac')  # Add other supported formats as needed
audio_files = [f for f in os.listdir(audio_dir) if f.lower().endswith(supported_extensions)]

# Process each audio file
for index, filename in enumerate(audio_files):
    # Calculate progress percentage
    progress = (index + 1) / len(audio_files) * 100
    
    # Full path to the audio file
    audio_path = os.path.join(audio_dir, filename)
    
    # Transcribe the audio file with explicit Russian language setting
    print(f"Transcribing {filename}... ({progress:.2f}% completed)")
    result = model.transcribe(
        audio_path,
        language="ru",
        initial_prompt=context,
        task="transcribe",
        beam_size=5,
        best_of=5,
        temperature=0.1,
        fp16=False,
        condition_on_previous_text=False,
        verbose=True
    )
    
    # Save the raw text output before any further processing
    raw_text_filename = get_unique_filename(os.path.splitext(filename)[0], 'txt', txt_dir)
    with open(os.path.join(txt_dir, raw_text_filename), 'w', encoding='utf-8') as raw_text_file:
        raw_text_file.write(result['text'])
    print(f"Saved raw text file: {raw_text_filename}")
    
    # Determine output file type
    if 'segments' in result:  # This indicates the presence of time codes
        output_extension = 'srt'
        srt_content = result_to_srt(result)
        base_name = os.path.splitext(filename)[0]
        output_filename = get_unique_filename(base_name, output_extension, srt_dir)
        
        # Write the .srt file
        with open(os.path.join(srt_dir, output_filename), 'w', encoding='utf-8') as srt_file:
            srt_file.write(srt_content)
        print(f"Saved SRT file: {output_filename}")
    
    print(f"Progress: {progress:.2f}%")

print("\nAll audio files have been transcribed.")

# End time tracking
end_time = time.time()

# Calculate and print the elapsed time
elapsed_time = end_time - start_time
minutes, seconds = divmod(elapsed_time, 60)
print(f"Time taken for transcription: {int(minutes)} minutes and {seconds:.2f} seconds\n\n")

logfile.close()  # Close log file
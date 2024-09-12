# -*- coding: utf-8 -*-
import openai
import os
import pysrt
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
sys.stdout = Tee(sys.stdout, logfile)  # Redirect console to log

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / 'data' / 'output' / 'ru' / 'verbalized'
output_dir = base_dir / 'data' / 'output' / 'uk'

# Ensure the output directories exist
os.makedirs(output_dir, exist_ok=True)

# Getting the API key from the file
def get_api_key():
    """Reads the OpenAI API key from a file."""
    try:
        with open('api_key.txt', 'r') as f:
            api_key = f.read().strip()
        return api_key
    except FileNotFoundError:
        print("Error: 'api_key.txt' not found. Please ensure the file exists.")
        sys.exit(1)

openai.api_key = get_api_key()

# Function to translate text using OpenAI GPT-4
def translate_text(text, source_language="ru", target_language="uk"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    f"You are a translator. Translate the following text from {source_language} to {target_language}. "
                    "The text is from a mathematical lecture (algebra and geometry), use the appropriate terminology "
                    "for mathematical contexts. Specifically, avoid the following mistakes: "
                    "'сусідніх' should be translated as 'сумiжних', "
                    "'нахилені' as 'похилі', "
                    "'рівне' as 'дорівнює', "
                    "'бокові сторони' as 'бічні сторони', "
                    "'підстави' as 'основи', "
                    "'точка' as 'крапка', "
                    "'ступінь' (ж.р.) as 'степінь' (м.р.), "
                    "'позитивні' as 'додатні'."
                )},
                {"role": "user", "content": f"{text}"}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error during translation: {e}")
        return text  # Return the original text in case of an error

# Function to process a single SRT file
def process_srt_file(input_file, output_file):
    try:
        subs = pysrt.open(input_file, encoding='utf-8')
    except Exception as e:
        print(f"Error loading subtitle file: {e}")
        subs = None

    # Translate subtitles
    if subs:
        total_subs = len(subs)  # Get the total number of subtitle blocks
        for idx, sub in enumerate(subs, start=1):
            translated_text = translate_text(sub.text, source_language="ru", target_language="uk")
            sub.text = translated_text  # Replace the original text with the translated text

            # Print the progress of processing subtitle blocks
            print(f"Translated subtitle {idx} of {total_subs}...")

        # Save the translated file while preserving the timestamps
        try:
            subs.save(output_file, encoding='utf-8')
        except Exception as e:
            print(f"Error saving subtitle file: {e}")

# Process all SRT files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.srt'):
        input_file = input_dir / filename
        
        # Remove 'verbalized' from the filename and add '_uk' before the extension
        output_filename = filename.replace('_verbalized', '').replace('.srt', '_uk.srt')
        output_file = output_dir / output_filename
        
        print(f"Processing {input_file}...")
        process_srt_file(input_file, output_file)
        print(f"Processed {input_file} -> {output_file}")

logfile.close()  # Close log file after processing all files

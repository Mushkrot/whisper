# -*- coding: utf-8 -*-
import openai
import os
import pysrt
from pathlib import Path

logfile = open('correction_output.log', 'a')  # Open log file for corrections
sys.stdout = Tee(sys.stdout, logfile)  # Redirect console to log

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / 'data' / 'output' / 'uk'  # Directory with translated SRT files
output_dir = base_dir / 'data' / 'output' / 'uk' / 'corrected'  # Directory for corrected files

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

# Function to correct text based on specific rules
def correct_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are a corrector for mathematical text translations from Russian to Ukrainian. "
                    "Your task is to make minimal changes based on specific rules: "
                    "1. Replace 'S1, S2' with 'C1, C2'. "
                    "2. Replace 'C, C1' with 'Ц, Ц1' (only if they represent mathematical figures or variables). "
                    "3. Replace 'H' with 'АШ'. "
                    "4. Replace lowercase 'а' with uppercase 'А' if it represents a variable. "
                    "5. Replace 'кут Б' with 'кут Бетта', 'кут А' with 'кут Альфа', etc., if they represent angles. "
                    "6. Replace 'площа S' with 'площа C'. "
                    "Use your judgment and context to decide if the letter refers to a mathematical variable or figure. "
                    "Do not modify text if you are uncertain of its context. If a term doesn't seem mathematical, leave it unchanged."
                )},
                {"role": "user", "content": f"{text}"}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error during correction: {e}")
        return text  # Return the original text in case of an error

# Function to process a single SRT file
def process_srt_file(input_file, output_file):
    try:
        subs = pysrt.open(input_file, encoding='utf-8')
    except Exception as e:
        print(f"Error loading subtitle file: {e}")
        subs = None

    # Correct subtitles
    if subs:
        total_subs = len(subs)  # Get the total number of subtitle blocks
        for idx, sub in enumerate(subs, start=1):
            corrected_text = correct_text(sub.text)
            sub.text = corrected_text  # Replace the original text with the corrected text

            # Print the progress of processing subtitle blocks
            print(f"Corrected subtitle {idx} of {total_subs}...")

        # Save the corrected file while preserving the timestamps
        try:
            subs.save(output_file, encoding='utf-8')
        except Exception as e:
            print(f"Error saving subtitle file: {e}")

# Process all SRT files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.srt'):
        input_file = input_dir / filename
        
        # Add '_corrected' before the extension to indicate it's a corrected file
        output_filename = filename.replace('.srt', '_corrected.srt')
        output_file = output_dir / output_filename
        
        print(f"Processing {input_file} for corrections...")
        process_srt_file(input_file, output_file)
        print(f"Processed {input_file} -> {output_file}")

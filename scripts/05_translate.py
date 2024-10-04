# -*- coding: utf-8 -*-
from openai import OpenAI

import os
import pysrt
import sys
import time
from pathlib import Path

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
input_dir = base_dir / 'data' / 'output'
output_dir = base_dir / 'data' / 'output'

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

client = OpenAI(api_key=get_api_key())

# Configuration for batch processing
blocks_per_request = 10  # Number of subtitle blocks to send in one request
separator = "<|SUB_SEPARATOR|>"  # Unique separator to join subtitle texts

# Function to translate a batch of texts using OpenAI GPT-4
# New models are "o1-preview" and "o1-mini".
# gpt-4o-2024-08-06:    approximately   $0.030 per 15 min srt file
# o1-mini:              approximately   $0.036 per 15 min srt file
# o1-preview:           approximately   $0.18 per 15 min srt file
def translate_text_batch(text_batch, source_language="ru", target_language="uk"):
    try:
        response = client.chat.completions.create(model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system", "content": (
                    f"""You are a translator. Translate the following text from {source_language} to {target_language}.
The text is from a mathematical lecture (algebra and geometry), so please use the correct mathematical terminology in {target_language}.
Important: Do not replace letter representations of mathematical symbols with the symbols themselves or use mathematical notation.
Instead, replace the {source_language} letters representing mathematical symbols with {target_language} letters or letter combinations that convey the same pronunciation, considering the nuances of the {target_language} language.
For example:
- Replace 'икс' with 'ікс'.
- Replace 'аШ' with 'аШ'.
- Replace 'С-один' with 'С-один'.
- Replace 'С-четыре' with 'С-чотири'.
- Replace 'икс квадрат' with 'ікс квадрат'.
- Do not introduce mathematical symbols, Latin, or Greek letters in the translation. Keep all designations in {target_language} alphabet letters.
- Please pay attention to the following terminology preferences:
- Use 'суміжних' instead of 'сусідніх'.
- Use 'похилі' вместо 'нахилені'.
- Use 'дорівнює' вместо 'рівне'.
- Use 'бічні сторони' вместо 'бокові сторони'.
- Use 'основи' вместо 'підстави'.
- Use 'крапка' вместо 'точка'.
- Use 'степінь' (masculine) вместо 'ступінь' (feminine).
- Use 'додатні' вместо 'позитивні'.
Please ensure that multiple subtitle blocks are separated by the unique separator "<|SUB_SEPARATOR|>" and translate each block individually while preserving the separator."""
                )
            },
            {"role": "user", "content": f"{text_batch}"}
        ],
        max_tokens=1500 * blocks_per_request,  # Adjust max_tokens based on batch size
        temperature=0.3)
        translated_text = response.choices[0].message.content.strip()
        return translated_text
    except Exception as e:
        print(f"Error during batch translation: {e}")
        return text_batch.replace(separator, '\n')  # Return the original text in case of an error

# Function to process a single SRT file with batch translation
def process_srt_file(input_file, output_file):
    try:
        subs = pysrt.open(input_file, encoding='utf-8')
    except Exception as e:
        print(f"Error loading subtitle file '{input_file}': {e}")
        return  # Exit the function if loading fails

    total_subs = len(subs)  # Get the total number of subtitle blocks

    # Process subtitles in batches
    for start in range(0, total_subs, blocks_per_request):
        end = min(start + blocks_per_request, total_subs)
        batch = subs[start:end]

        # Concatenate the text of the current batch of subtitles using the unique separator
        batch_text = separator.join([sub.text.replace('\n', ' ') for sub in batch])  # Replace newlines to maintain block integrity

        # Translate the concatenated batch text
        translated_batch_text = translate_text_batch(batch_text, source_language="ru", target_language="uk")

        # Split the translated text back into individual subtitle blocks using the unique separator
        translated_texts = translated_batch_text.split(separator)

        # Check if the number of translated texts matches the number of original blocks
        if len(translated_texts) != len(batch):
            print(f"Warning: Mismatch in number of translated blocks. Expected {len(batch)}, got {len(translated_texts)}.")
            # Handle the mismatch by skipping this batch
            for sub in batch:
                print(f"Skipping translation for subtitle starting at {sub.start} due to mismatch.")
            continue  # Skip this batch

        # Assign the translated texts back to the subtitle blocks
        for i, sub in enumerate(batch):
            sub.text = translated_texts[i].strip()

        # Print the progress of processing subtitle blocks in batches
        print(f"Translated subtitles {start + 1} to {end} of {total_subs}...")

        # Add a delay between API requests to avoid hitting rate limits
        time.sleep(0.5)  # Adjust the sleep duration as needed

    # Save the translated file while preserving the timestamps
    try:
        subs.save(output_file, encoding='utf-8')
    except Exception as e:
        print(f"Error saving subtitle file '{output_file}': {e}")

# Function to process all SRT files in the input directory
def process_directory(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.srt'):
            input_file = input_dir / filename

            # Remove 'verbalized' from the filename and add '_uk' before the extension
            output_filename = filename.replace('.srt', '_uk.srt')
            output_file = output_dir / output_filename

            print(f"Processing {input_file}...")
            process_srt_file(input_file, output_file)
            print(f"Processed {input_file} -> {output_file}\n\n")

# Main function to run the script
def main():
    process_directory(input_dir, output_dir)
    print("All files processed.\n\n")

if __name__ == "__main__":
    main()

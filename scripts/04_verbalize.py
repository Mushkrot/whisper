# -*- coding: utf-8 -*-
import re
import os
from openai import OpenAI

import pysrt
from num2words import num2words
import argparse
from pathlib import Path

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
input_dir =  base_dir / 'data' / 'output'
output_dir = base_dir / 'data' / 'output'
blocks_per_request = 10  # Number of subtitle blocks to send in one request

# Ensure the output directories exist
os.makedirs(output_dir, exist_ok=True)

# Getting the API key from the file
def get_api_key():
    """Reads the OpenAI API key from a file."""
    with open('api_key.txt', 'r') as f:
        api_key = f.read().strip()
    return api_key

client = OpenAI(api_key=get_api_key())

# Function to replace numbers with their word equivalents considering correct grammar forms
def replace_numbers(text):
    def num_to_word(match):
        number = int(match.group())
        # Convert number to Russian text with correct forms
        try:
            return num2words(number, lang='ru')
        except NotImplementedError:
            return str(number)

    # Find and replace all numbers in the text
    return re.sub(r'\b\d+\b', num_to_word, text)

# Function to interact with OpenAI using the chat-completions API and explain the task of replacing variables and numbers
def use_openai_for_replacements(text_batch):
    # Create instruction for OpenAI
    separator = "<|SUB_SEPARATOR|>"
    messages = [
        {"role": "system", "content": "You are a language assistant specializing in text preprocessing for speech synthesis. Your task is to process Russian subtitles from mathematics lectures to prepare them for text-to-speech conversion."},
        {"role": "system", "content": "In the text, replace all mathematical variables (such as 'x', 'y', 'z', 'π', and any other letters, including Greek letters like 'α', 'β', 'γ', 'Ω') with their Russian word equivalents (e.g., 'икс', 'игрек', 'зет', 'пи', 'альфа', 'бета', 'гамма', 'омега'), ensuring proper grammatical case and agreement in the context."},
        {"role": "system", "content": "For sequences of uppercase letters representing geometric figures or designations (e.g., 'OA', 'ABCD'), transform each letter to its Russian uppercase equivalent in Cyrillic, separated by hyphens. For example, 'отрезок OA' becomes 'отрезок О-А', 'фигура ABCD' becomes 'фигура А-Б-Ц-Д'."},
        {"role": "system", "content": "All such letters that should be read separately as mathematical symbols or designations should be printed in uppercase Cyrillic letters."},
        {"role": "system", "content": "Replace all numbers with their word equivalents in Russian, using correct grammar and case. This includes cardinal numbers, ordinal numbers, and numbers in mathematical expressions."},
        {"role": "system", "content": "Replace any mathematical symbols or operators (like '+', '-', '*', '/', '=', '>', '<', '≥', '≤') with their word equivalents in Russian, ensuring correct grammatical usage."},
        {"role": "system", "content": "Do not alter any other content. Preserve any punctuation, formatting, or separators (like '<|SUB_SEPARATOR|>') exactly as they are."},
        {"role": "system", "content": "Examples:"},
        {"role": "system", "content": "'x = 10' -> 'икс равно десять'"},
        {"role": "system", "content": "'3.14' -> 'три целых четырнадцать сотых'"},
        {"role": "system", "content": "'5 в степени x' -> 'пять в степени икс'"},
        {"role": "system", "content": "'x > 0' -> 'икс больше нуля'"},
        {"role": "system", "content": "'н = 0' -> 'игрек равен нулю'"},
        {"role": "system", "content": "'cos 2x' -> 'косинус двух икс'"},
        {"role": "system", "content": "'sin 3y' -> 'синус трёх игрек'"},
        {"role": "system", "content": "'отрезок OA' -> 'отрезок О-А'"},
        {"role": "system", "content": "'фигура ABCD' -> 'фигура А-Б-Ц-Д'"},
        {"role": "system", "content": f"Process the following text accordingly, ensuring all instances of '{separator}' are preserved exactly as they are."},
        {"role": "user", "content": text_batch}
    ]

    # Use the ChatCompletion endpoint
    # New models are "o1-preview" and "o1-mini".
    # GPT-4o:       approximately   $0.030 per 15 min srt file
    # o1-mini:      approximately   $0.036 per 15 min srt file
    # o1-preview:   approximately   $0.18 per 15 min srt file
    response = client.chat.completions.create(model="gpt-4o-2024-08-06",
    messages=messages,
    max_tokens=1500,
    temperature=0.3)

    # Return the processed text from OpenAI
    return response.choices[0].message.content

# Function to process a single SRT file using pysrt
def process_srt_file(input_file, output_file):
    subs = pysrt.open(input_file, encoding='utf-8')
    total_subs = len(subs)  # Get the total number of subtitle blocks
    modified_subs = []  # List to store modified subtitles
    separator = "<|SUB_SEPARATOR|>"  # Unique separator unlikely to appear in subtitles

    # Process subtitles in batches
    for start in range(0, total_subs, blocks_per_request):
        end = min(start + blocks_per_request, total_subs)
        batch = subs[start:end]

        # Concatenate the text of the current batch of subtitles using the unique separator
        batch_text = separator.join([sub.text for sub in batch])

        # First, replace numbers with words in the entire batch
        modified_batch_text = replace_numbers(batch_text)

        # Then, use OpenAI to intelligently replace Latin variables and adjust grammar
        modified_batch_text = use_openai_for_replacements(modified_batch_text)

        # Split the modified text back into individual subtitle blocks using the unique separator
        modified_batch_texts = modified_batch_text.split(separator)

        # Check if the lengths match
        if len(modified_batch_texts) != len(batch):
            print(f"Warning: Mismatch in lengths. Expected {len(batch)}, got {len(modified_batch_texts)}.")
            # Handle the mismatch if necessary
            continue  # Skip this batch or handle accordingly

        # Update each subtitle block with the modified text
        for i, sub in enumerate(batch):
            sub.text = modified_batch_texts[i]
            modified_subs.append(sub)

        # Print the progress of processing subtitle blocks in batches
        print(f"Verbalized blocks {start + 1} to {end} of {total_subs}...")

    # Save the modified subtitles to the output file
    subs.save(output_file, encoding='utf-8')

# Function to process all SRT files in the specified directory
def process_directory(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.srt'):
            input_file = os.path.join(input_dir, filename)
            # Change name if requiered
            output_file = os.path.join(output_dir, filename.replace('.srt', '.srt'))

            print(f"Processing {input_file}...")
            process_srt_file(input_file, output_file)
            print(f"Processed {input_file} -> {output_file}")

# Main function to run the script
def main():
    parser = argparse.ArgumentParser(description="Process SRT files in a directory to replace numbers with words and Latin variables with their equivalents, using OpenAI.")
    parser.add_argument("--input_dir", default=input_dir, help="Path to the input directory containing SRT files")
    parser.add_argument("--output_dir", default=output_dir, help="Path to the output directory (optional, defaults to input directory)")

    args = parser.parse_args()

    # Check if the input directory exists
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory {args.input_dir} not found.")
        return

    # Process all SRT files in the directory
    process_directory(args.input_dir, args.output_dir)
    print("All files verbalized.\n\n")

if __name__ == "__main__":
    main()

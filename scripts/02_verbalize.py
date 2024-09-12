# -*- coding: utf-8 -*-
import re
import os
import openai
import pysrt
from num2words import num2words
import argparse
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

# Paths to directories
base_dir = Path(__file__).resolve().parent.parent
input_dir =  base_dir / 'data' / 'output' / 'ru' / 'srt'
output_dir = base_dir / 'data' / 'output' / 'ru' / 'verbalized'
blocks_per_request = 10  # Number of subtitle blocks to send in one request

# Ensure the output directories exist
os.makedirs(output_dir, exist_ok=True)

# Getting the API key from the file
def get_api_key():
    """Reads the OpenAI API key from a file."""
    with open('api_key.txt', 'r') as f:
        api_key = f.read().strip()
    return api_key
openai.api_key = get_api_key()

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

# Function to interact with OpenAI using the chat-completions API and explain the task of replacing Latin letters and numbers
def use_openai_for_replacements(text_batch):
    # Create instruction for OpenAI
    messages = [
        {"role": "system", "content": "You are a subtitle processing assistant. Your only task is to process subtitles from lectures on mathematics (algebra and geometry) in Russian."},
        {"role": "system", "content": "If the text contains mathematical variables (such as 'x', 'y', 'z', 'π''), replace them with their Russian equivalents ('икс', 'игрек', 'зет', `пи`)."},
        {"role": "system", "content": "If the text contains numbers, replace them with their word equivalents using proper Russian grammar."},
        {"role": "system", "content": "If the text does not contain any mathematical variables or numbers, return the text exactly as it is, without any changes or additional comments."},
        {"role": "system", "content": "Always ensure the correct grammatical case is applied in Russian language, following Russian language rules. For example:"},
        {"role": "system", "content": "'x = 10' should become 'икс = десять', '3,14 первое' should become 'три четырнадцать первое'"},
        {"role": "system", "content": "'5 в степени х should become 'пять в степени икс` and 'NASA' should remain unchanged."},
        {"role": "system", "content": "'икс равен нулю' (not 'икс равен ноль')"},
        {"role": "system", "content": "'cos 2x' should become 'косинус двух икс' (not 'косинус два икс')"},
        {"role": "system", "content": "'sin 3y' should become 'синус трёх игрек' (not 'синус три икс')"},
        {"role": "user", "content": text_batch}
    ]
    
    # Use the ChatCompletion endpoint for the correct model
    response = openai.ChatCompletion.create(
        model="gpt-4o-2024-08-06",
        messages=messages,
        max_tokens=1500,
        temperature=0.3,
    )
    
    # Return the processed text from OpenAI
    return response['choices'][0]['message']['content']

# Function to process a single SRT file using pysrt
def process_srt_file(input_file, output_file):
    subs = pysrt.open(input_file, encoding='utf-8')
    total_subs = len(subs)  # Get the total number of subtitle blocks
    modified_subs = []  # List to store modified subtitles

    # Process subtitles in batches
    for start in range(0, total_subs, blocks_per_request):
        end = min(start + blocks_per_request, total_subs)
        batch = subs[start:end]

        # Concatenate the text of the current batch of subtitles
        batch_text = "\n\n".join([sub.text for sub in batch])
        
        # First, replace numbers with words in the entire batch
        modified_batch_text = replace_numbers(batch_text)
        
        # Then, use OpenAI to intelligently replace Latin variables and adjust grammar
        modified_batch_text = use_openai_for_replacements(modified_batch_text)
        
        # Split the modified text back into individual subtitle blocks
        modified_batch_texts = modified_batch_text.split("\n\n")
        
        # Update each subtitle block with the modified text
        for i, sub in enumerate(batch):
            sub.text = modified_batch_texts[i]
            modified_subs.append(sub)
        
        # Print the progress of processing subtitle blocks in batches
        print(f"Processed subtitle blocks {start + 1} to {end} of {total_subs}...")

    # Save the modified subtitles to the output file
    subs.save(output_file, encoding='utf-8')

# Function to process all SRT files in the specified directory
def process_directory(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.srt'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename.replace('.srt', '_verbalized.srt'))

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
    print(f"All files processed. Results saved to {args.output_dir}")

if __name__ == "__main__":
    main()

logfile.close()  # Close log file

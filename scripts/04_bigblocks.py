# -*- coding: utf-8 -*-
import pysrt
import os
from datetime import timedelta
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
input_dir = base_dir / 'data' / 'output' / 'uk'
output_dir = base_dir / 'data' / 'output' / 'uk'

# Ensure the output directories exist
os.makedirs(output_dir, exist_ok=True)

# Variable to control the number of seconds for word grouping
SECONDS_PER_BLOCK = 21  # You can change this value manually to control block length

def add_time(start_time, delta_ms):
    """Adds milliseconds to a SubRipTime object and returns a new SubRipTime object."""
    total_ms = (start_time.hours * 3600 + start_time.minutes * 60 + start_time.seconds) * 1000 + start_time.milliseconds + delta_ms
    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

def split_subtitle(subtitle, words_per_block):
    """Splits a subtitle block into smaller parts based on the specified word count."""
    words = subtitle.text.split()
    start_time = subtitle.start
    parts = []
    
    # Calculate the duration of each word
    word_duration_ms = subtitle.duration.ordinal / len(words)

    for i in range(0, len(words), words_per_block):
        # Calculate end time for the current block
        end_time = add_time(start_time, word_duration_ms * min(len(words[i:i+words_per_block]), words_per_block))
        part_text = ' '.join(words[i:i+words_per_block])
        parts.append((start_time, end_time, part_text))
        start_time = end_time
    
    return parts

def calculate_words_per_block(subs):
    """Calculates WORDS_PER_BLOCK based on the provided SECONDS_PER_BLOCK."""
    # Find the last time code to determine the total duration
    total_duration_seconds = subs[-1].end.ordinal / 1000.0
    
    # Count the total number of words in the subtitles
    total_words = sum(len(sub.text.split()) for sub in subs)
    
    # Calculate the average time per word
    avg_time_per_word = total_duration_seconds / total_words
    
    # Calculate the number of words that can be spoken in SECONDS_PER_BLOCK seconds
    words_per_block = int(SECONDS_PER_BLOCK / avg_time_per_word)
    
    return words_per_block

def process_srt_file(input_file, output_file):
    """Processes an SRT file, splitting or merging subtitle blocks and saving the result."""
    subs = pysrt.open(input_file)
    
    # Automatically calculate the value of WORDS_PER_BLOCK
    words_per_block = calculate_words_per_block(subs)
    
    new_subs = pysrt.SubRipFile()

    current_block_words = []
    current_block_start = None

    for sub in subs:
        sub_words = sub.text.split()
        
        if current_block_start is None:
            current_block_start = sub.start
        
        current_block_words.extend(sub_words)

        # If current block has reached or exceeded the words_per_block, finalize it
        while len(current_block_words) >= words_per_block:
            # Determine end time for the block
            duration = sub.end.ordinal - current_block_start.ordinal
            word_duration_ms = duration / len(current_block_words)
            end_time = add_time(current_block_start, word_duration_ms * words_per_block)
            
            # Create the new subtitle block
            new_text = ' '.join(current_block_words[:words_per_block])
            new_sub = pysrt.SubRipItem(index=len(new_subs) + 1, start=current_block_start, end=end_time, text=new_text)
            new_subs.append(new_sub)
            
            # Prepare remaining words for next block
            current_block_words = current_block_words[words_per_block:]
            current_block_start = end_time

    # Handle any remaining words in the last block
    if current_block_words:
        new_text = ' '.join(current_block_words)
        new_sub = pysrt.SubRipItem(index=len(new_subs) + 1, start=current_block_start, end=subs[-1].end, text=new_text)
        new_subs.append(new_sub)
    
    new_subs.save(output_file, encoding='utf-8')

# Process all SRT files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith('.srt'):
        input_file = input_dir / filename
        
        # Create the output filename by adding '_bigblocks' before the extension
        output_filename = filename.replace('.srt', '_bigblocks.srt')
        output_file = output_dir / output_filename
        
        print(f"Processing {input_file}...")
        process_srt_file(input_file, output_file)
        print(f"Processed {input_file} -> {output_file}")

logfile.close()  # Close log file
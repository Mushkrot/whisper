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
        {"role": "system", "content": """Вам предоставляется автоматическая транскрипция лекции по математике, содержащая ошибки, допущенные при распознавании речи и математических выражений. Ваша цель — исправить текст, чтобы он стал точным, читабельным и соответствовал оригинальному содержанию лекции, сохранив синхронизацию с видео. Лекция ведется от первого лица женского рода, и это следует учитывать при анализе текста. Тем не менее, род лекторки не должен путать вас с грамматическим родом математических объектов, таких как "треугольник" (мужской род) или "линия" (женский род).

**Инструкции:**

1. **Анализ контекста и точность терминов:**
   - Прочитайте текст целиком, чтобы понять контекст обсуждаемых математических тем.
   - Убедитесь, что все математические термины и понятия используются корректно (например, исправьте "тетрадер" на "тетраэдр").
   - Обратите внимание на правильное написание греческих букв и математических символов (например, "альфа", "пи"). 

2. **Замена математических выражений на текст:**
   - Все математические переменные (например, "x", "y", "z", "π", и греческие буквы) должны быть заменены на их русские эквиваленты (например, "икс", "игрек", "зет", "пи", "альфа"). Следите за правильным грамматическим согласованием в контексте предложения.
   - Если математические переменные или обозначения представлены в виде букв (например, "ABCD"), заменяйте их на кириллические буквы с дефисами (например, "А-Б-Ц-Д").
   - Заменяйте все математические символы и операции (например, "+", "-", "*", "/") на их текстовые эквиваленты в русском языке (например, "плюс", "минус", "умножить", "разделить").
   - Числа в транскрипции также должны быть преобразованы в текст, включая математические выражения (например, "3.14" -> "три целых четырнадцать сотых", "x = 10" -> "икс равно десять").

3. **Исправление чисел и математических выражений:**
   - Проверяйте и корректируйте все числовые значения и математические выражения, учитывая их текстовое представление (например, "пять в степени икс" вместо "5^x").
   - Убедитесь, что дроби и степени переданы верно в текстовом виде (например, "одна вторая" вместо "1/2", "пять в степени икс" вместо "5^x").
   - Применяйте правила написания для сложных чисел и выражений, например, "ноль целых две десятых" вместо "0.2".

4. **Грамматика и синтаксис:**
   - Исправляйте грамматические ошибки: согласование подлежащего и сказуемого, род, число, падеж. Учитывайте, что лекторка говорит от первого лица женского рода (например, "я сказала" вместо "я сказал"), но грамматический род терминов сохраняется (например, "треугольник" остается в мужском роде, "линия" — в женском).
   - Добавляйте недостающие знаки препинания, такие как запятые, точки и тире, чтобы улучшить читабельность текста.
   - Сохраняйте естественность речи лектора, но избегайте разговорных выражений, таких как "ну", "вот", "как бы".

5. **Исправление ошибок распознавания речи:**
   - Исправляйте слова, которые были неправильно распознаны из-за сходства звучания (например, "иррациональные числа" вместо "рациональные числа"). Исходите из контекста, чтобы правильно понять, какое слово использовать.
   - Следите за правильным распознаванием математических терминов и выражений (например, "косинус двух икс" вместо "cos 2x").

6. **Сохранение длины и структуры текста:**
   - Избегайте значительных изменений в длине текста, чтобы субтитры оставались синхронизированными с видео.
   - Сохраняйте структуру предложений и не добавляйте новую информацию, не существующую в оригинальной лекции.

7. **Контекст важнее временных меток:**
   - Игнорируйте time codes в тексте и основывайте свои исправления на содержании лекции, а не на временных метках.
   - Если в тексте пропущены части, восстановите их на основе контекста.

**Примеры исправлений:**

1. **Замена математических выражений:**
   - **Исходный текст:** "5^x"
   - **Исправленный текст:** "пять в степени икс"

2. **Ошибки в математических терминах:**
   - **Исходный текст:** "П-рисно"
   - **Исправленный текст:** "первообразная"

3. **Ошибки в числах:**
   - **Исходный текст:** "триста триста пятьдесят шесть"
   - **Исправленный текст:** "триста пятьдесят шесть"

**Важные указания:**

- **Не изменяйте смысл текста:** Сохраняйте общий смысл и последовательность информации.
- **Используйте контекст и математическую логику:** Исправляйте текст, основываясь на математическом контексте и логике.
- **Синхронизация:** Сохраняйте синхронизацию текста с видеоматериалом, избегая значительных изменений в длине текста.

**Цель:**

Получить точную и читабельную транскрипцию математической лекции, исправив ошибки распознавания, грамматики и математических выражений, сохранив оригинальную структуру текста и синхронизацию с видео.
"""},

        {"role": "system", "content": f"Обработайте следующий текст в соответствии с инструкциями, при этом убедитесь, что все вхождения '{separator}' сохранены в точности такими, какие они есть."},
        {"role": "user", "content": text_batch}
    ]

    # Use the ChatCompletion endpoint
    # New models are "o1-preview" and "o1-mini".
    # gpt-4o-2024-08-06:    approximately   $0.030 per 15 min srt file
    # o1-mini:              approximately   $0.036 per 15 min srt file
    # o1-preview:           approximately   $0.18 per 15 min srt file
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

            print(f"\nProcessing {input_file}...")
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
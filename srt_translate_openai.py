import openai
import pysrt

# Set your OpenAI API key
openai.api_key = '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'

# Function to translate text using OpenAI GPT-4o
def translate_text(text, source_language="ru", target_language="uk"):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": f"You are a translator. Translate the following text from {source_language} to {target_language}."},
                {"role": "user", "content": f"{text}"}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error during translation: {e}")
        return text  # Return the original text in case of an error

# Load the subtitle file
try:
    subs = pysrt.open('11_A6_ru.srt', encoding='utf-8')
except Exception as e:
    print(f"Error loading subtitle file: {e}")
    subs = None

# Translate subtitles
if subs:
    for sub in subs:
        translated_text = translate_text(sub.text, source_language="ru", target_language="uk")
        sub.text = translated_text  # Replace the original text with the translated text

    # Save the translated file while preserving the timestamps
    try:
        subs.save('translated_openai.srt', encoding='utf-8')
    except Exception as e:
        print(f"Error saving subtitle file: {e}")

import os
import glob
import requests
import time
import re
import logging
from typing import List, Tuple, Dict

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subtitles_translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SEPARATOR_TEMPLATE = "␞{}"
MAX_CHUNK_SIZE = 1900
API_URL = "https://api.deepseek.com/v1/chat/completions"
SETTINGS_FILE = 'settings.txt'

def create_default_settings():
    """Create default settings file"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write('time_shift=0.0\n')
        f.write('target_language=English\n')
        f.write('api_key=\n')

def read_settings() -> Dict:
    """Read settings from file"""
    settings = {'time_shift': 0.0, 'target_language': 'English', 'api_key': ''}
    if not os.path.exists(SETTINGS_FILE):
        create_default_settings()
    else:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'time_shift':
                        settings[key] = float(value)
                    else:
                        settings[key] = value
    return settings

def write_settings(settings: Dict):
    """Save settings to file"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write(f'time_shift={settings["time_shift"]}\n')
        f.write(f'target_language={settings["target_language"]}\n')
        f.write(f'api_key={settings["api_key"]}\n')

def configure_settings(settings: Dict):
    """Settings menu"""
    while True:
        print("\nSettings:")
        print(f"1. Time shift (current: {settings['time_shift']} sec)")
        print(f"2. Target language (current: '{settings['target_language']}')")
        print(f"3. API key (current status: {'set' if settings['api_key'] else 'not set'})")
        print("4. Start")
        choice = input("Select option: ").strip()
        
        if choice == '1':
            while True:
                user_input = input("Enter time shift in seconds (decimal with dot, negative for backward shift): ")\
                              .replace(',', '.').strip()
                try:
                    shift = float(user_input)
                    settings['time_shift'] = shift
                    write_settings(settings)
                    print("Time shift updated")
                    break
                except ValueError:
                    print("Invalid number format. Use 123.45 format")
        
        elif choice == '2':
            lang = input("Enter target language (e.g. 'English', 'Spanish' or 'none'): ").strip()
            settings['target_language'] = lang
            write_settings(settings)
            print("Translation language updated")
        
        elif choice == '3':
            api_key = input("Enter new API key: ").strip()
            settings['api_key'] = api_key
            write_settings(settings)
            print("API key updated")
        
        elif choice == '4':
            break
        
        else:
            print("Invalid choice. Try again.")

def get_api_key(settings: Dict) -> str:
    """Get API key from environment or settings"""
    api_key = os.getenv("DEEPSEEK_API_KEY") or settings['api_key']
    
    if not api_key:
        print("\nAPI key not found!")
        api_key = input("Enter your Deepseek API key: ").strip()
        settings['api_key'] = api_key
        write_settings(settings)
        print("API key saved in settings")
    
    return api_key

def parse_time(time_str: str) -> float:
    """Parse time string to seconds"""
    time_parts = re.split(r'[:,]', time_str)
    if len(time_parts) != 4:
        return 0.0
    
    try:
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2])
        milliseconds = int(time_parts[3])
        return hours*3600 + minutes*60 + seconds + milliseconds/1000
    except ValueError:
        return 0.0

def format_time(seconds: float) -> str:
    """Format seconds to SRT timecode"""
    hours = int(seconds // 3600)
    remainder = seconds % 3600
    minutes = int(remainder // 60)
    seconds = remainder % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def adjust_timecode(timecode: str, shift: float) -> str:
    """Adjust timecode with shift"""
    try:
        start_end = timecode.split(' --> ')
        if len(start_end) != 2:
            return timecode
        
        start = parse_time(start_end[0].strip()) + shift
        end = parse_time(start_end[1].strip()) + shift
        
        start = max(start, 0.0)
        end = max(end, 0.0)
        
        return f"{format_time(start)} --> {format_time(end)}"
    except Exception as e:
        print(f"Time processing error: {str(e)}")
        return timecode

def parse_srt(content: str) -> Tuple[List[str], List[str]]:
    """Parse SRT content"""
    blocks = content.strip().split('\n\n')
    timecodes = []
    subtitles = []
    
    for block in blocks:
        lines = [line.strip() for line in block.split('\n')]
        if len(lines) >= 3:
            timecode = lines[1]
            text = ' '.join(lines[2:])
            text = re.sub(r'\s+', ' ', text).strip()
            timecodes.append(timecode)
            subtitles.append(text)
    
    return timecodes, subtitles

def translate_text(text: str, settings: Dict) -> str:
    """Translate text using Deepseek API"""
    headers = {
        "Authorization": f"Bearer {get_api_key(settings)}",
        "Content-Type": "application/json"
    }
    
    system_prompt = {
        "role": "system",
        "content": f"""Perform a literary translation to {settings['target_language']} strictly following these rules:
1. Keep all ␞N separators in original positions
2. Don't add new separators
3. Maintain text structure
4. Preserve original style
5. Keep HTML tags unchanged. While translating the text inside the tags, translate it as if the tags do not exist, i.e., in the context of the surrounding text.
6. Don't translate Latin words"""
    }
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [system_prompt, {"role": "user", "content": text}],
                "temperature": 0.3
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        raise Exception(f"API error: {str(e)}")

def process_file(filename: str, settings: Dict):
    """Process subtitle file"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    timecodes, subtitles = parse_srt(content)
    if not subtitles:
        print(f"No subtitles found in {filename}")
        return
    
    print(f"\nProcessing file: {filename}")
    print(f"Subtitles found: {len(subtitles)}")
    
    if settings['time_shift'] != 0:
        print(f"Applying time shift: {settings['time_shift']} sec")
        timecodes = [adjust_timecode(tc, settings['time_shift']) for tc in timecodes]
    
    if settings['target_language'].lower() != 'none':
        joined_text = ''.join(f"{sub}{SEPARATOR_TEMPLATE.format(i)}" for i, sub in enumerate(subtitles, 1))
        
        protected_text = re.sub(
            r'(␞\d+|</?i>)', 
            lambda m: f"[[PROTECT:{m.group()}]]", 
            joined_text
        )
        
        sentences = re.split(r'(?<=[.!?])\s+|(?=\[\[PROTECT:)', protected_text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.replace("[[PROTECT:", "").replace("]]", "")
            sentence_length = len(sentence)
            
            if current_length + sentence_length > MAX_CHUNK_SIZE and current_chunk:
                chunks.append(''.join(current_chunk))
                current_chunk = []
                current_length = 0
                
            current_chunk.append(sentence)
            current_length += sentence_length
        
        if current_chunk:
            chunks.append(''.join(current_chunk))
        
        translated_chunks = []
        try:
            for i, chunk in enumerate(chunks, 1):
                print(f"Translating chunk {i}/{len(chunks)}")
                translated = translate_text(chunk, settings)
                translated_chunks.append(translated)
                time.sleep(1)
            
            full_translated = ''.join(translated_chunks)
            translated_subtitles = []
            pattern = re.compile(r'␞(\d+)')
            indexes = {int(m.group(1)): m.start() for m in pattern.finditer(full_translated)}
            indexes[len(subtitles)] = len(full_translated)
            
            last_pos = 0
            for i in range(1, len(subtitles)+1):
                if i in indexes:
                    text = re.sub(r'␞\d+', '', full_translated[last_pos:indexes[i]]).strip()
                    translated_subtitles.append(text)
                    last_pos = indexes[i]
                else:
                    translated_subtitles.append(subtitles[i-1])
            
            translated_subtitles = translated_subtitles[:len(subtitles)]
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return
    else:
        translated_subtitles = subtitles
    
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (timecode, text) in enumerate(zip(timecodes, translated_subtitles), 1):
            f.write(f"{i}\n{timecode}\n{text}\n\n")
    
    print(f"File saved: {output_file}\n")

def main():
    """Main function"""
    settings = read_settings()
    
    try:
        api_key = get_api_key(settings)
        if not api_key:
            print("Failed to get API key")
            return
    except Exception as e:
        print(f"Critical error: {str(e)}")
        return
    
    srt_files = glob.glob('*.srt')
    print(f"\nFound SRT files: {len(srt_files)}")
    
    if not srt_files:
        print("No files to process")
        return
    
    print("\nCurrent settings:")
    print(f"Time shift: {settings['time_shift']} sec")
    print(f"Target language: {settings['target_language']}")
    print(f"API key: {'set' if settings['api_key'] else 'not set'}")
    
    choice = input("\nPress Enter to start processing or enter 1 for settings: ").strip()
    if choice == '1':
        configure_settings(settings)
        print("\nStarting processing...")
    else:
        print("\nStarting processing...")
    
    for filename in srt_files:
        try:
            process_file(filename, settings)
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    main()
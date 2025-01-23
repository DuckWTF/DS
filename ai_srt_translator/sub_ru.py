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
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write('time_shift=0.0\n')
        f.write('target_language=русский\n')
        f.write('api_key=\n')

def read_settings() -> Dict:
    settings = {'time_shift': 0.0, 'target_language': 'русский', 'api_key': ''}
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
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write(f'time_shift={settings["time_shift"]}\n')
        f.write(f'target_language={settings["target_language"]}\n')
        f.write(f'api_key={settings["api_key"]}\n')

def configure_settings(settings: Dict):
    while True:
        print("\nНастройки:")
        print(f"1. Сдвиг времени (текущее значение: {settings['time_shift']} сек)")
        print(f"2. Язык перевода (текущий: '{settings['target_language']}')")
        print(f"3. API ключ (текущий статус: {'установлен' if settings['api_key'] else 'не установлен'})")
        print("4. Начать")
        choice = input("Выберите опцию: ").strip()
        
        if choice == '1':
            while True:
                user_input = input("Введите время сдвига в секундах (дробное через точку, отрицательное для сдвига назад): ")\
                              .replace(',', '.').strip()
                try:
                    shift = float(user_input)
                    settings['time_shift'] = shift
                    write_settings(settings)
                    print("Сдвиг времени обновлен")
                    break
                except ValueError:
                    print("Некорректный формат числа. Используйте формат 123.45")
        
        elif choice == '2':
            lang = input("Введите язык для перевода (например 'русский', 'английский' или 'none'): ").strip()
            settings['target_language'] = lang
            write_settings(settings)
            print("Язык перевода обновлен")
        
        elif choice == '3':
            api_key = input("Введите новый API ключ: ").strip()
            settings['api_key'] = api_key
            write_settings(settings)
            print("API ключ обновлен")
        
        elif choice == '4':
            break
        
        else:
            print("Неверный выбор. Попробуйте снова.")

def get_api_key(settings: Dict) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY") or settings['api_key']
    
    if not api_key:
        print("\nAPI ключ не найден!")
        api_key = input("Введите ваш API ключ для Deepseek: ").strip()
        settings['api_key'] = api_key
        write_settings(settings)
        print("API ключ сохранен в настройки")
    
    return api_key

def parse_time(time_str: str) -> float:
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
    hours = int(seconds // 3600)
    remainder = seconds % 3600
    minutes = int(remainder // 60)
    seconds = remainder % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def adjust_timecode(timecode: str, shift: float) -> str:
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
        print(f"Ошибка обработки времени: {str(e)}")
        return timecode

def parse_srt(content: str) -> Tuple[List[str], List[str]]:
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
    headers = {
        "Authorization": f"Bearer {get_api_key(settings)}",
        "Content-Type": "application/json"
    }
    
    system_prompt = {
        "role": "system",
        "content": f"""Выполни литературный перевод на {settings['target_language']} строго соблюдая правила:
1. Все разделители вида ␞N должны оставаться в соответствующих местах
2. Не добавляй новые разделители
3. Сохраняй структуру текста
4. Сохраняй стиль оригинала
5. Не изменяй HTML-теги. При этом текст внутри тегов переводи так, будто этих тегов нет т.е. с контекстом остального текста.
6. Не переводи латынь"""
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
        raise Exception(f"Ошибка API: {str(e)}")

def process_file(filename: str, settings: Dict):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    timecodes, subtitles = parse_srt(content)
    if not subtitles:
        print(f"Файл {filename} не содержит субтитров")
        return
    
    print(f"\nОбработка файла: {filename}")
    print(f"Найдено субтитров: {len(subtitles)}")
    
    if settings['time_shift'] != 0:
        print(f"Применение сдвига времени: {settings['time_shift']} сек")
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
                print(f"Перевод блока {i}/{len(chunks)}")
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
            print(f"Ошибка перевода: {str(e)}")
            return
    else:
        translated_subtitles = subtitles
    
    output_dir =  'output'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, filename)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (timecode, text) in enumerate(zip(timecodes, translated_subtitles), 1):
            f.write(f"{i}\n{timecode}\n{text}\n\n")
    
    print(f"Результат сохранен: {output_file}\n")

def main():
    settings = read_settings()
    
    try:
        api_key = get_api_key(settings)
        if not api_key:
            print("Не удалось получить API ключ")
            return
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
        return
    
    srt_files = glob.glob('*.srt')
    print(f"\nНайдено SRT-файлов: {len(srt_files)}")
    
    if not srt_files:
        print("Нет файлов для обработки")
        return
    
    print("\nТекущие настройки:")
    print(f"Сдвиг времени: {settings['time_shift']} сек")
    print(f"Язык перевода: {settings['target_language']}")
    print(f"API ключ: {'установлен' if settings['api_key'] else 'отсутствует'}")
    
    choice = input("\nНажмите Enter для начала обработки или введите 1 для настройки: ").strip()
    if choice == '1':
        configure_settings(settings)
        print("\nЗапуск обработки...")
    else:
        print("\nЗапуск обработки...")
    
    for filename in srt_files:
        try:
            process_file(filename, settings)
        except Exception as e:
            print(f"Ошибка обработки файла {filename}: {str(e)}")

if __name__ == "__main__":
    main()
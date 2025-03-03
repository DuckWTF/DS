import glob
from typing import List, Tuple, Dict, Optional, Set
import logging
import time
import requests
import json
import re
import os
import random

logging.basicConfig(
    level=logging.INFO , # <---- Измените на DEBUG
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subtitles_translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)




MAX_CHUNK_SIZE = 0
BASE_DELAY = 3
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent" 
SETTINGS_FILE = 'settings.txt'

class ChunkInfo:
    def __init__(self, indices: List[int], content: str):
        self.indices = indices
        self.content = content
        self.size = len(content.encode('utf-8'))

def create_default_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write('time_shift=0.0\n')
        f.write('target_language=русский\n')
        f.write('api_provider=gemini\n')
        f.write('deepseek_api_key=\n')
        f.write('gemini_api_key=\n')
        f.write('gemini_model=gemini-2.0-flash-thinking-exp-01-21\n')
        f.write('deepseek_model=deepseek-chat\n')  
        f.write('chunk_size=0\n')
        f.write('max_retries=10\n')
        f.write('timeout=360\n')  

def read_settings() -> Dict:
    settings = {
        'time_shift': 0.0,
        'target_language': 'русский',
        'api_provider': 'gemini',
        'deepseek_api_key': '',
        'gemini_api_key': '',
        'gemini_model': 'gemini-2.0-flash-thinking-exp-01-21',
        'deepseek_model': 'deepseek-chat',  
        'chunk_size': 0,
        'max_retries': 10,
        'timeout': 360  # <-- Значение по умолчанию
    }
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
                    elif key == 'max_retries':
                        settings[key] = int(value)
                    elif key == 'chunk_size':
                        settings[key] = int(value)
                    elif key == 'timeout':
                        settings[key] = int(value)
                    else:
                        settings[key] = value
    # Гарантируем, что api_provider есть в settings, даже если не было в файле
    if 'api_provider' not in settings:
        settings['api_provider'] = 'deepseek'
    return settings

def write_settings(settings: Dict):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.write(f"time_shift={settings['time_shift']}\n")
        f.write(f"target_language={settings['target_language']}\n")
        f.write(f"api_provider={settings['api_provider']}\n")
        f.write(f"deepseek_api_key={settings['deepseek_api_key']}\n")
        f.write(f"gemini_api_key={settings['gemini_api_key']}\n")
        f.write(f"gemini_model={settings['gemini_model']}\n")
        f.write(f"deepseek_model={settings['deepseek_model']}\n")  # <-- Запись настроек модели DeepSeek
        f.write(f"chunk_size={settings['chunk_size']}\n")
        f.write(f"max_retries={settings['max_retries']}\n")
        f.write(f"timeout={settings['timeout']}\n")  # <-- Запись таймаута

def configure_settings(settings: Dict):
    while True:
        print("\nНастройки:")
        print(f"1. Сдвиг времени (текущее: {settings['time_shift']} сек)")
        print(f"2. Язык перевода (текущий: '{settings['target_language']}')")
        print(f"3. Провайдер API (текущий: '{settings['api_provider']}')")

        next_option = 4

        if settings['api_provider'] == 'gemini':
            api_key_status = 'установлен' if settings['gemini_api_key'] else 'отсутствует'
            print(f"{next_option}. API ключ Gemini (статус: {api_key_status})")
            option_number_gemini_key = next_option
            next_option += 1
            print(f"{next_option}. Модель Gemini (текущая: '{settings['gemini_model']}')")
            option_number_gemini_model = next_option
            next_option += 1

        elif settings['api_provider'] == 'deepseek':
            api_key_status = 'установлен' if settings['deepseek_api_key'] else 'отсутствует'
            print(f"{next_option}. API ключ DeepSeek (статус: {api_key_status})")
            option_number_deepseek_key = next_option
            next_option += 1
            print(f"{next_option}. Модель DeepSeek (текущая: '{settings['deepseek_model']}')")
            option_number_deepseek_model = next_option
            next_option += 1

        else:
            print(f"{next_option}. API ключ (неизвестный провайдер)")
            option_number_unknown_provider_key = next_option
            next_option += 1

        print(f"{next_option}. Размер блока (текущий: {settings['chunk_size']} символов, 0 - отключено)")
        option_number_chunk_size = next_option
        next_option += 1

        print(f"{next_option}. Повторные попытки (текущие: {settings['max_retries']})")
        option_number_retries = next_option
        next_option += 1

        print(f"{next_option}. Таймаут (текущий: {settings['timeout']} c)")
        option_number_timeout = next_option
        next_option += 1

        print(f"{next_option}. Начать обработку")
        option_number_start = next_option

        choice = input("Выберите опцию: ").strip()

        if choice == '1':
            while True:
                user_input = input("Введите сдвиг времени (секунды с точкой): ").replace(',', '.').strip()
                try:
                    settings['time_shift'] = float(user_input)
                    write_settings(settings)
                    print("Сдвиг обновлен")
                    break
                except ValueError:
                    print("Ошибка формата числа!")
            continue

        elif choice == '2':
            lang = input("Введите язык перевода (например 'russian' или 'none'): ").strip()
            settings['target_language'] = lang
            write_settings(settings)
            print("Язык обновлен")
            continue

        elif choice == '3':
            while True:
                print("   Выберите провайдера:")
                print("   1 - Gemini")
                print("   2 - DeepSeek")
                provider_choice = input("Выберите провайдера API (1 или 2): ").strip()
                if provider_choice == '1':
                    settings['api_provider'] = 'gemini'
                    write_settings(settings)
                    print("Провайдер API изменен на 'gemini'")
                    break
                elif provider_choice == '2':
                    settings['api_provider'] = 'deepseek'
                    write_settings(settings)
                    print("Провайдер API изменен на 'deepseek'")
                    break
                else:
                    print("Неверный выбор. Введите 1 или 2.")
            continue

        # --- БЛОК Gemini ---
        elif settings['api_provider'] == 'gemini' and choice.isdigit():
            numeric_choice = int(choice)

            if numeric_choice == option_number_gemini_key:
                api_key = input("Введите новый API ключ Gemini: ").strip()
                settings['gemini_api_key'] = api_key
                write_settings(settings)
                print("Ключ API обновлен")
                continue

            elif numeric_choice == option_number_gemini_model:
                while True:
                    print("   Выберите модель Gemini:")
                    print("   1 - Gemini 2.0 Flash (gemini-2.0-flash)")
                    print("   2 - Gemini 2.0 Flash-Lite (gemini-2.0-flash-lite-preview-02-05)")
                    print("   3 - Gemini 1.5 Flash (gemini-1.5-flash)")
                    print("   4 - Gemini 1.5 Flash-8B (gemini-1.5-flash-8b)")
                    print("   5 - Gemini 1.5 Pro (gemini-1.5-pro)")
                    print("   6 - Gemini 2.0 Pro Exp (gemini-2.0-pro-exp-02-05)")
                    print("   7 - Gemini 2.0 Flash Thinking Exp (gemini-2.0-flash-thinking-exp-01-21)")
                    model_choice = input("Выберите номер модели Gemini: ").strip()

                    if model_choice == '1':
                        settings['gemini_model'] = 'gemini-2.0-flash'
                    elif model_choice == '2':
                        settings['gemini_model'] = 'gemini-2.0-flash-lite-preview-02-05'
                    elif model_choice == '3':
                        settings['gemini_model'] = 'gemini-1.5-flash'
                    elif model_choice == '4':
                        settings['gemini_model'] = 'gemini-1.5-flash-8b'
                    elif model_choice == '5':
                        settings['gemini_model'] = 'gemini-1.5-pro'
                    elif model_choice == '6':
                        settings['gemini_model'] = 'gemini-2.0-pro-exp-02-05'
                    elif model_choice == '7':
                        settings['gemini_model'] = 'gemini-2.0-flash-thinking-exp-01-21'
                    else:
                        print("Неверный выбор модели.")
                        continue

                    write_settings(settings)
                    print(f"Модель Gemini изменена на '{settings['gemini_model']}'")
                    break
                continue

        # --- БЛОК DeepSeek ---
        elif settings['api_provider'] == 'deepseek' and choice.isdigit():
            numeric_choice = int(choice)

            if numeric_choice == option_number_deepseek_key:
                api_key = input("Введите новый API ключ DeepSeek: ").strip()
                settings['deepseek_api_key'] = api_key
                write_settings(settings)
                print("Ключ API обновлен")
                continue

            elif numeric_choice == option_number_deepseek_model:
                while True:
                    print("   Выберите модель DeepSeek:")
                    print("   1 - deepseek-chat (64K контекст, 8K выход)")
                    print("   2 - deepseek-reasoner (64K контекст, 8K выход, CoT до 32K)")
                    model_choice = input("Выберите номер модели DeepSeek: ").strip()

                    if model_choice == '1':
                        settings['deepseek_model'] = 'deepseek-chat'
                    elif model_choice == '2':
                        settings['deepseek_model'] = 'deepseek-reasoner'
                    else:
                        print("Неверный выбор модели.")
                        continue

                    write_settings(settings)
                    print(f"Модель DeepSeek изменена на '{settings['deepseek_model']}'")
                    break
                continue

        # --- Прочие опции ---
        if choice.isdigit():
            numeric_choice = int(choice)

            # Размер блока
            if numeric_choice == option_number_chunk_size:
                while True:
                    user_input = input("Введите новый размер блока (0-1000000, 0 - отключить): ").strip()
                    try:
                        chunk_size = int(user_input)
                        if 0 <= chunk_size <= 1000000:
                            settings['chunk_size'] = chunk_size
                            write_settings(settings)
                            print("Размер блока обновлен")
                            break
                        else:
                            print(f"Недопустимое значение. Введите число от 0 до 1000000")
                    except ValueError:
                        print("Ошибка формата числа!")
                continue

            # Повторные попытки
            elif numeric_choice == option_number_retries:
                while True:
                    try:
                        retries = int(input("Введите количество повторных попыток (0-1000): "))
                        if 0 <= retries <= 1000:
                            settings['max_retries'] = retries
                            write_settings(settings)
                            print("Значение обновлено")
                            break
                        else:
                            print(f"Недопустимое значение. Введите число от 0 до 1000")
                    except ValueError:
                        print("Введите целое число")
                continue

            # Таймаут
            elif numeric_choice == option_number_timeout:
                while True:
                    try:
                        new_timeout = int(input("Введите таймаут в секундах (0-3600): "))
                        if 0 <= new_timeout <= 3600:
                            settings['timeout'] = new_timeout
                            write_settings(settings)
                            print("Таймаут обновлён.")
                            break
                        else:
                            print("Недопустимое значение. Введите число от 0 до 3600.")
                    except ValueError:
                        print("Введите целое число.")
                continue

            # Начать обработку
            elif numeric_choice == option_number_start:
                break

        print("Неверный выбор")

def get_api_key(settings: Dict) -> Optional[str]:
    api_provider = settings['api_provider']
    api_key = None

    if api_provider == 'deepseek':
        api_key = os.getenv("DEEPSEEK_API_KEY") or settings['deepseek_api_key']
        env_var_name = "DEEPSEEK_API_KEY"
        setting_name = "deepseek_api_key"
    elif api_provider == 'gemini':
        api_key = os.getenv("GEMINI_API_KEY") or settings['gemini_api_key']
        env_var_name = "GEMINI_API_KEY"
        setting_name = "gemini_api_key"
    else:
        logger.error(f"Неизвестный провайдер API: {api_provider}")
        return None

    if not api_key:
        print(f"\nAPI ключ {api_provider} не найден!")
        api_key = input(f"Введите ваш API ключ {api_provider}: ").strip()
        settings[setting_name] = api_key
        write_settings(settings)
    return api_key

def parse_time(time_str: str) -> float:
    parts = re.split(r'[:,]', time_str)
    try:
        return sum([
            int(parts[0]) * 3600,
            int(parts[1]) * 60,
            int(parts[2]),
            int(parts[3])/1000
        ])
    except (IndexError, ValueError):
        return 0.0

def parse_time_ass(time_str: str) -> float:
    """
    Преобразует время из формата ASS (h:mm:ss.cs) в секунды (float).

    Пример входа: "0:01:02.50"
    Выход: 62.50 (float)
    """
    # Формат: ЧАСЫ:МИНУТЫ:СЕКУНДЫ.ЦЕНТИСЕКУНДЫ (или миллисекунды, зависит от софта)
    # Часто указывают 2 знака после точки (сотые секунды), но бывает 3 знака (миллисекунды).
    # Разберём общее с плавающей точкой.
    try:
        parts = time_str.split(':')  # [часы, минуты, "секунды.доли"]
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_fraction = float(parts[2])  # секунды + десятичная часть
        return hours * 3600 + minutes * 60 + sec_fraction
    except Exception:
        # Если парсинг не удался, вернём 0
        return 0.0

def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    remainder = seconds % 3600
    minutes = int(remainder // 60)
    seconds = remainder % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

def format_time_ass(seconds: float) -> str:
    """
    Форматирует время (float, сек) в строку формата ASS (h:mm:ss.cs).

    Пример входа: 62.50
    Выход: "0:01:02.50"
    """
    # Ограничимся двумя знаками после десятичной точки для совместимости
    # (многие редакторы .ass используют сотые доли секунды).
    hours = int(seconds // 3600)
    remainder = seconds % 3600
    minutes = int(remainder // 60)
    sec_fraction = remainder % 60  # это секунды с плавающей точкой
    return f"{hours}:{minutes:02}:{sec_fraction:05.2f}"

def adjust_timecode(timecode: str, shift: float) -> str:
    try:
        start, end = timecode.split(' --> ')
        start_sec = parse_time(start) + shift
        end_sec = parse_time(end) + shift
        return (
            f"{format_time(max(start_sec, 0))} --> "
            f"{format_time(max(end_sec, 0))}"
        )
    except Exception as e:
        logger.error(f"Ошибка коррекции времени: {str(e)}")
        return timecode

def adjust_timecode_ass(dialogues, shift: float):
    """
    Применяет сдвиг времени (shift в секундах) ко всем репликам в списке dialogues.
    dialogues - это список словарей, у каждого есть 'start' и 'end' (float).

    В результате меняет поля 'start' и 'end' на скорректированные значения (не меньше 0).
    """
    for d in dialogues:
        new_start = d['start'] + shift
        new_end = d['end'] + shift
        if new_start < 0:
            new_start = 0.0
        if new_end < 0:
            new_end = 0.0
        d['start'] = new_start
        d['end'] = new_end

def parse_srt(content: str) -> Tuple[List[str], List[str]]:
    blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
    timecodes = []
    subtitles = []

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            timecodes.append(lines[1])
            subtitles.append('\n'.join(lines[2:]).rstrip())

    return timecodes, subtitles

def parse_ass(content: str):
    """
    Разбирает содержимое .ass-файла, возвращая:
      - header_lines: все строки заголовка (до [Events], включая сам блок Script Info и т.д.)
      - events_format_line: строку 'Format:...' (если есть) из секции [Events]
      - dialogues: список словарей, где каждый словарь описывает строку субтитров:
          {
            'layer': str,
            'start': float,
            'end': float,
            'style': str,
            'name': str,
            'margin_l': str,
            'margin_r': str,
            'margin_v': str,
            'effect': str,
            'text': str
          }
      - timecodes: список строк вида "start --> end" (аналогично SRT), чтобы переиспользовать логику chunk'ов.
      - subtitles: список только текстов (по тому же индексу, что и timecodes).
    
    Пример формата диалога:
      Dialogue: 0,0:01:02.50,0:01:05.00,Default,Nobody,0,0,0,,Это текст
    
    Порядок полей после 'Dialogue:' совпадает с:
      Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    """
    lines = content.split('\n')
    header_lines = []
    events_format_line = ""
    dialogues = []

    in_events_section = False
    timecodes = []
    subtitles = []

    for line in lines:
        stripped = line.strip()
        if not in_events_section:
            # Ищем блок [Events]
            header_lines.append(line)  # Пишем в header всё, что до [Events] (включая саму строку)
            if stripped.lower() == '[events]':
                in_events_section = True
            continue

        # Уже в блоке [Events]
        if stripped.lower().startswith('format:'):
            # Формат описания полей
            events_format_line = line
            continue

        if stripped.lower().startswith('dialogue:'):
            # Парсим строку субтитров
            # Диалог формата: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            # Разделим с помощью split(',', 9), чтобы не "порезать" текст
            parts = line.split(':', 1)  # ["Dialogue", " Layer,0:...,Text"]
            dialogue_data = parts[1].strip()
            fields = dialogue_data.split(',', 9)  # максимум 10 полей

            if len(fields) < 10:
                # Неверная структура
                continue

            layer_str = fields[0].strip()
            start_str = fields[1].strip()
            end_str = fields[2].strip()
            style_str = fields[3].strip()
            name_str = fields[4].strip()
            margin_l_str = fields[5].strip()
            margin_r_str = fields[6].strip()
            margin_v_str = fields[7].strip()
            effect_str = fields[8].strip()
            text_str = fields[9]

            start_sec = parse_time_ass(start_str)
            end_sec = parse_time_ass(end_str)

            dialogues.append({
                'layer': layer_str,
                'start': start_sec,
                'end': end_sec,
                'style': style_str,
                'name': name_str,
                'margin_l': margin_l_str,
                'margin_r': margin_r_str,
                'margin_v': margin_v_str,
                'effect': effect_str,
                'text': text_str
            })

            # Для дальнейшей логики переводов делаем аналог SRT-структуры
            # timecodes[i], subtitles[i]
            srt_style_timecode = f"{format_time_ass(start_sec)} --> {format_time_ass(end_sec)}"
            timecodes.append(srt_style_timecode)
            subtitles.append(text_str)

        else:
            # Это может быть "Comment:" или что-то ещё. Сохраним как есть в header_lines
            # Или, при желании, можно обрабатывать Comment: ... так же.
            header_lines.append(line)

    return header_lines, events_format_line, dialogues, timecodes, subtitles

def reconstruct_ass(header_lines: list,
                    events_format_line: str,
                    dialogues: list,
                    translated_subs: list) -> str:
    """
    Пересобирает итоговый текст .ass на основе:
      - header_lines (всё, что было до и внутри [Events], но без 'Dialogue:' строк),
      - events_format_line (строка 'Format: ...'),
      - dialogues (список словарей с ключами: start, end, layer, style, name, margin_l, margin_r, margin_v, effect),
      - translated_subs (список итоговых переведённых текстов той же длины, что и dialogues).

    Возвращает финальную строку .ass для записи в файл.
    """
    output_lines = []
    # Сначала добавляем все строки заголовка
    for hl in header_lines:
        output_lines.append(hl)

    # Если есть строка формата, добавляем её
    if events_format_line:
        output_lines.append(events_format_line)

    # Затем добавляем строки диалогов с переведённым текстом
    for i, d in enumerate(dialogues):
        start_str = format_time_ass(d['start'])
        end_str = format_time_ass(d['end'])
        text_str = translated_subs[i]  # перевод либо оригинал, если пропущен

        # Собираем поля согласно формату: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        line_fields = [
            d['layer'],
            start_str,
            end_str,
            d['style'],
            d['name'],
            d['margin_l'],
            d['margin_r'],
            d['margin_v'],
            d['effect'],
            text_str
        ]
        dialogue_str = "Dialogue: " + ",".join(line_fields)
        output_lines.append(dialogue_str)

    # Возвращаем итоговый текст, объединённый переводами
    return "\n".join(output_lines) + "\n"

def translate_chunk(chunk: ChunkInfo, 
                    settings: Dict, 
                    subtitles: List[str], 
                    translated_subs: List[str],
                    attempt_type: str = "initial") -> Set[int]:
    """
    Переводит блок субтитров. При любом несоответствии индексов
    оставшиеся строки этого блока помечаются как "пропущенные".
    """

    failed_indices = set()
    instruction_prefixes = ("Важно:", "Инструкция:", "Note:", "Important:")

    try:
        translated_text = translate_text(chunk.content, settings)
        if translated_text is None:
            # API вернул None (например, заблокировано policy)
            # Все строки блока помечаем как неудачные
            failed_indices.update(chunk.indices)
            return failed_indices

        translated_blocks = translated_text.strip().split('\n\n')
        processed_indices = set()

        # Подготовка итератора по индексам исходных строк
        chunk_indices_iter = iter(chunk.indices)
        original_idx = next(chunk_indices_iter, None)

        tb_index = 0  # индекс по блокам перевода

        while tb_index < len(translated_blocks) and original_idx is not None:
            block = translated_blocks[tb_index].strip()
            if not block:
                # Пустой блок перевода, пропускаем
                tb_index += 1
                continue

            lines_in_block = block.split('\n')
            first_line = lines_in_block[0].strip()

            # 1) Проверка: нецифровая первая строка => инструкция или "мусор"
            if not first_line.isdigit():
                # Проверка на возможные инструкционные префиксы
                if any(first_line.startswith(pref) for pref in instruction_prefixes):
                    # Это не субтитр, а явно служебная инструкция от модели
                    tb_index += 1
                    continue
                else:
                    # Если это не инструкция и не номер, 
                    # то целиком воспринимаем как перевод для текущего original_idx
                    translated_subs[original_idx] = block
                    processed_indices.add(original_idx)
                    original_idx = next(chunk_indices_iter, None)
                    tb_index += 1
                    continue

            # Если строка – это цифра, пытаемся сопоставить индексы
            try:
                translated_idx_from_block = int(first_line) - 1
            except ValueError:
                # Теоретически не должно произойти, но на всякий случай
                # Если не удаётся преобразовать – считаем это ошибкой индекса
                # и помечаем оставшиеся строки
                tail_index_pos = chunk.indices.index(original_idx)
                missed_lines = chunk.indices[tail_index_pos:]
                failed_indices.update(missed_lines)
                return failed_indices

            # 2) Сравнение индексов
            if translated_idx_from_block == original_idx:
                # Совпадение – берём перевод (без первой строки)
                translated_text_block = '\n'.join(lines_in_block[1:])
                translated_subs[original_idx] = translated_text_block
                processed_indices.add(original_idx)

                original_idx = next(chunk_indices_iter, None)
                tb_index += 1

            else:
                # Любое несоответствие -> «ошибка индекса»
                # Нужно добавить в пропущенные ВСЕ оставшиеся строки
                tail_index_pos = chunk.indices.index(original_idx)
                missed_lines = chunk.indices[tail_index_pos:]
                failed_indices.update(missed_lines)
                return failed_indices

        # Если в конце цикла остались оригинальные индексы,
        # значит их не перевели – тоже помечаем как пропущенные
        while original_idx is not None:
            failed_indices.add(original_idx)
            original_idx = next(chunk_indices_iter, None)

    except Exception as e:
        # Любая ошибка – все строки блока идут в пропущенные
        failed_indices.update(chunk.indices)
        logger.error(f"Ошибка перевода блока ({attempt_type}): {str(e)}")
        logger.exception("Детали ошибки:")

    return failed_indices

def translate_text_deepseek(text: str, settings: Dict) -> Optional[str]:
    api_key = get_api_key(settings)
    if not api_key:
        return None  # Нет API ключа – выходим

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Используем из настроек выбранную модель (deepseek-chat или deepseek-reasoner)
    chosen_model = settings.get('deepseek_model', 'deepseek-chat')

    data = {
        "model": chosen_model,  # <-- Берём название модели из настроек
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Выполните литературный перевод на {settings['target_language']} строго соблюдая:\n"
                        "1. Сохраняй исходные номера строк без изменений\n"
                        "2. Не меняй структуру блоков и порядок строк\n"
                        "3. Первая строка блока - всегда только номер\n"
                        "4. Не добавляй новые строки и символы\n"
                        "5. Специальные конструкции (например, ♪) сохраняй как есть\n"
                        "6. Учитывай контекст всего текста, как если бы разделения на строки и нумерации строк не было\n"
                        "7. Не изменяй HTML-теги (но переводи текст внутри тегов с учётом общего контекста)\n"
                        "8. Для многозначных выражений и слов выбирай контекстно-подходящий перевод\n"
                        "9. Не переводи латынь\n\n"
                    f"{text}"
                )
            }
        ],
        "stream": False  # Отключаем потоковый режим
    }

    try:
        timeout_value = int(settings.get('timeout', 360))
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            data=json.dumps(data),
            timeout=timeout_value
        )
        response.raise_for_status()
        response_json = response.json()

        logger.debug(f"DeepSeek API Response (JSON):\n{json.dumps(response_json, indent=2, ensure_ascii=False)}")

        if 'choices' in response_json and response_json['choices']:
            message = response_json['choices'][0].get('message')
            if message and 'content' in message:
                return message['content']
            else:
                logger.error(f"DeepSeek API: No content in response: {response_json}")
                return None
        else:
            logger.error(f"DeepSeek API: Unexpected response structure: {response_json}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API Request Error: {e}")
        return None
    except Exception as e:
        logger.error(f"DeepSeek API Error: {str(e)}")
        logger.exception("DeepSeek API Exception details:")
        return None

def translate_text_gemini(text: str, settings: Dict) -> Optional[str]:
    api_key = get_api_key(settings)
    if not api_key:
        return None

    headers = {
        'Content-Type': 'application/json'
    }
    params = {
        'key': api_key
    }
    data = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        f"Выполните литературный перевод на {settings['target_language']} строго соблюдая:\n"
                        "1. Сохраняй исходные номера строк без изменений\n"
                        "2. Не меняй структуру блоков и порядок строк\n"
                        "3. Первая строка блока - всегда только номер\n"
                        "4. Не добавляй новые строки и символы\n"
                        "5. Специальные конструкции (например, ♪) сохраняй как есть\n"
                        "6. Учитывай контекст всего текста, как если бы разделения на строки и нумерации строк не было\n"
                        "7. Не изменяй HTML-теги (но переводи текст внутри тегов с учётом общего контекста)\n"
                        "8. Для многозначных выражений и слов выбирай контекстно-подходящий перевод\n"
                        "9. Не переводи латынь\n\n"
                        f"{text}"
                    )
                }
            ]
        }],
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }

    try:
        timeout_value = int(settings.get('timeout', 360))  # <-- Используем таймаут из настроек
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings['gemini_model']}:generateContent",
            headers=headers,
            params=params,
            data=json.dumps(data),
            timeout=timeout_value
        )
        response.raise_for_status()
        response_json = response.json()

        logger.debug(f"Gemini API Response (JSON):\n{json.dumps(response_json, indent=2, ensure_ascii=False)}")

        if 'candidates' in response_json and response_json['candidates']:
            candidate = response_json['candidates'][0]
            if 'finishReason' in candidate and candidate['finishReason'] == 'SAFETY':
                safety_ratings = candidate.get('safetyRatings', [])
                safety_details = ", ".join(
                    [f"{rating['category']}: {rating['probability']}" for rating in safety_ratings]
                )
                logger.warning(f"Gemini API blocked content due to safety policy. Details: {safety_details}")
                return None

            if 'content' in candidate and candidate['content']['parts']:
                text_result = candidate['content']['parts'][0]['text']
                if text_result is None:
                    raise Exception("Gemini API returned None text in response")
                return text_result

        logger.error(f"Gemini API response structure error: {response_json}")
        raise Exception("Неожиданная структура ответа Gemini API")

    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini API HTTP Error: {e}")
        if e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
        return None

    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        logger.exception("Gemini API Exception details:")
        return None


def translate_text(text: str, settings: Dict) -> Optional[str]:
    api_provider = settings['api_provider']
    if api_provider == 'deepseek':
        return translate_text_deepseek(text, settings)
    elif api_provider == 'gemini':
        return translate_text_gemini(text, settings)
    else:
        logger.error(f"Неизвестный провайдер API: {api_provider}")
        raise ValueError(f"Неизвестный провайдер API: {api_provider}")

def create_chunks(indices: Set[int], subtitles: List[str], settings: Dict, overlap: int = 10) -> List[ChunkInfo]:
    """
    Создает блоки с перекрытием.

    Args:
        indices: Множество индексов субтитров для обработки.
        subtitles: Список субтитров.
        settings: Dict - словарь настроек, содержащий chunk_size
        overlap: Количество строк перекрытия между блоками.

    Returns:
        Список ChunkInfo.
    """
    chunk_size_setting = settings.get('chunk_size', MAX_CHUNK_SIZE) # Получаем chunk_size из настроек
    if chunk_size_setting == 0: # Если chunk_size = 0, не делим на блоки
        full_content = '\n\n'.join([f"{i+1}\n{subtitles[i]}" for i in sorted(list(indices))])
        return [ChunkInfo(indices=sorted(list(indices)), content=full_content)]


    chunks = []
    current_chunk = []
    current_indices = []
    current_size = 0
    sorted_indices = sorted(list(indices))  # Преобразуем в список и сортируем

    for i, idx in enumerate(sorted_indices):
        sub = f"{idx + 1}\n{subtitles[idx]}"
        sub_size = len(sub.encode('utf-8')) + 2

        if current_size + sub_size > chunk_size_setting and current_chunk: # Используем chunk_size_setting
            chunks.append(ChunkInfo(
                indices=current_indices.copy(),
                content='\n\n'.join(current_chunk)
            ))
            # Перекрытие: начинаем следующий блок на 'overlap' строк раньше, но не более, чем есть строк
            start_overlap = max(0, len(current_indices) - overlap)
            current_chunk = current_chunk[start_overlap:]
            current_indices = current_indices[start_overlap:]
            current_size = sum(len(f"{ind + 1}\n{subtitles[ind]}".encode('utf-8')) + 2 for ind in current_indices)


        current_chunk.append(sub)
        current_indices.append(idx)
        current_size += sub_size

    if current_chunk:
        chunks.append(ChunkInfo(
            indices=current_indices.copy(),
            content='\n\n'.join(current_chunk)
        ))

    return chunks

def create_tail_chunks(failed_indices: Set[int], 
                       subtitles: List[str], 
                       settings: Dict,
                       overlap: int = 10) -> List[ChunkInfo]:
    """
    Создаёт блоки для повторного перевода "хвостов" – пропущенных строк.
    Логика:
      1) Группируем пропущенные строки по близости (если между ними разница <= overlap).
      2) Для каждой группы добавляем overlap строк до начала группы (если возможно).
      3) Режем итог по chunk_size (если > 0).
    """

    # Если пропущенных строк нет – ничего возвращать
    if not failed_indices:
        return []

    chunk_size_setting = settings.get('chunk_size', 1900)
    # сортируем пропущенные индексы
    sorted_failed = sorted(list(failed_indices))

    # 1. Сгруппируем пропущенные строки
    groups = []
    current_group = [sorted_failed[0]]
    for i in range(1, len(sorted_failed)):
        if (sorted_failed[i] - sorted_failed[i - 1]) <= overlap:
            # Продолжаем текущую группу
            current_group.append(sorted_failed[i])
        else:
            # Закрываем текущую группу и начинаем новую
            groups.append(current_group)
            current_group = [sorted_failed[i]]
    groups.append(current_group)  # последний участок

    # 2. Для каждой группы создадим итоговые блоки с учётом overlap строк "до" группы
    tail_chunks: List[ChunkInfo] = []

    for grp in groups:
        start_fail = grp[0]
        end_fail = grp[-1]

        # Вычислим, откуда начинаем контекст (overlap строк до начала группы)
        coverage_start = max(0, start_fail - overlap)
        coverage_end = end_fail  # включительно

        # Собираем все ИСТИННЫЕ индексы для данного покрытия
        coverage_indices = list(range(coverage_start, coverage_end + 1))

        # 3. Теперь надо превратить coverage_indices в один или несколько блоков
        #    в зависимости от chunk_size_setting.
        if chunk_size_setting == 0:
            # Без лимита размера – делаем один блок
            chunk_content = []
            for idx in coverage_indices:
                # Формируем в стиле SRT (номер_строки, перевод)
                chunk_content.append(f"{idx + 1}\n{subtitles[idx]}")
            content_str = "\n\n".join(chunk_content)
            tail_chunks.append(ChunkInfo(indices=coverage_indices, content=content_str))
        else:
            # Ограничиваем по размеру блока (байты utf-8)
            temp_content = []
            temp_indices = []
            current_size = 0

            for idx in coverage_indices:
                sub_str = f"{idx + 1}\n{subtitles[idx]}"
                sub_size = len(sub_str.encode('utf-8')) + 2  # +2 на '\n\n'
                # Если не влезает – оформляем предыдущий блок
                if current_size + sub_size > chunk_size_setting and temp_content:
                    # Сохраняем накопленное
                    chunk_str = "\n\n".join(temp_content)
                    tail_chunks.append(ChunkInfo(indices=temp_indices.copy(), content=chunk_str))
                    # Начинаем новый
                    temp_content = []
                    temp_indices = []
                    current_size = 0

                # Добавляем строку
                temp_content.append(sub_str)
                temp_indices.append(idx)
                current_size += sub_size

            # Если что-то осталось в temp_content
            if temp_content:
                chunk_str = "\n\n".join(temp_content)
                tail_chunks.append(ChunkInfo(indices=temp_indices, content=chunk_str))

    return tail_chunks

def translate_chunk(chunk: ChunkInfo, settings: Dict, subtitles: List[str], translated_subs: List[str],
                    attempt_type: str = "initial", overlap: int = 10) -> Set[int]:
    """
    Переводит блок субтитров, улучшенная обработка инструкций от API.
    """
    failed_indices = set()
    instruction_prefixes = ("Важно:", "Инструкция:", "Note:", "Important:") # Список префиксов инструкций

    try:
        translated_text = translate_text(chunk.content, settings)
        if translated_text is None:
            logger.warning(f"Перевод блока ({attempt_type}) не удался (API error/safety block).")
            failed_indices.update(chunk.indices)
            return failed_indices

        translated_blocks = translated_text.strip().split('\n\n')
        processed_indices = set()
        
        # 1. Подготовка: Индексы и итераторы
        chunk_indices_iter = iter(chunk.indices) # Итератор по индексам блока
        original_idx = next(chunk_indices_iter, None) # Текущий индекс оригинала, начинаем с первого

        translated_block_index = 0 # Индекс текущего блока перевода

        logger.debug(f"блок ({attempt_type}): индексы {chunk.indices}")

        # 2. Основной цикл обработки блоков перевода
        while translated_block_index < len(translated_blocks) and original_idx is not None:
            block = translated_blocks[translated_block_index]
            block_lines = block.strip().split('\n')

            if not block_lines: #Пустой блок
                logger.warning(f"Пустой блок в переводе, пропуск.")
                translated_block_index += 1
                continue

            first_line = block_lines[0].strip()
            if not first_line.isdigit(): #Первая строка - не номер
                is_instruction = False
                for prefix in instruction_prefixes: #Проверка на префикс инструкции
                    if first_line.startswith(prefix):
                        is_instruction = True
                        break
                if is_instruction: #Это инструкция
                    logger.warning(f"Блок-инструкция пропущен: '{first_line}'.")
                    translated_block_index += 1 #Пропускаем блок-инструкцию, original_idx не меняем
                    continue #Переходим к следующему блоку перевода (не меняя original_idx)
                else: #Не номер и не инструкция - обрабатываем как перевод для текущего original_idx
                    logger.warning(f"Первая строка не номер и не инструкция ('{first_line}'), блок целиком обрабатывается как перевод для текущего original_idx={original_idx}.")
                    #Весь блок считаем переводом для текущего original_idx
                    translated_text_block = block #Весь блок, включая "не-номер" в первой строке
                    translated_subs[original_idx] = translated_text_block
                    processed_indices.add(original_idx)
                    original_idx = next(chunk_indices_iter, None) #Переходим к следующему original_idx
                    translated_block_index += 1 #Переходим к следующему блоку перевода
                    continue


            translated_idx_from_block = int(first_line) - 1 #Номер из блока перевода

            if translated_idx_from_block == original_idx:
                # 3. Случай 1: Идеальное совпадение индексов (1:1)
                translated_text_block = '\n'.join(block_lines[1:]) #Перевод - все строки, кроме первой (с номером)
                translated_subs[original_idx] = translated_text_block
                processed_indices.add(original_idx)
                logger.debug(f"  1:1 Совпадение: original_idx={original_idx}, translated_idx={translated_idx_from_block}")

                original_idx = next(chunk_indices_iter, None) #Переходим к следующему original_idx
                translated_block_index += 1 #Переходим к следующему блоку перевода


            elif translated_idx_from_block < original_idx:
                # 4. Случай 2: "Лишний" блок в переводе (индекс перевода МЕНЬШЕ индекса оригинала)
                logger.warning(f"  Лишний блок в переводе (translated_idx={translated_idx_from_block} < original_idx={original_idx}), пропуск блока.")
                translated_block_index += 1 #Пропускаем "лишний" блок, но original_idx не меняем
                

            elif translated_idx_from_block > original_idx:
                # 5. Случай 3: "Пропущен" субтитр в переводе (индекс перевода БОЛЬШЕ индекса оригинала)
                logger.warning(f"  Пропущен субтитр в переводе (translated_idx={translated_idx_from_block} > original_idx={original_idx}), заполнение оригинала.")
                #Заполняем translated_subs[original_idx] оригинальным текстом (или можно пустой строкой, если нужно)
                translated_subs[original_idx] = subtitles[original_idx] #Оригинальный текст
                processed_indices.add(original_idx) #Помечаем как "обработанный" (хотя и не переведен)

                original_idx = next(chunk_indices_iter, None) #Переходим к следующему original_idx, блок перевода не трогаем, т.к. он "не подходит"

            else: #default case - shouldn't happen, but for safety
                logger.error(f"  Неожиданная ситуация при сопоставлении: translated_idx={translated_idx_from_block}, original_idx={original_idx}. Пропуск блока.")
                translated_block_index += 1 #Пропускаем блок перевода


        # 6. Обработка "хвоста" оригинальных субтитров (если остались не сопоставленные original_idx)
        while original_idx is not None:
            failed_indices.add(original_idx) #Помечаем оставшиеся как непереведенные
            logger.warning(f"  Необработанный хвост оригинала: original_idx={original_idx}")
            original_idx = next(chunk_indices_iter, None)


        failed_indices.update(set(chunk.indices) - processed_indices)


    except Exception as e:
        logger.error(f"Ошибка перевода блока ({attempt_type}): {str(e)}")
        failed_indices.update(chunk.indices)
        logger.exception("Детали ошибки:") #Трассировка ошибки полностью


    return failed_indices

def initial_translation(chunks: List[ChunkInfo], settings: Dict, subtitles: List[str], translated_subs: List[str]) -> Set[int]:
    """
    Выполняет первичный перевод субтитров.
    """
    failed_indices = set()
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        print(f"Перевод блока {i + 1} из {total_chunks}")
        chunk_failed_indices = translate_chunk(chunk, settings, subtitles, translated_subs, "initial")
        failed_indices.update(chunk_failed_indices)
        # Экспоненциальная задержка + jitter
        delay = BASE_DELAY * (2**1) + random.uniform(0, 0.5) # attempt_number = 1 для первой попытки
        time.sleep(delay)
    return failed_indices

def retry_translation(failed_indices: Set[int], 
                      settings: Dict, 
                      subtitles: List[str], 
                      translated_subs: List[str]) -> Set[int]:
    """
    Выполняет повторные попытки перевода "хвостов", используя create_tail_chunks.
    При каждой итерации переводятся только пропущенные строки, 
    вокруг которых добавляется контекст overlap.
    """
    current_failed_indices = failed_indices.copy()
    attempt = 1
    max_attempts = settings.get('max_retries', 5)
    overlap = 10  # можно вынести в настройки при желании

    while attempt <= max_attempts and current_failed_indices:
        logger.info(f"\nПовторная попытка № {attempt} из {max_attempts}")
        logger.info(f"Осталось пропущенных строк: {len(current_failed_indices)}")

        # Создаём хвостовые блоки
        tail_chunks = create_tail_chunks(current_failed_indices, subtitles, settings, overlap=overlap)
        logger.info(f"Сформировано хвостовых блоков: {len(tail_chunks)}")

        iteration_failed_indices = set()

        for i, chunk in enumerate(tail_chunks, start=1):
            print(f"Перевод хвостового блока {i} из {len(tail_chunks)}")
            # Попытка перевести блок
            chunk_failed = translate_chunk(chunk, settings, subtitles, translated_subs, f"tail-retry-{attempt}")
            iteration_failed_indices.update(chunk_failed)

            # Небольшая задержка между запросами
            time.sleep(BASE_DELAY)

        # Теперь то, что снова пропущено, пойдёт на следующую итерацию
        current_failed_indices = iteration_failed_indices.copy()
        attempt += 1

    return current_failed_indices

def process_file(filename: str, settings: Dict):
    logger.info(f"\nОбработка файла: {filename}")

    # Определяем, нужно ли вообще переводить
    need_translation = settings['target_language'].lower() not in ['none', '']
    api_key = None

    if need_translation:
        api_key = get_api_key(settings)
        if not api_key:
            logger.warning(f"API ключ {settings['api_provider']} не найден, пропуск перевода.")
            return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Ошибка чтения файла {filename}: {str(e)}")
        return

    # Определяем расширение (srt или ass)
    _, ext = os.path.splitext(filename.lower())

    if ext == '.srt':
        # === SRT ===
        # Парсим SRT
        timecodes, subtitles = parse_srt(content)
        total_subs = len(subtitles)
        if not total_subs:
            logger.warning(f"Файл {filename} не содержит субтитров.")
            return

        # Сдвигаем время, если нужно
        if settings['time_shift'] != 0:
            timecodes = [adjust_timecode(tc, settings['time_shift']) for tc in timecodes]

        translated_subs = subtitles.copy()

        if need_translation and api_key:
            # Начальный перевод блоками
            initial_chunks = create_chunks(set(range(total_subs)), subtitles, settings)
            logger.info(f"Начальный перевод (SRT): всего {len(initial_chunks)} блоков")
            failed_indices = set()

            # Переводим начальные блоки
            for i, ch in enumerate(initial_chunks, start=1):
                print(f"Перевод блока {i} из {len(initial_chunks)}")
                chunk_failed = translate_chunk(ch, settings, subtitles, translated_subs, attempt_type="initial")
                failed_indices.update(chunk_failed)
                time.sleep(BASE_DELAY)

            # Повторные попытки для "хвостов"
            final_failed_indices = retry_translation(failed_indices, settings, subtitles, translated_subs)
            logger.info(f"Итогово непреведённых строк: {len(final_failed_indices)}")

            # Оставшиеся — оставляем оригинал
            for idx in final_failed_indices:
                translated_subs[idx] = subtitles[idx]

        # Сохраняем результат в output/<имя_файла>
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, (tc, text) in enumerate(zip(timecodes, translated_subs), 1):
                    f.write(f"{i}\n{tc}\n{text}\n\n")
            logger.info(f"Сохранено: {output_path}")
        except Exception as e:
            logger.error(f"Ошибка записи {output_path}: {str(e)}")

    elif ext == '.ass':
        # === ASS ===
        header_lines, events_format_line, dialogues, timecodes, subtitles = parse_ass(content)
        total_subs = len(subtitles)
        if not total_subs:
            logger.warning(f"Файл {filename} не содержит строк типа 'Dialogue:'.")
            return

        # Сдвиг времени, если нужно
        if settings['time_shift'] != 0:
            adjust_timecode_ass(dialogues, settings['time_shift'])
            # Обновим timecodes (аналог SRT "start --> end"), чтобы блок-система видела новое время
            for i, d in enumerate(dialogues):
                new_tc = f"{format_time_ass(d['start'])} --> {format_time_ass(d['end'])}"
                timecodes[i] = new_tc

        translated_subs = subtitles.copy()

        if need_translation and api_key:
            # Начальный перевод блоками
            initial_chunks = create_chunks(set(range(total_subs)), subtitles, settings)
            logger.info(f"Начальный перевод (ASS): всего {len(initial_chunks)} блоков")
            failed_indices = set()

            # Переводим начальные блоки
            for i, ch in enumerate(initial_chunks, start=1):
                print(f"Перевод блока {i} из {len(initial_chunks)}")
                chunk_failed = translate_chunk(ch, settings, subtitles, translated_subs, attempt_type="initial")
                failed_indices.update(chunk_failed)
                time.sleep(BASE_DELAY)

            # Повторные попытки для "хвостов"
            final_failed_indices = retry_translation(failed_indices, settings, subtitles, translated_subs)
            logger.info(f"Итогово непреведённых строк: {len(final_failed_indices)}")

            # Оставшиеся — оставляем оригинал
            for idx in final_failed_indices:
                translated_subs[idx] = subtitles[idx]

        # Пересобираем финальный .ass
        output_ass = reconstruct_ass(header_lines, events_format_line, dialogues, translated_subs)

        # Сохраняем результат
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_ass)
            logger.info(f"Сохранено: {output_path}")
        except Exception as e:
            logger.error(f"Ошибка записи {output_path}: {str(e)}")

    else:
        logger.warning(f"Файл {filename} имеет неподдерживаемое расширение. Пропуск.")

def main():
    settings = read_settings()

    # Ищем все файлы с расширениями .srt и .ass
    subtitle_files = glob.glob('*.srt') + glob.glob('*.ass')
    if not subtitle_files:
        logger.warning("Не найдено файлов SRT или ASS для обработки")
        return

    print("\nТекущие настройки:")
    print(f"• Сдвиг времени: {settings['time_shift']} сек")
    print(f"• Язык перевода: {settings['target_language']}")
    print(f"• Провайдер API: {settings['api_provider']}")

    if settings['api_provider'] == 'deepseek':
        api_key_status = 'установлен' if settings['deepseek_api_key'] else 'отсутствует'
        print(f"• API ключ DeepSeek: {api_key_status}")
        print(f"• Модель DeepSeek: {settings['deepseek_model']}")
    elif settings['api_provider'] == 'gemini':
        api_key_status = 'установлен' if settings['gemini_api_key'] else 'отсутствует'
        print(f"• API ключ Gemini: {api_key_status}")
        print(f"• Модель Gemini: {settings['gemini_model']}")

    print(f"• Повторные попытки: {settings['max_retries']}")

    if input("\nНажмите Enter для старта или 1 для настроек: ").strip() == '1':
        configure_settings(settings)

    logger.info("Начало обработки файлов...")
    for file in subtitle_files:
        process_file(file, settings)

    logger.info("Обработка завершена")



if __name__ == "__main__":
    main()

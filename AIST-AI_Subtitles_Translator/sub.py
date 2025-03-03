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
    level=logging.INFO , 
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
        f.write('target_language=english\n')
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
        'target_language': 'english',
        'api_provider': 'gemini',
        'deepseek_api_key': '',
        'gemini_api_key': '',
        'gemini_model': 'gemini-2.0-flash-thinking-exp-01-21',
        'deepseek_model': 'deepseek-chat',  
        'chunk_size': 0,
        'max_retries': 10,
        'timeout': 360  
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
    # Ensure that api_provider is in settings, even if it was not in the file
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
        f.write(f"deepseek_model={settings['deepseek_model']}\n") 
        f.write(f"chunk_size={settings['chunk_size']}\n")
        f.write(f"max_retries={settings['max_retries']}\n")
        f.write(f"timeout={settings['timeout']}\n") 

def configure_settings(settings: Dict):
    while True:
        print("\nSettings:")
        print(f"1. Time shift (current: {settings['time_shift']} sec)")
        print(f"2. Translation language (current: '{settings['target_language']}')")
        print(f"3. API provider (current: '{settings['api_provider']}')")

        next_option = 4

        if settings['api_provider'] == 'gemini':
            api_key_status = 'set' if settings['gemini_api_key'] else 'missing'
            print(f"{next_option}. Gemini API key (status: {api_key_status})")
            option_number_gemini_key = next_option
            next_option += 1
            print(f"{next_option}. Gemini Model (current: '{settings['gemini_model']}')")
            option_number_gemini_model = next_option
            next_option += 1

        elif settings['api_provider'] == 'deepseek':
            api_key_status = 'set' if settings['deepseek_api_key'] else 'missing'
            print(f"{next_option}. DeepSeek API key (status: {api_key_status})")
            option_number_deepseek_key = next_option
            next_option += 1
            print(f"{next_option}. DeepSeek Model (current: '{settings['deepseek_model']}')")
            option_number_deepseek_model = next_option
            next_option += 1

        else:
            print(f"{next_option}. API key (unknown provider)")
            option_number_unknown_provider_key = next_option
            next_option += 1

        print(f"{next_option}. Chunk size (current: {settings['chunk_size']} characters, 0 - disabled)")
        option_number_chunk_size = next_option
        next_option += 1

        print(f"{next_option}. Retries (current: {settings['max_retries']})")
        option_number_retries = next_option
        next_option += 1

        print(f"{next_option}. Timeout (current: {settings['timeout']} s)")
        option_number_timeout = next_option
        next_option += 1

        print(f"{next_option}. Start processing")
        option_number_start = next_option

        choice = input("Choose an option: ").strip()

        if choice == '1':
            while True:
                user_input = input("Enter time shift (seconds with a dot): ").replace(',', '.').strip()
                try:
                    settings['time_shift'] = float(user_input)
                    write_settings(settings)
                    print("Shift updated")
                    break
                except ValueError:
                    print("Number format error!")
            continue

        elif choice == '2':
            lang = input("Enter translation language (e.g. 'russian' or 'none'): ").strip()
            settings['target_language'] = lang
            write_settings(settings)
            print("Language updated")
            continue

        elif choice == '3':
            while True:
                print("   Choose a provider:")
                print("   1 - Gemini")
                print("   2 - DeepSeek")
                provider_choice = input("Select API provider (1 or 2): ").strip()
                if provider_choice == '1':
                    settings['api_provider'] = 'gemini'
                    write_settings(settings)
                    print("API provider changed to 'gemini'")
                    break
                elif provider_choice == '2':
                    settings['api_provider'] = 'deepseek'
                    write_settings(settings)
                    print("API provider changed to 'deepseek'")
                    break
                else:
                    print("Invalid choice. Enter 1 or 2.")
            continue

        # --- Gemini BLOCK ---
        elif settings['api_provider'] == 'gemini' and choice.isdigit():
            numeric_choice = int(choice)

            if numeric_choice == option_number_gemini_key:
                api_key = input("Enter new Gemini API key: ").strip()
                settings['gemini_api_key'] = api_key
                write_settings(settings)
                print("API key updated")
                continue

            elif numeric_choice == option_number_gemini_model:
                while True:
                    print("   Choose Gemini model:")
                    print("   1 - Gemini 2.0 Flash (gemini-2.0-flash)")
                    print("   2 - Gemini 2.0 Flash-Lite (gemini-2.0-flash-lite-preview-02-05)")
                    print("   3 - Gemini 1.5 Flash (gemini-1.5-flash)")
                    print("   4 - Gemini 1.5 Flash-8B (gemini-1.5-flash-8b)")
                    print("   5 - Gemini 1.5 Pro (gemini-1.5-pro)")
                    print("   6 - Gemini 2.0 Pro Exp (gemini-2.0-pro-exp-02-05)")
                    print("   7 - Gemini 2.0 Flash Thinking Exp (gemini-2.0-flash-thinking-exp-01-21)")
                    model_choice = input("Select Gemini model number: ").strip()

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
                        print("Invalid model choice.")
                        continue

                    write_settings(settings)
                    print(f"Gemini model changed to '{settings['gemini_model']}'")
                    break
                continue

        # --- DeepSeek BLOCK ---
        elif settings['api_provider'] == 'deepseek' and choice.isdigit():
            numeric_choice = int(choice)

            if numeric_choice == option_number_deepseek_key:
                api_key = input("Enter new DeepSeek API key: ").strip()
                settings['deepseek_api_key'] = api_key
                write_settings(settings)
                print("API key updated")
                continue

            elif numeric_choice == option_number_deepseek_model:
                while True:
                    print("   Choose DeepSeek model:")
                    print("   1 - deepseek-chat (64K context, 8K output)")
                    print("   2 - deepseek-reasoner (64K context, 8K output, CoT up to 32K)")
                    model_choice = input("Select DeepSeek model number: ").strip()

                    if model_choice == '1':
                        settings['deepseek_model'] = 'deepseek-chat'
                    elif model_choice == '2':
                        settings['deepseek_model'] = 'deepseek-reasoner'
                    else:
                        print("Invalid model choice.")
                        continue

                    write_settings(settings)
                    print(f"DeepSeek model changed to '{settings['deepseek_model']}'")
                    break
                continue

        # --- Other options ---
        if choice.isdigit():
            numeric_choice = int(choice)

            # Chunk size
            if numeric_choice == option_number_chunk_size:
                while True:
                    user_input = input("Enter new chunk size (0-1000000, 0 - disable): ").strip()
                    try:
                        chunk_size = int(user_input)
                        if 0 <= chunk_size <= 1000000:
                            settings['chunk_size'] = chunk_size
                            write_settings(settings)
                            print("Chunk size updated")
                            break
                        else:
                            print(f"Invalid value. Enter a number from 0 to 1000000")
                    except ValueError:
                        print("Number format error!")
                continue

            # Retries
            elif numeric_choice == option_number_retries:
                while True:
                    try:
                        retries = int(input("Enter number of retries (0-1000): "))
                        if 0 <= retries <= 1000:
                            settings['max_retries'] = retries
                            write_settings(settings)
                            print("Value updated")
                            break
                        else:
                            print(f"Invalid value. Enter a number from 0 to 1000")
                    except ValueError:
                        print("Enter an integer")
                continue

            # Timeout
            elif numeric_choice == option_number_timeout:
                while True:
                    try:
                        new_timeout = int(input("Enter timeout in seconds (0-3600): "))
                        if 0 <= new_timeout <= 3600:
                            settings['timeout'] = new_timeout
                            write_settings(settings)
                            print("Timeout updated.")
                            break
                        else:
                            print("Invalid value. Enter a number from 0 to 3600.")
                    except ValueError:
                        print("Enter an integer.")
                continue

            # Start processing
            elif numeric_choice == option_number_start:
                break

        print("Invalid choice")

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
        logger.error(f"Unknown API provider: {api_provider}")
        return None

    if not api_key:
        print(f"\nAPI key {api_provider} not found!")
        api_key = input(f"Enter your API key {api_provider}: ").strip()
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
    Converts time from ASS format (h:mm:ss.cs) to seconds (float).

    Example input: "0:01:02.50"
    Output: 62.50 (float)
    """
    # Format: HOURS:MINUTES:SECONDS.CENTISECONDS (or milliseconds, depends on software)
    # Often 2 digits after the dot (hundredths of a second), but sometimes 3 digits (milliseconds).
    # Let's parse the general case with a floating point.
    try:
        parts = time_str.split(':')  # [hours, minutes, "seconds.fractions"]
        hours = int(parts[0])
        minutes = int(parts[1])
        sec_fraction = float(parts[2])  # seconds + decimal part
        return hours * 3600 + minutes * 60 + sec_fraction
    except Exception:
        # If parsing fails, return 0
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
    Formats time (float, sec) into ASS format string (h:mm:ss.cs).

    Example input: 62.50
    Output: "0:01:02.50"
    """
    # Let's limit to two decimal places for compatibility
    # (many .ass editors use hundredths of a second).
    hours = int(seconds // 3600)
    remainder = seconds % 3600
    minutes = int(remainder // 60)
    sec_fraction = remainder % 60  # this is seconds with a floating point
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
        logger.error(f"Time correction error: {str(e)}")
        return timecode

def adjust_timecode_ass(dialogues, shift: float):
    """
    Applies time shift (shift in seconds) to all dialogues in the dialogues list.
    dialogues is a list of dictionaries, each has 'start' and 'end' (float).

    As a result, changes 'start' and 'end' fields to corrected values (not less than 0).
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
    Parses the content of an .ass file, returning:
      - header_lines: all header lines (up to [Events], including the Script Info block, etc.)
      - events_format_line: 'Format:...' line (if present) from [Events] section
      - dialogues: a list of dictionaries, where each dictionary describes a subtitle line:
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
      - timecodes: a list of strings like "start --> end" (similar to SRT), to reuse chunk logic.
      - subtitles: a list of only texts (at the same index as timecodes).

    Example dialogue format:
      Dialogue: 0,0:01:02.50,0:01:05.00,Default,Nobody,0,0,0,,This is text

    Order of fields after 'Dialogue:' matches:
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
            # Looking for [Events] block
            header_lines.append(line)  # Write to header everything before [Events] (including the line itself)
            if stripped.lower() == '[events]':
                in_events_section = True
            continue

        # Already in [Events] block
        if stripped.lower().startswith('format:'):
            # Format description of fields
            events_format_line = line
            continue

        if stripped.lower().startswith('dialogue:'):
            # Parsing subtitle line
            # Dialogue format: Dialogue: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
            # Split using split(',', 9) to avoid "cutting" the text
            parts = line.split(':', 1)  # ["Dialogue", " Layer,0:...,Text"]
            dialogue_data = parts[1].strip()
            fields = dialogue_data.split(',', 9)  # max 10 fields

            if len(fields) < 10:
                # Invalid structure
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

            # For further translation logic, we create an SRT-like structure
            # timecodes[i], subtitles[i]
            srt_style_timecode = f"{format_time_ass(start_sec)} --> {format_time_ass(end_sec)}"
            timecodes.append(srt_style_timecode)
            subtitles.append(text_str)

        else:
            # Could be "Comment:" or something else. Save as is in header_lines
            # Or, if desired, you can process Comment: ... the same way.
            header_lines.append(line)

    return header_lines, events_format_line, dialogues, timecodes, subtitles

def reconstruct_ass(header_lines: list,
                    events_format_line: str,
                    dialogues: list,
                    translated_subs: list) -> str:
    """
    Reassembles the final .ass text based on:
      - header_lines (everything before and inside [Events], but without 'Dialogue:' lines),
      - events_format_line ('Format: ...' line),
      - dialogues (list of dictionaries with keys: start, end, layer, style, name, margin_l, margin_r, margin_v, effect),
      - translated_subs (list of final translated texts of the same length as dialogues).

    Returns the final .ass string to write to a file.
    """
    output_lines = []
    # First, add all header lines
    for hl in header_lines:
        output_lines.append(hl)

    # If there is a format line, add it
    if events_format_line:
        output_lines.append(events_format_line)

    # Then add dialogue lines with translated text
    for i, d in enumerate(dialogues):
        start_str = format_time_ass(d['start'])
        end_str = format_time_ass(d['end'])
        text_str = translated_subs[i]  # translation or original if skipped

        # Assemble fields according to format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
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

    # Return the final text combined with translations
    return "\n".join(output_lines) + "\n"

def translate_chunk(chunk: ChunkInfo,
                    settings: Dict,
                    subtitles: List[str],
                    translated_subs: List[str],
                    attempt_type: str = "initial") -> Set[int]:
    """
    Translates a chunk of subtitles. In case of any index mismatch,
    the remaining lines of this chunk are marked as "skipped".
    """

    failed_indices = set()
    instruction_prefixes = ("Важно:", "Инструкция:", "Note:", "Important:") # Intentionally left in Russian and English

    try:
        translated_text = translate_text(chunk.content, settings)
        if translated_text is None:
            # API returned None (e.g., blocked by policy)
            # Mark all lines of the chunk as failed
            failed_indices.update(chunk.indices)
            return failed_indices

        translated_blocks = translated_text.strip().split('\n\n')
        processed_indices = set()

        # Preparing iterator over original line indices
        chunk_indices_iter = iter(chunk.indices)
        original_idx = next(chunk_indices_iter, None)

        tb_index = 0  # index in translated blocks

        while tb_index < len(translated_blocks) and original_idx is not None:
            block = translated_blocks[tb_index].strip()
            if not block:
                # Empty translation block, skipping
                tb_index += 1
                continue

            lines_in_block = block.split('\n')
            first_line = lines_in_block[0].strip()

            # 1) Check: non-digit first line => instruction or "garbage"
            if not first_line.isdigit():
                # Checking for possible instruction prefixes
                if any(first_line.startswith(pref) for pref in instruction_prefixes):
                    # This is not a subtitle, but clearly a service instruction from the model
                    tb_index += 1
                    continue
                else:
                    # If it's not an instruction and not a number,
                    # then we perceive it entirely as a translation for the current original_idx
                    translated_subs[original_idx] = block
                    processed_indices.add(original_idx)
                    original_idx = next(chunk_indices_iter, None)
                    tb_index += 1
                    continue

            # If the line is a digit, try to match indices
            try:
                translated_idx_from_block = int(first_line) - 1
            except ValueError:
                # Theoretically should not happen, but just in case
                # If conversion fails - consider it an index error
                # and mark the remaining lines
                tail_index_pos = chunk.indices.index(original_idx)
                missed_lines = chunk.indices[tail_index_pos:]
                failed_indices.update(missed_lines)
                return failed_indices

            # 2) Index comparison
            if translated_idx_from_block == original_idx:
                # Match - take the translation (without the first line)
                translated_text_block = '\n'.join(lines_in_block[1:])
                translated_subs[original_idx] = translated_text_block
                processed_indices.add(original_idx)

                original_idx = next(chunk_indices_iter, None)
                tb_index += 1

            else:
                # Any mismatch -> "index error"
                # Need to add ALL remaining lines to skipped
                tail_index_pos = chunk.indices.index(original_idx)
                missed_lines = chunk.indices[tail_index_pos:]
                failed_indices.update(missed_lines)
                return failed_indices

        # If original indices are left at the end of the loop,
        # it means they were not translated - also mark as skipped
        while original_idx is not None:
            failed_indices.add(original_idx)
            original_idx = next(chunk_indices_iter, None)

    except Exception as e:
        # Any error - all lines of the chunk go to skipped
        failed_indices.update(chunk.indices)
        logger.error(f"Chunk translation error ({attempt_type}): {str(e)}")
        logger.exception("Error details:")

    return failed_indices

def translate_text_deepseek(text: str, settings: Dict) -> Optional[str]:
    api_key = get_api_key(settings)
    if not api_key:
        return None  # No API key - exiting

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # Use the selected model from settings (deepseek-chat or deepseek-reasoner)
    chosen_model = settings.get('deepseek_model', 'deepseek-chat')

    data = {
        "model": chosen_model,  #  Get model name from settings
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Perform a literary translation into {settings['target_language']} strictly adhering to:\n"
                        "1. Keep the original line numbers unchanged\n"
                        "2. Do not change the structure of blocks and the order of lines\n"
                        "3. The first line of a block is always just a number\n"
                        "4. Do not add new lines and symbols\n"
                        "5. Keep special constructions (e.g., ♪) as is\n"
                        "6. Consider the context of the entire text as if there were no line breaks and line numbering\n"
                        "7. Do not change HTML tags (but translate the text inside the tags considering the overall context)\n"
                        "8. For ambiguous expressions and words, choose a contextually appropriate translation\n"
                        "9. Do not translate Latin\n\n"
                    f"{text}"
                )
            }
        ],
        "stream": False  # Disable streaming mode
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
                        f"Perform a literary translation into {settings['target_language']} strictly adhering to:\n"
                        "1. Keep the original line numbers unchanged\n"
                        "2. Do not change the structure of blocks and the order of lines\n"
                        "3. The first line of a block is always just a number\n"
                        "4. Do not add new lines and symbols\n"
                        "5. Keep special constructions (e.g., ♪) as is\n"
                        "6. Consider the context of the entire text as if there were no line breaks and line numbering\n"
                        "7. Do not change HTML tags (but translate the text inside the tags considering the overall context)\n"
                        "8. For ambiguous expressions and words, choose a contextually appropriate translation\n"
                        "9. Do not translate Latin\n\n"
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
        timeout_value = int(settings.get('timeout', 360)) 
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
        raise Exception("Unexpected structure from Gemini API")

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
        logger.error(f"Unknown API provider: {api_provider}")
        raise ValueError(f"Unknown API provider: {api_provider}")

def create_chunks(indices: Set[int], subtitles: List[str], settings: Dict, overlap: int = 10) -> List[ChunkInfo]:
    """
    Creates chunks with overlap.

    Args:
        indices: Set of subtitle indices to process.
        subtitles: List of subtitles.
        settings: Dict - settings dictionary containing chunk_size
        overlap: Number of lines to overlap between chunks.

    Returns:
        List of ChunkInfo.
    """
    chunk_size_setting = settings.get('chunk_size', MAX_CHUNK_SIZE) # Get chunk_size from settings
    if chunk_size_setting == 0: # If chunk_size = 0, do not split into chunks
        full_content = '\n\n'.join([f"{i+1}\n{subtitles[i]}" for i in sorted(list(indices))])
        return [ChunkInfo(indices=sorted(list(indices)), content=full_content)]


    chunks = []
    current_chunk = []
    current_indices = []
    current_size = 0
    sorted_indices = sorted(list(indices))  # Convert to list and sort

    for i, idx in enumerate(sorted_indices):
        sub = f"{idx + 1}\n{subtitles[idx]}"
        sub_size = len(sub.encode('utf-8')) + 2

        if current_size + sub_size > chunk_size_setting and current_chunk: # Use chunk_size_setting
            chunks.append(ChunkInfo(
                indices=current_indices.copy(),
                content='\n\n'.join(current_chunk)
            ))
            # Overlap: start the next chunk 'overlap' lines earlier, but not more lines than available
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
    Creates chunks for re-translation of "tails" – skipped lines.
    Logic:
      1) Group skipped lines by proximity (if the difference between them is <= overlap).
      2) For each group, add overlap lines before the start of the group (if possible).
      3) Cut the result by chunk_size (if > 0).
    """

    # If there are no skipped lines - return nothing
    if not failed_indices:
        return []

    chunk_size_setting = settings.get('chunk_size', 1900)
    # sort skipped indices
    sorted_failed = sorted(list(failed_indices))

    # 1. Group skipped lines
    groups = []
    current_group = [sorted_failed[0]]
    for i in range(1, len(sorted_failed)):
        if (sorted_failed[i] - sorted_failed[i - 1]) <= overlap:
            # Continue current group
            current_group.append(sorted_failed[i])
        else:
            # Close current group and start new one
            groups.append(current_group)
            current_group = [sorted_failed[i]]
    groups.append(current_group)  # last section

    # 2. For each group, create final chunks considering overlap lines "before" the group
    tail_chunks: List[ChunkInfo] = []

    for grp in groups:
        start_fail = grp[0]
        end_fail = grp[-1]

        # Calculate from where to start context (overlap lines before the start of the group)
        coverage_start = max(0, start_fail - overlap)
        coverage_end = end_fail  # inclusive

        # Collect all TRUE indices for this coverage
        coverage_indices = list(range(coverage_start, coverage_end + 1))

        # 3. Now need to convert coverage_indices into one or more chunks
        #    depending on chunk_size_setting.
        if chunk_size_setting == 0:
            # No size limit - make one chunk
            chunk_content = []
            for idx in coverage_indices:
                # Format in SRT style (line_number, translation)
                chunk_content.append(f"{idx + 1}\n{subtitles[idx]}")
            content_str = "\n\n".join(chunk_content)
            tail_chunks.append(ChunkInfo(indices=coverage_indices, content=content_str))
        else:
            # Limit by chunk size (utf-8 bytes)
            temp_content = []
            temp_indices = []
            current_size = 0

            for idx in coverage_indices:
                sub_str = f"{idx + 1}\n{subtitles[idx]}"
                sub_size = len(sub_str.encode('utf-8')) + 2  # +2 for '\n\n'
                # If it doesn't fit - finalize the previous chunk
                if current_size + sub_size > chunk_size_setting and temp_content:
                    # Save accumulated
                    chunk_str = "\n\n".join(temp_content)
                    tail_chunks.append(ChunkInfo(indices=temp_indices.copy(), content=chunk_str))
                    # Start new one
                    temp_content = []
                    temp_indices = []
                    current_size = 0

                # Add line
                temp_content.append(sub_str)
                temp_indices.append(idx)
                current_size += sub_size

            # If something is left in temp_content
            if temp_content:
                chunk_str = "\n\n".join(temp_content)
                tail_chunks.append(ChunkInfo(indices=temp_indices, content=chunk_str))

    return tail_chunks

def translate_chunk(chunk: ChunkInfo, settings: Dict, subtitles: List[str], translated_subs: List[str],
                    attempt_type: str = "initial", overlap: int = 10) -> Set[int]:
    """
    Translates a chunk of subtitles, improved handling of API instructions.
    """
    failed_indices = set()
    instruction_prefixes = ("Важно:", "Инструкция:", "Note:", "Important:") # List of instruction prefixes, mixed Russian and English

    try:
        translated_text = translate_text(chunk.content, settings)
        if translated_text is None:
            logger.warning(f"Chunk translation ({attempt_type}) failed (API error/safety block).")
            failed_indices.update(chunk.indices)
            return failed_indices

        translated_blocks = translated_text.strip().split('\n\n')
        processed_indices = set()

        # 1. Preparation: Indices and iterators
        chunk_indices_iter = iter(chunk.indices) # Iterator for chunk indices
        original_idx = next(chunk_indices_iter, None) # Current original index, start with the first one

        translated_block_index = 0 # Index of the current translation block

        logger.debug(f"chunk ({attempt_type}): indices {chunk.indices}")

        # 2. Main loop for processing translation blocks
        while translated_block_index < len(translated_blocks) and original_idx is not None:
            block = translated_blocks[translated_block_index]
            block_lines = block.strip().split('\n')

            if not block_lines: #Empty block
                logger.warning(f"Empty block in translation, skipping.")
                translated_block_index += 1
                continue

            first_line = block_lines[0].strip()
            if not first_line.isdigit(): #First line is not a number
                is_instruction = False
                for prefix in instruction_prefixes: #Check for instruction prefix
                    if first_line.startswith(prefix):
                        is_instruction = True
                        break
                if is_instruction: #It's an instruction
                    logger.warning(f"Instruction block skipped: '{first_line}'.")
                    translated_block_index += 1 #Skip instruction block, original_idx does not change
                    continue #Go to the next translation block (without changing original_idx)
                else: #Not a number and not an instruction - process as translation for current original_idx
                    logger.warning(f"First line is not a number and not an instruction ('{first_line}'), block processed entirely as translation for current original_idx={original_idx}.")
                    #Consider the whole block as translation for the current original_idx
                    translated_text_block = block #Whole block, including the "non-number" in the first line
                    translated_subs[original_idx] = translated_text_block
                    processed_indices.add(original_idx)
                    original_idx = next(chunk_indices_iter, None) #Go to the next original_idx
                    translated_block_index += 1 #Go to the next translation block
                    continue


            translated_idx_from_block = int(first_line) - 1 #Number from translation block

            if translated_idx_from_block == original_idx:
                # 3. Case 1: Perfect index match (1:1)
                translated_text_block = '\n'.join(block_lines[1:]) #Translation - all lines except the first one (with number)
                translated_subs[original_idx] = translated_text_block
                processed_indices.add(original_idx)
                logger.debug(f"  1:1 Match: original_idx={original_idx}, translated_idx={translated_idx_from_block}")

                original_idx = next(chunk_indices_iter, None) #Go to the next original_idx
                translated_block_index += 1 #Go to the next translation block


            elif translated_idx_from_block < original_idx:
                # 4. Case 2: "Extra" block in translation (translation index LESS than original index)
                logger.warning(f"  Extra block in translation (translated_idx={translated_idx_from_block} < original_idx={original_idx}), skipping block.")
                translated_block_index += 1 #Skip "extra" block, but do not change original_idx


            elif translated_idx_from_block > original_idx:
                # 5. Case 3: "Skipped" subtitle in translation (translation index GREATER than original index)
                logger.warning(f"  Skipped subtitle in translation (translated_idx={translated_idx_from_block} > original_idx={original_idx}), filling with original.")
                #Fill translated_subs[original_idx] with original text (or you can use empty string if needed)
                translated_subs[original_idx] = subtitles[original_idx] #Original text
                processed_indices.add(original_idx) #Mark as "processed" (even if not translated)

                original_idx = next(chunk_indices_iter, None) #Go to the next original_idx, do not touch translation block as it "doesn't fit"

            else: #default case - shouldn't happen, but for safety
                logger.error(f"  Unexpected situation during matching: translated_idx={translated_idx_from_block}, original_idx={original_idx}. Skipping block.")
                translated_block_index += 1 #Skip translation block


        # 6. Processing "tail" of original subtitles (if there are unmapped original_idx left)
        while original_idx is not None:
            failed_indices.add(original_idx) #Mark remaining as untranslated
            logger.warning(f"  Unhandled original tail: original_idx={original_idx}")
            original_idx = next(chunk_indices_iter, None)


        failed_indices.update(set(chunk.indices) - processed_indices)


    except Exception as e:
        logger.error(f"Chunk translation error ({attempt_type}): {str(e)}")
        failed_indices.update(chunk.indices)
        logger.exception("Error details:") #Full error traceback


    return failed_indices

def initial_translation(chunks: List[ChunkInfo], settings: Dict, subtitles: List[str], translated_subs: List[str]) -> Set[int]:
    """
    Performs initial translation of subtitles.
    """
    failed_indices = set()
    total_chunks = len(chunks)
    for i, chunk in enumerate(chunks):
        print(f"Translating chunk {i + 1} of {total_chunks}")
        chunk_failed_indices = translate_chunk(chunk, settings, subtitles, translated_subs, "initial")
        failed_indices.update(chunk_failed_indices)
        # Exponential delay + jitter
        delay = BASE_DELAY * (2**1) + random.uniform(0, 0.5) # attempt_number = 1 for the first attempt
        time.sleep(delay)
    return failed_indices

def retry_translation(failed_indices: Set[int],
                      settings: Dict,
                      subtitles: List[str],
                      translated_subs: List[str]) -> Set[int]:
    """
    Performs retry attempts to translate "tails", using create_tail_chunks.
    In each iteration, only skipped lines are translated,
    around which overlap context is added.
    """
    current_failed_indices = failed_indices.copy()
    attempt = 1
    max_attempts = settings.get('max_retries', 5)
    overlap = 10  # can be moved to settings if desired

    while attempt <= max_attempts and current_failed_indices:
        logger.info(f"\nRetry attempt № {attempt} of {max_attempts}")
        logger.info(f"Remaining skipped lines: {len(current_failed_indices)}")

        # Create tail chunks
        tail_chunks = create_tail_chunks(current_failed_indices, subtitles, settings, overlap=overlap)
        logger.info(f"Tail chunks formed: {len(tail_chunks)}")

        iteration_failed_indices = set()

        for i, chunk in enumerate(tail_chunks, start=1):
            print(f"Translating tail chunk {i} of {len(tail_chunks)}")
            # Attempt to translate chunk
            chunk_failed = translate_chunk(chunk, settings, subtitles, translated_subs, f"tail-retry-{attempt}")
            iteration_failed_indices.update(chunk_failed)

            # Small delay between requests
            time.sleep(BASE_DELAY)

        # Now, what is skipped again, will go to the next iteration
        current_failed_indices = iteration_failed_indices.copy()
        attempt += 1

    return current_failed_indices

def process_file(filename: str, settings: Dict):
    logger.info(f"\nProcessing file: {filename}")

    # Determine if translation is needed at all
    need_translation = settings['target_language'].lower() not in ['none', '']
    api_key = None

    if need_translation:
        api_key = get_api_key(settings)
        if not api_key:
            logger.warning(f"API key {settings['api_provider']} not found, skipping translation.")
            return

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        return

    # Determine extension (srt or ass)
    _, ext = os.path.splitext(filename.lower())

    if ext == '.srt':
        # === SRT ===
        # Parse SRT
        timecodes, subtitles = parse_srt(content)
        total_subs = len(subtitles)
        if not total_subs:
            logger.warning(f"File {filename} does not contain subtitles.")
            return

        # Shift time if needed
        if settings['time_shift'] != 0:
            timecodes = [adjust_timecode(tc, settings['time_shift']) for tc in timecodes]

        translated_subs = subtitles.copy()

        if need_translation and api_key:
            # Initial translation in chunks
            initial_chunks = create_chunks(set(range(total_subs)), subtitles, settings)
            logger.info(f"Initial translation (SRT): total {len(initial_chunks)} chunks")
            failed_indices = set()

            # Translate initial chunks
            for i, ch in enumerate(initial_chunks, start=1):
                print(f"Translating chunk {i} of {len(initial_chunks)}")
                chunk_failed = translate_chunk(ch, settings, subtitles, translated_subs, attempt_type="initial")
                failed_indices.update(chunk_failed)
                time.sleep(BASE_DELAY)

            # Retry attempts for "tails"
            final_failed_indices = retry_translation(failed_indices, settings, subtitles, translated_subs)
            logger.info(f"Finally untranslated lines: {len(final_failed_indices)}")

            # For remaining - leave the original
            for idx in final_failed_indices:
                translated_subs[idx] = subtitles[idx]

        # Save result to output/<filename>
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, (tc, text) in enumerate(zip(timecodes, translated_subs), 1):
                    f.write(f"{i}\n{tc}\n{text}\n\n")
            logger.info(f"Saved: {output_path}")
        except Exception as e:
            logger.error(f"Error writing {output_path}: {str(e)}")

    elif ext == '.ass':
        # === ASS ===
        header_lines, events_format_line, dialogues, timecodes, subtitles = parse_ass(content)
        total_subs = len(subtitles)
        if not total_subs:
            logger.warning(f"File {filename} does not contain 'Dialogue:' type lines.")
            return

        # Time shift if needed
        if settings['time_shift'] != 0:
            adjust_timecode_ass(dialogues, settings['time_shift'])
            # Update timecodes (SRT-like "start --> end") so that the chunk-system sees the new time
            for i, d in enumerate(dialogues):
                new_tc = f"{format_time_ass(d['start'])} --> {format_time_ass(d['end'])}"
                timecodes[i] = new_tc

        translated_subs = subtitles.copy()

        if need_translation and api_key:
            # Initial translation in chunks
            initial_chunks = create_chunks(set(range(total_subs)), subtitles, settings)
            logger.info(f"Initial translation (ASS): total {len(initial_chunks)} chunks")
            failed_indices = set()

            # Translate initial chunks
            for i, ch in enumerate(initial_chunks, start=1):
                print(f"Translating chunk {i} of {len(initial_chunks)}")
                chunk_failed = translate_chunk(ch, settings, subtitles, translated_subs, attempt_type="initial")
                failed_indices.update(chunk_failed)
                time.sleep(BASE_DELAY)

            # Retry attempts for "tails"
            final_failed_indices = retry_translation(failed_indices, settings, subtitles, translated_subs)
            logger.info(f"Finally untranslated lines: {len(final_failed_indices)}")

            # For remaining - leave the original
            for idx in final_failed_indices:
                translated_subs[idx] = subtitles[idx]

        # Reassemble final .ass
        output_ass = reconstruct_ass(header_lines, events_format_line, dialogues, translated_subs)

        # Save result
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_ass)
            logger.info(f"Saved: {output_path}")
        except Exception as e:
            logger.error(f"Error writing {output_path}: {str(e)}")

    else:
        logger.warning(f"File {filename} has an unsupported extension. Skipping.")

def main():
    settings = read_settings()

    # Find all files with .srt and .ass extensions
    subtitle_files = glob.glob('*.srt') + glob.glob('*.ass')
    if not subtitle_files:
        logger.warning("No SRT or ASS files found for processing")
        return

    print("\nCurrent settings:")
    print(f"• Time shift: {settings['time_shift']} sec")
    print(f"• Translation language: {settings['target_language']}")
    print(f"• API provider: {settings['api_provider']}")

    if settings['api_provider'] == 'deepseek':
        api_key_status = 'set' if settings['deepseek_api_key'] else 'missing'
        print(f"• DeepSeek API key: {api_key_status}")
        print(f"• DeepSeek Model: {settings['deepseek_model']}")
    elif settings['api_provider'] == 'gemini':
        api_key_status = 'set' if settings['gemini_api_key'] else 'missing'
        print(f"• Gemini API key: {api_key_status}")
        print(f"• Gemini Model: {settings['gemini_model']}")

    print(f"• Retries: {settings['max_retries']}")

    if input("\nPress Enter to start or 1 for settings: ").strip() == '1':
        configure_settings(settings)

    logger.info("Starting file processing...")
    for file in subtitle_files:
        process_file(file, settings)

    logger.info("Processing completed")



if __name__ == "__main__":
    main()
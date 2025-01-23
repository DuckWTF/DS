```markdown
# Subtitle Translator & Time Shifter 🇬🇧/🇷🇺

[English](#features) | [Русский](#features-ru)

![Demo](https://via.placeholder.com/800x400.png?text=Subtitle+Processor+Demo)

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Platform Commands](#platform-commands)
- [Examples](#examples)

---

## Features <a name="features"></a>
- Time shifting (± values supported)
- AI translation via Deepseek API
- Batch processing
- Configuration persistence
- Structure/HTML tags protection

## Features (Русская версия) <a name="features-ru"></a>
- Сдвиг времени (± значения)
- Перевод через Deepseek API
- Пакетная обработка
- Сохранение настроек
- Защита структуры/HTML-тегов

---

## Requirements <a name="requirements"></a>
- Python 3.8+
- [Deepseek API Key](https://platform.deepseek.com/)

---

## Installation <a name="installation"></a>

```bash
git clone https://github.com/DuckWTF/DS.git
cd DS/ai_srt_translator
pip install -r requirements.txt
```

Create `requirements.txt`:
```
requests
```

---

## Getting Started <a name="getting-started"></a>

### English Version:
```bash
python sub.py
```
1. Paste API key when prompted
2. Configure settings via menu

### Русская Версия:
```bash
python sub_ru.py
```
1. Введите API ключ при запросе
2. Настройте параметры через меню

---

## Usage <a name="usage"></a>

### English:
1. Place SRT files in `ai_srt_translator` folder
2. Run:
```bash
python sub.py
```
3. Output in `/ai_srt_translator/output`

### Русский:
1. Поместите SRT-файлы в папку `ai_srt_translator`
2. Запустите:
```bash
python sub_ru.py
```
3. Результат в папке `/ai_srt_translator/output`

---

## Platform Commands <a name="platform-commands"></a>

### Windows:
```cmd
cd ai_srt_translator
:: English
py -3 sub.py

:: Русский
py -3 sub_ru.py
```

### Linux/macOS:
```bash
cd ai_srt_translator
# English
python3 sub.py

# Русский
python3 sub_ru.py
```

---

## Examples <a name="examples"></a>

### English:
```bash
# Shift +5s, no translation
python sub.py -> Set shift=5.0, language=none

# Translate to German
python sub.py -> Set language=German
```

### Русский:
```bash
# Сдвиг +5с, без перевода
python sub_ru.py -> Укажите сдвиг=5.0, язык=none

# Перевод на немецкий
python sub_ru.py -> Укажите язык=German
```
```

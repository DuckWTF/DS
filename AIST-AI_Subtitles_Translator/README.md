<!--- AI SRT Translator README -->
<a name="top"></a>
<div align="center">
  <h1>🤖 AIST Artificial Intelligence Subtitles Translator</h1>
  <p>Automated .srt and .ass subtitle translation and time shifting using Deepseek AI or Gemini AI</p>
  <p> Простой универсальный скрипт для пакетного ИИ перевода и синхронизации времени .srt и .ass субтитров</p>
</div>

## 🔍 Table of Contents

**English**
<a href="#features">Features</a> •
<a href="#requirements">Requirements</a> •
<a href="#installation">Installation</a> •
<a href="#usage">Usage</a> •
<a href="#api">API Key</a> •
<a href="#settings">Settings</a>

**Русский**
<a href="#особенности">Особенности</a> •
<a href="#требования">Требования</a> •
<a href="#установка">Установка</a> •
<a href="#использование">Использование</a> •
<a href="#api-key">API Ключ</a> •
<a href="#настройки">Настройки</a>

<a name="features"></a>
## 🌟 Features
- Batch processing of SRT and ASS files
- Context-aware AI translation via Deepseek API or Gemini API
- Millisecond-accurate time shifting
- Configurable translation settings
- All languages are supported

<a name="requirements"></a>
## ⚙️ System Requirements
- Python 3.7+ (PATH configured)
- Active Deepseek API key or Gemini API key
- `requests` library for Python (for deepseek)

<a name="installation"></a>
## 📦 Installation

### All Platforms
1. Install required library (if not already installed):

   Windows: `pip install requests`
   Linux/macOS: `$ pip install requests`

2. Download script:
   [sub.py](https://github.com/DuckWTF/DS/raw/master/AIST-AI_Subtitles_Translator/sub.py)
   *Right Click → "Save Link As" (Chrome) / "Download Linked File" (Safari)*

3. Extract to empty folder:
   Windows: `C:\AIST-AI_Subtitles_Translator`
   Linux/macOS: `~/AIST-AI_Subtitles_Translator`

<a name="usage"></a>
## 🚀 Usage
1. Place SRT or ASS files in the script folder
2. Open terminal in folder:
   Windows > Press Win + R → type `cmd` → Enter: `cd C:\AIST-AI_Subtitles_Translator`

   Linux/macOS:  `$ cd ~/AIST-AI_Subtitles_Translator`

3. Run script:
   Windows:  `python sub.py`

   Linux/macOS:  `$ python sub.py`

4. To adjust settings (time shift, language, API provider, keys, models, chunk size, retries, timeout), press `1` and Enter. To start processing with current settings, just press Enter.

5. If API key is missing, the script will ask for it.

6. Processed files saved in /output

<a name="api"></a>
## 🔑 API Key Guide

To use the translation feature, you need an API key from either Deepseek or Gemini, depending on your chosen provider.

### Deepseek API Key
1. Register at [Deepseek](https://platform.deepseek.com/signup)
2. Add payment method
3. Generate key in [API Console](https://platform.deepseek.com/api-keys)
4. Copy key starting with `sk-`
5. You can set the `DEEPSEEK_API_KEY` environment variable or enter it when the script prompts you, or configure it in settings.

### Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey) and create a project if you haven't already.
2. In the "API keys" section, create an API key.
3. Copy the API key.
4. You can set the `GEMINI_API_KEY` environment variable or enter it when the script prompts you, or configure it in settings.

<a name="settings"></a>
## ⚙️ Settings

You can configure the script settings by running it and pressing `1` when prompted. The following settings are available:

1.  **Time shift**: Adjust the timecodes of subtitles by a specified number of seconds. Useful for synchronizing subtitles with video.
2.  **Translation language**: Set the target language for translation (e.g., `russian`, `french`, `german`, `none` to disable translation).
3.  **API provider**: Choose between `gemini` and `deepseek` to select which API to use for translation.
4.  **[Deepseek/Gemini] API key**: Set or update your API key for the selected provider. You can also set API keys as environment variables `DEEPSEEK_API_KEY` or `GEMINI_API_KEY`.
5.  **Gemini Model**: Choose a specific Gemini model to use for translation. Available models:
    - `gemini-2.0-flash`
    - `gemini-2.0-flash-lite-preview-02-05`
    - `gemini-1.5-flash`
    - `gemini-1.5-flash-8b`
    - `gemini-1.5-pro`
    - `gemini-2.0-pro-exp-02-05`
    - `gemini-2.0-flash-thinking-exp-01-21` (default)
6.  **DeepSeek Model**: Choose a specific DeepSeek model to use for translation. Available models:
    - `deepseek-chat` (default)
    - `deepseek-reasoner`
7.  **Chunk size**: Set the maximum chunk size in characters for processing text in parts, can be useful for VERY long files. `0` (default) disables chunking and processes the entire subtitle file at once.
8.  **Retries**: Set the number of retry attempts for translation in case of errors.
9.  **Timeout**: Set the timeout in seconds for API requests.

Settings are saved in `settings.txt` file in the script folder and will be loaded on the next run.

---

<a name="особенности"></a>
## 🌟 Особенности
- Пакетная обработка SRT и ASS субтитров
- Контекстно-зависимый перевод через Deepseek AI или Gemini AI
- Пакетная синхронизация времени субтитров
- Настраиваемые параметры перевода 
- Поддержка всех языков, включая клингон и эльфийский

<a name="требования"></a>
## ⚙️ Требования
- Python 3.7+ (в системном PATH)
- API ключ Deepseek или Gemini
- Библиотека `requests` для Python (для использование deepseek)

<a name="установка"></a>
## 📦 Установка

1. Установите (если еще не установлен) **python 3.7+**

   Windows: в терминале (WIN + R → cmd.exe) `winget install Python.Python.3`

   Linux/macOS:  `sudo apt update`
                 `sudo apt install python3`

2. Установите (если еще не установлена) библиотеку **requests**:

   Windows:   `pip install requests`

   Linux/macOS:  `$ pip install requests`

3. Скачайте скрипт:
   [sub_ru.py](https://github.com/DuckWTF/DS/raw/master/AIST-AI_Subtitles_Translator/sub_ru.py)
   *ПКМ → "Сохранить ссылку как" (Chrome) / "Загрузить связанный файл" (Safari)*

4. Сохраните файл в пустую папку, например
   `C:\AIST-AI_Subtitles_Translator`

<a name="использование"></a>
## 🚀 Использование
1. Поместите SRT или ASS файлы в папку со скриптом

2. Откройте папку в терминале:
   Windows:  `cd C:\AIST-AI_Subtitles_Translator`

   Linux/macOS:  `$ cd ~/AIST-AI_Subtitles_Translator`

3. Запустите скрипт:
   Windows:  `python sub_ru.py`

   Linux/macOS:  `$ python sub_ru.py`

4. Для настройки синхронизации таймингов, выбора языка, провайдера API, ключей, моделей, размера блоков, количества попыток и таймаута нажмите `1` и Enter. Для запуска с текущими настройками нажмите Enter.

5. При отсутствии API ключа скрипт запросит его ввод.

6. Результаты в папке /output

<a name="api-key"></a>
## 🔑 Получение API Ключа

Для использования функции перевода необходим API ключ Deepseek или Gemini, в зависимости от выбранного провайдера. **Для использования Gemini API может потребоваться VPN.**

### Deepseek API Ключ
1. Зарегистрируйтесь на [Deepseek](https://platform.deepseek.com/signup)
2. Привяжите платежный метод
3. Создайте ключ в разделе API
4. Скопируйте ключ формата `sk-1abcd234de56fg7hij8klmnopq9rstu0`
5. Вы можете задать ключ как переменную окружения `DEEPSEEK_API_KEY`, ввести при запросе скрипта или настроить через меню настроек.

### Gemini API Ключ
1. Перейдите на [Google AI Studio](https://makersuite.google.com/app/apikey) и создайте проект, если еще не создавали. **Для доступа к Google AI Studio может потребоваться VPN.**
2. В разделе "API keys" создайте API ключ.
3. Скопируйте API ключ.
4. Вы можете задать ключ как переменную окружения `GEMINI_API_KEY`, ввести при запросе скрипта или настроить через меню настроек.

<a name="настройки"></a>
## ⚙️ Настройки

Вы можете настроить параметры скрипта, запустив его и нажав `1` при появлении запроса. Доступны следующие настройки:

1.  **Сдвиг времени**: Корректировка таймкодов субтитров на указанное количество секунд. Полезно для синхронизации субтитров с видео.
2.  **Язык перевода**: Установка языка перевода (например, `russian`, `french`, `german`, `none` для отключения перевода).
3.  **Провайдер API**: Выбор между `gemini` и `deepseek` для определения, какое API использовать для перевода.
4.  **[Deepseek/Gemini] API ключ**: Установка или обновление API ключа для выбранного провайдера. Вы также можете задать API ключи как переменные окружения `DEEPSEEK_API_KEY` или `GEMINI_API_KEY`.
5.  **Модель Gemini**: Выбор конкретной модели Gemini для перевода. Доступные модели:
    - `gemini-2.0-flash`
    - `gemini-2.0-flash-lite-preview-02-05`
    - `gemini-1.5-flash`
    - `gemini-1.5-flash-8b`
    - `gemini-1.5-pro`
    - `gemini-2.0-pro-exp-02-05`
    - `gemini-2.0-flash-thinking-exp-01-21` (по умолчанию)
6.  **Модель DeepSeek**: Выбор конкретной модели DeepSeek для перевода. Доступные модели:
    - `deepseek-chat` (по умолчанию)
    - `deepseek-reasoner`
7.  **Размер чанка**: Установка максимального размера чанка в символах для обработки текста частями. `0` отключает разделение на чанки и обрабатывает весь файл субтитров целиком (не рекомендуется для очень больших файлов). Рекомендуемые значения от 1000 до 100000.
8.  **Повторные попытки**: Установка количества повторных попыток перевода в случае ошибок.
9.  **Таймаут**: Установка таймаута в секундах для запросов к API.

Настройки сохраняются в файле `settings.txt` в папке со скриптом и загружаются при следующем запуске.

---

<div align="center">
  <br><a href="#top">↑ Back to Top ↑</a>
</div>

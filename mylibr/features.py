import re
import asyncio
from aiogram import Bot

def convert_gemini_to_html(text: str) -> str:
    """
    Преобразует Markdown-текст из Google Gemini в HTML для aiogram.
    """
    def sanitize_html(text: str) -> str:
        """
        Функция для очистки HTML-текста от неподдерживаемых тегов и символов.
        """
        # Удаляем все теги, которые не поддерживаются Telegram
        text = re.sub(r'<(?!\/?(b|strong|i|em|u|ins|s|strike|del|code|pre|a href="[^"]*")[^>]*>', '', text)

        # Экранируем специальные символы
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        return text
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<i>\1</i>', text)
    text = re.sub(r'^\* ', '\t• ', text, flags=re.MULTILINE)
    text = re.sub(r'## (.*?)\n', r'<b>\1</b>\n', text)

    # Преобразуем кодовые блоки в инлайн-код
    text = re.sub(r'```(\w+\W*)\n(.*?)```', r'<pre><code class="language-\1">\2</code></pre>', text, flags=re.DOTALL)
    text = re.sub(r'```\n(.*?)\n```', r"<pre>\1</pre>", text, flags=re.DOTALL)
    text = re.sub(r'(?<!`)`([^`].*?[^`])`(?!`)', r'<code>\1</code>', text, flags=re.DOTALL) #белые скобки это значит что апостроф не должен следовать там

    text = re.sub(r'^""', '\"\"', text, flags=re.MULTILINE)
    text = re.sub(r'<(/*)iostream>', r'\<\1iostream>', text, flags=re.IGNORECASE)
    text = re.sub('(?<!\\)!doctype', r'\!doctype', text, flags=re.IGNORECASE)
    text = re.sub(r'(?<!\\)=', r'\=', text)
    text = re.sub(r'<(/*)(b|integer)>', r'\<\1\2>', text, flags=re.IGNORECASE)
    return text

def convert_gemini_to_markdown(text: str) -> str:
    """Преобразует текст, возвращаемый Gemini, в формат MarkdownV2 для использования с aiogram."""

    escape_chars = "*][)(_}{'`~>#+-=|.!"
    text = re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)
    text = re.sub(r'\\\*\\\*(.*?)\\\*\\\*', r'*\1*', text)
    text = re.sub(r'\\_\\_(.*?)\\_\\_', r'_\1_', text)
    text = re.sub(r'^\s*\\\* ', ' • ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\\#\\# (.*?)\n', r'*\1*\n', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\\#\\#\\# (.*?)\n', r'*_\1_*\n', text, flags=re.MULTILINE)
    text = re.sub(r'\\`\\`\\`([a-zA-Z]*\W*)\n(.*?)\\`\\`\\`', r'```\1\n\2\n```', text, flags=re.DOTALL)
    text = re.sub(r'(?<!`)\\`([^`\n]+?)\\`(?!`)', r'`\1`', text)
    text = re.sub(r'```c\\#\n', '```csharp\n', text)
    text = re.sub(r'```c\\\+\\\+\n', '```cpp\n', text)

    return text

async def show_typing(bot: Bot, chat_id: int, event: asyncio.Event, action: str = 'typing', duration: int = 15) -> None:
    """
    Periodically sends a chat action to simulate typing a message.

    :param chat_id: ID of the chat where the action is sent.
    :param action: Type of action to broadcast. Choose one, depending on what the user is about to receive: *typing* for `text messages`_, *upload_photo* for `photos`_, *record_video* or *upload_video* for `videos`_, *record_voice* or *upload_voice* for `voice notes`_, *upload_document* for `general files`_, *choose_sticker* for `stickers`_, *find_location* for `location data`_, *record_video_note* or *upload_video_note* for `video notes`_.
    :param duration: The duration in seconds during which the action will be sent.
    """
    end_time = asyncio.get_event_loop().time() + duration
    while not event.is_set() and asyncio.get_event_loop().time() < end_time:
        await bot.send_chat_action(chat_id, action=action)
        await asyncio.sleep(3)
        print(f'Прошло {asyncio.get_event_loop().time() - (end_time - duration)} секунд')

def decode_language_code(code: str) -> str:
    languages = {
        "ru": "Russian",
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arab",
        "uk": "Ukrainian",
        "pl": "Polish",
        "be": "Belorussian",
        "nl": "Dutch",
        "sv": "Swedish",
        "cs": "Czech",
        "ro": "Romanian",
        "tr": "Turkish",
        "he": "Hebrew",
        "id": "Indonesian",
        "vi": "Vietnamese",
        "th": "Thai",
        "hi": "Hindi",
        "bn": "Bengal",
        "ms": "Malay",
        "my": "Burmese",
        "tl": "Tagalog",
        "fa": "Pradostavsky",
        "gu": "Gujaratis",
        "ta": "Tamil",
        "ur": "Hit",
        "kn": "In Kannada",
        "or": "Oriya",
        "eo": "Esperanto",
        "si": "Sinhalese"
    }

    return languages.get(code, code)
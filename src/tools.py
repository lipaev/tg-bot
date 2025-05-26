import re
import asyncio
from config import config


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
    """Converts the text returned by Gemini and escaped to the MarkdownV2 format for use with aiogram."""

    escape_chars = "*][)(_}{'`~>#+-=|.!"
    text = re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)
    text = re.sub(r'\\\*\\\*(.+?)\\\*\\\*', r'*\1*', text)
    text = re.sub(r'^\s*\\\* ', ' • ', text, flags=re.MULTILINE)
    text = re.sub(r'\\\*(.+?)\\\*', r'*\1*', text)
    text = re.sub(r'^\s*\\#\\# (.*?)\n', r'*__\1__*\n', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\\#\\#\\# (.*?)\n', r'*_\1_*\n', text, flags=re.MULTILINE)
    text = re.sub(r'\\`\\`\\`([a-zA-Z]*\W*)\n(.*?)\\`\\`\\`', r'```\1\n\2\n```', text, flags=re.DOTALL)
    text = re.sub(r'(?<!`)\\`([^`\n]+?)\\`(?!`)', r'`\1`', text)
    text = re.sub(r'^\\>', '>', text, flags=re.MULTILINE)
    text = re.sub(r'```c\\#\n', '```csharp\n', text)
    text = re.sub(r'```c\\\+\\\+\n', '```cpp\n', text)
    #text = re.sub(r'\\_\\_(.*?)\\_\\_', r'_\1_', text)
    text = re.sub(r'\\\[(.+?)\\\]\\\((.+?)\\\)', r'[\1](\2)', text)

    return text

async def lp(chat_id: int, cycles: int = 18, action: str = 'typing') -> None:
    """
    Send a typing action to a chat.

    Args:
        bot: Bot instance.
        chat_id: Id of chat to send the action.
        action: `typing` for text, `upload_photo` for photos, `record_video` or `upload_video` for videos, `record_voice` or `upload_voice` for voice notes, `upload_document` for general files, `choose_sticker` for stickers, `find_location` for location data, `record_video_note` or `upload_video_note` for video. Defaults to 'typing'.
        cycles: Number of cycles of 5 seconds. Defaults to 18.
    """
    for _ in range(cycles):
        await config.bot.send_chat_action(chat_id, action)
        await asyncio.sleep(5)

def help_format(model: str, stream: bool):
    return f"""Ваша модель: {config.model_names[model]}\nСтриминг ответов ИИ: {'✅' if stream else '❎'}\n\n*Команды*:\n/stream - {'Отключает режим стриминга ответов ИИ.' if stream else "Включает режим стриминга ответов ИИ."}\n/clear - забыть историю сообщений"""

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


import re
import asyncio
from config import config
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardMarkup


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

def convert_gemini_to_markdown(text: str, expandable: bool=False) -> str:
    """Converts the text returned by Gemini and escaped to the MarkdownV2 format for use with aiogram.

    Args:
        expandable: If true, then additionally converts a text which has an expandable parts"""
        
    def clear_code(delete_quotes: bool=False):
        def clear(match_obj):
            lang = match_obj.group(1) if match_obj.group(1) else ""
            code = match_obj.group(2)
            if delete_quotes:
                code = re.sub(r"\n>", r"\n", code)
            return f"```{lang}{code.rstrip()}```"
        return clear

    escape_chars = "*][)(_}{`>~#+-=|.!"
    text = re.sub(r'\\', r'\\\\', text)
    text = re.sub(r'([{}])'.format(re.escape(escape_chars)), r'\\\1', text)
    if expandable:
        text = re.sub(r'^\\\*\\\*\\>', '**>', text, flags=re.MULTILINE)
        text = re.sub(r"\n(?!\\\*\\\*>)", "\n>", text, flags=re.MULTILINE) # или (?!\n*\*\*>)
        text = re.sub(r'^> *\\\* ', '> • ', text, flags=re.MULTILINE)
        text = re.sub(r'\\\|\\\|', '||', text, flags=re.MULTILINE)
        text = re.sub(r'> *\\`\\`\\`([a-zA-Z]*\W*)(\n.*?)\\`\\`\\`', clear_code(delete_quotes=True), text, flags=re.DOTALL)
    else:
        text = re.sub(r'\\`\\`\\`([a-zA-Z]*\W*)(\n.*?)\\`\\`\\`', clear_code(), text, flags=re.DOTALL)
    text = re.sub(r'\\\*\\\*(\S.*?)\\\*\\\*', r'*\1*', text)
    text = re.sub(r'^ *\\\* ', ' • ', text, flags=re.MULTILINE)
    text = re.sub(r'\\\*(\S.*?)\\\*', r'*\1*', text)
    text = re.sub(r'(^|>) *(\\#){2,5} (.*?)\n', r'\1*__\3__*\n', text, flags=re.MULTILINE)
    #text = re.sub(r'(^|>) *\\#\\# (.*?)\n', r'\1*__\2__*\n', text, flags=re.MULTILINE)
    text = re.sub(r'(?<!`)\\`([^`\n]+?)\\`(?!`)', r'`\1`', text)
    text = re.sub(r'^\\>', r'>', text, flags=re.MULTILINE)
    text = re.sub(r'```c\\#\n', '```csharp\n', text)
    text = re.sub(r'```c\\\+\\\+\n', '```cpp\n', text)
    text = re.sub(r'\\\[(.+?)\\\]\\\((.+?)\\\)', r'[\1](\2)', text)
    text = re.sub(r"(\\\| (.* \\\|)+\n(\\\| ?:?(\\-)+ ?)+\\\|(\n\\\| (.* \\\|)+)+)", r"```spreadsheet\n\1```", text)

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

def generate_settings_text(user_id: int):
    users = config.users
    l = ['❎', '✅']
    text = (
        f"Ваша модель: {config.model_names[users.model(user_id)]}\n"
        f"Стриминг ответов ИИ: {l[users.stream(user_id)]}\n"
        f"Временный чат: {l[users.temp(user_id)]}"
        )
    return text

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

async def bot_send_message(
    message: Message,
    text: str,
    reply_markup_func: callable = None,
    parse_mode: str = 'MarkdownV2',
    disable_notification: bool = False,
    *,
    user_id: int | None = None,
    ):
    """
    Sends a message to a chat.

    Args:
        message: _description_
        text: _description_
        reply_markup_func: _description_. Defaults to None.
        parse_mode: _description_. Defaults to 'MarkdownV2'.
        disable_notification: . Defaults to False.
        user_id: ID из message не соответствует ID пользователя поэтому передаем его явно. Defaults to None.

    Returns:
        _description_
    """
    try:
        return await config.bot.send_message(
            message.chat.id,
            text,
            parse_mode=parse_mode,
            disable_notification=disable_notification,
            reply_markup=reply_markup_func(user_id) if reply_markup_func else None
        )
    except TelegramBadRequest as e:
        if "can't parse entities" in str(e):
            config.logging.error("This message can't be parsed:\n" + text)
            return await config.bot.send_message(
                message.chat.id,
                text,
                disable_notification=disable_notification,
                reply_markup=reply_markup_func(user_id) if reply_markup_func else None
                )
        config.logging.error(e)
        await config.bot.send_message(chat_id=message.chat.id, text=str(e))
    except Exception as e:
        config.logging.error(f"Error sending message: {e}")

async def try_edit_message(
    message: Message,
    text: str,
    reply_markup_func: callable = None,
    parse_mode: str = 'MarkdownV2',
    *,
    user_id: int | None = None,
    ):
    """
    Edits a message with new text and optional reply markup.

    Args:
        message: The message to edit.
        text: The new text to set for the message.
        reply_markup_func: A function that generates the reply markup. Defaults to None.
        parse_mode: The parse mode to use for the message. Defaults to 'MarkdownV2'.
        user_id: ID из message не соответствует ID пользователя поэтому передаем его явно. Defaults to None.

    Returns:
        None
    """
    try:
        await message.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup_func(user_id) if reply_markup_func else None
            )
    except Exception as e:
        config.logging.error(f"{str(e)}\n{text}")

async def send_any_text(
    message: Message,
    text: str,
    convert: bool,
    user_id: int,
    keyboard: InlineKeyboardMarkup | None=None,
    ):
    """
    Sends any length text.

    Args:
        text: Text that will be converted for MarkdownV2.
        user_id: _description_.
        keyboard: _description_. Defaults to None.
    """
    if convert:
        convertedText = convert_gemini_to_markdown(text)
    else:
        convertedText = text

    while True:
        if len(convertedText) <= 4096:
            message = await bot_send_message(
                message,
                convertedText,
                disable_notification=True,
                reply_markup_func=keyboard,
                user_id=user_id
                )
            break
        else:
            count = convertedText[0:4096].count('```')
            code = convertedText[0:4096].rfind('```')
            cut = convertedText[0:4096].rfind('\n\n')
            if count % 2 == 0 and count > 0:
                if code > cut:
                    cut = code + 3
            elif count > 0:
                cut = code
            elif cut == -1:
                cut = convertedText.rfind('\n', 0, 4096)
            else:
                cut = convertedText.rfind(' ', 0, 4096)
            temporary, convertedText = convertedText[:cut], convertedText[cut:]
            await bot_send_message(
                message,
                temporary,
                disable_notification=True,
                reply_markup_func=keyboard,
                user_id=user_id
            )

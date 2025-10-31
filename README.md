# Telegram Bot

A feature-rich Telegram bot powered by AI.

## Features

- **AI Chat**: Engage in conversations with AI models.
- **Voice-to-Text**: Convert voice messages to text using [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) model.
- **Text-to-Voice**: Generate speech from text using [Gemini](https://ai.google.dev/gemini-api/docs/speech-generation) and [Bing](https://github.com/rany2/edge-tts) TTS models.
- **Text-to-Image**: Create images from text prompts.
- **RAG (Retrieval-Augmented Generation)**: Enhance responses with relevant information from a custom knowledge base.
- **Stream Mode**: Toggle AI response streaming mode.
- **Message History**: Maintain context with message history.
- **Multi-User Support**: Handle multiple users simultaneously.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/tg-bot.git
   cd tg-bot
   ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Configure the environment:
   * Create a `.env` file in the root directory.
   * Add the required environment variables:
    ```
    VEAPIL_BOT=your_telegram_bot_token
    GOOGLE_API_KEY=your_google_api_key
    SQLCONNINFO="dbname=postgres user=postgres password=password"
    HF_API_KEY=your_huggingface_api_key
    ADMIN_ID=your_telegram_user_id
    ```
4. Run the bot:
   ```bash
   python main.py
   ```
## Usage

* Start the bot by sending the `/start` command.
* Use available commands for various tasks:
    * `/info` — Get bot information.
    * `/history` — View message history.
    * `/clear` — Clear message history.
    * `/temp` — Change temporary chat mode.
    * `/stream` — Toggle AI response streaming mode.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
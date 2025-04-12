# Telegram Bot

A feature-rich Telegram bot powered by AI.

## Features

- **AI Chat**: Engage in conversations with AI models.
- **Voice-to-Text**: Convert voice messages to text using Hugging Face models.
- **Image Generation**: Generate images based on text prompts.
- **Pet Photos**: Get random photos of foxes, dogs, or cats.
- **Stream Mode**: Toggle AI response streaming for real-time interaction.

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
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    HF_API_KEY=your_huggingface_api_key
    ```
4. Run the bot:
   ```bash
   python main.py
   ```
## Usage

* Start the bot by sending the `/start` command.
* Use available commands for various tasks:
    * `/help` — Get a list of available commands.
    * `/stream` — Toggle AI response streaming mode.
    * `/clear` — Clear message history.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
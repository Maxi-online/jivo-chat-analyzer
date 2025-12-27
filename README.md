# JivoAnalyticsBot

JivoAnalyticsBot is a small Python tool that downloads a Jivo chat export (JSON), extracts end-user messages, and classifies each message into a **category** and **sentiment** using the OpenAI API.

The classifier uses a generic taxonomy suitable for product/support analytics.

## Features

- Download Jivo export JSON by URL
- Extract end-user messages (filters out agent/bot events)
- AI classification:
  - Category: one of a predefined set (English)
  - Sentiment: `positive` / `negative` / `neutral`
- Save results to:
  - `parsed_jivo.json`
  - `parsed_jivo.csv`

## Requirements

- Python 3.10+ (recommended: 3.11)
- An OpenAI API key

## Installation (Windows)

1. Create and install dependencies:

```bash
install.bat
```

2. Set the `OPENAI_API_KEY` environment variable to your OpenAI API key, then restart the terminal so the variable is available.

## Usage

Run:

```bash
run.bat
```

Then paste the Jivo export JSON URL when prompted, for example:

- `https://files.jivosite.com/export/your_file.json`

After processing finishes, you will get:

- `parsed_jivo.json`
- `parsed_jivo.csv`

## Configuration

- `OPENAI_API_KEY` (required): your OpenAI API key.
- `OPENAI_BASE_URL` (optional): custom gateway/proxy base URL (if you use one).

## Project structure

- `json_to_csv_json.py`: main script (download → parse → classify → save)
- `agent.py`: OpenAI classifier logic
- `run.bat`: run helper for Windows
- `install.bat`: venv + dependencies
- `build_exe.bat` / `JivoAnalyticsBot.spec`: optional PyInstaller build files

## License

MIT. See `LICENSE`.


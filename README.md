# Jivo Chat Analyzer

**An asynchronous Python CLI for converting Jivo chat exports into labelled analytics data.**

The tool downloads a JSON export, filters end-user messages, requests a category
and sentiment label for each message, and writes JSON/CSV results. It is a compact
Applied AI integration with explicit parsing and output boundaries.

## Processing flow

```text
Jivo export URL → JSON parsing → end-user events → bounded async LLM requests → label validation → JSON / CSV
```

- Agent/bot events are separated from end-user messages before classification.
- Requests use a semaphore-based concurrency limit.
- The classifier requests JSON and normalizes category/sentiment values against
  a fixed taxonomy.
- Unknown category or malformed output can fall back to `Other` / `neutral`;
  these defaults should not be mistaken for confident model judgements.
- The output files are `parsed_jivo.json` and `parsed_jivo.csv`.

Classification is message-level. It is not a complete model of conversation
quality, customer intent or business outcomes.

## Setup and use

Use Python 3.10+; Python 3.11 is the existing recommended runtime.

```bash
git clone https://github.com/Maxi-online/jivo-chat-analyzer.git
cd jivo-chat-analyzer
```

On Windows, `install.bat` creates the environment and installs dependencies.
Configure `OPENAI_API_KEY` in the process environment before running the tool.
`OPENAI_BASE_URL` optionally selects a custom gateway. No key belongs in the
repository or a shared example.

```powershell
.\install.bat
.\run.bat
```

Paste a Jivo export URL you are authorized to process when prompted. The
configured model is selected in [agent.py](agent.py). Provider access, rate limits
and request charges apply when the classifier is run.

## Implementation map

| File | Responsibility |
|---|---|
| [json_to_csv_json.py](json_to_csv_json.py) | Download, event filtering, bounded processing and exports |
| [agent.py](agent.py) | Prompt, model request, taxonomy and response normalization |
| [install.bat](install.bat) / [run.bat](run.bat) | Windows setup and entry point |
| [build_exe.bat](build_exe.bat) | Optional PyInstaller packaging |

## Validation scope

There is no published held-out category/sentiment benchmark in this repository.
An evaluation should measure per-category confusion,
invalid-response/fallback rates, throughput and cost on anonymized or synthetic
messages with independently reviewed labels.

## License

[MIT](LICENSE).

## Configuration, privacy and reproducibility

Supply AI-provider credentials and chat-export access through local configuration. Replace names, contacts, customer identifiers and messages with synthetic examples before demonstrations. Do not commit real chat exports or reports derived from them.

Keep credentials in ignored local files or environment variables. Configuration examples contain structure only. Avoid passing secrets on the command line or committing populated `.env` files, private keys, databases or logs.

The [Secret scan](.github/workflows/secret-scan.yml) workflow scans current files and incoming commits with Gitleaks 8.30.1 and redacts matched values. Pattern scanning cannot prove that every possible disclosure is absent. Removing a value from HEAD does not clean older history; see [SECURITY.md](SECURITY.md) for incident handling.

# Week 5 - Day 1: LLM Application Development

This project demonstrates calling OpenAI and Anthropic LLM APIs, comparing their request/response formats, and measuring streaming latency.

## Features

- Loads `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` from `.env` using `python-dotenv`.
- Uses OpenAI Chat Completions and Anthropic Messages APIs.
- Sends the same three questions to both providers.
- Prints model names, answers, and token usage.
- Streams output from both providers and collects received chunks.
- Measures non-streaming total latency, streaming time to first token (TTFT), and total streaming time.
- Keeps partial text if a stream is interrupted.
- Includes a terminal typing effect for streamed demo output.

## Project structure

```text
week5_day1_llm_application/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── outputs/
    └── sample_output.txt
```

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and add your API keys:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEMO_MODE=false
```

**Never commit `.env` or share your API keys.** The `.gitignore` file excludes `.env`.

## Run

```powershell
python main.py
```

### Run without API keys

The project can still be executed for learning and screenshots without paid API access. Keep:

```env
DEMO_MODE=true
```

Demo mode prints clearly labeled sample responses. It does not make API requests and does not produce genuine token counts or latency measurements. For real timing and usage values, add valid keys and set `DEMO_MODE=false`.

## Task 1: SDK format differences

| Feature | OpenAI SDK | Anthropic SDK |
|---|---|---|
| Client | `OpenAI(api_key=...)` | `Anthropic(api_key=...)` |
| API method | `client.chat.completions.create(...)` | `client.messages.create(...)` |
| Model input | `model` | `model` |
| Conversation | `messages=[{"role": "user", "content": prompt}]` | `messages=[{"role": "user", "content": prompt}]` |
| System instruction | Usually a `{"role": "system", ...}` message | Separate `system="..."` argument |
| Output text | `response.choices[0].message.content` | Text blocks in `response.content` |
| Usage fields | `prompt_tokens`, `completion_tokens`, `total_tokens` | `input_tokens`, `output_tokens` |

## Task 2: Streaming

- OpenAI streaming uses `stream=True`; text arrives in `chunk.choices[0].delta.content`.
- Anthropic streaming uses `client.messages.stream(...)` and its `stream.text_stream` helper.
- Time to first token (TTFT) measures the time from starting the request until the first text chunk arrives.
- Total streaming time measures until the stream finishes.
- The program compares collected streaming text with the corresponding non-streaming response.

**Note:** Exact text equality is not guaranteed for all model/API settings because generation can be nondeterministic. The script reports the comparison result instead of assuming it will match.

## Why streaming improves user experience (4 lines)

1. Users see the first part of an answer without waiting for the entire response.
2. Early feedback makes the application feel faster and more responsive.
3. Users can begin reading or acting while the model generates the remaining text.
4. Streaming supports live interfaces such as chat applications and terminal assistants.

## Notes

- The example model names are configurable constants near the top of `main.py`.
- API model availability and pricing depend on your provider account.
- Demo output is illustrative only; replace it with a live run for genuine measurements.

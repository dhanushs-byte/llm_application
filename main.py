"""
Week 5 - Day 1: LLM Application Development
Runs with real API keys, or in demo mode without keys.
"""
import os
import sys
import time
import itertools
import threading
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

QUESTIONS = [
    "What is machine learning? Explain briefly.",
    "What is the difference between AI and generative AI?",
    "Give three practical uses of large language models.",
]

OPENAI_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-3-5-haiku-latest"

# Sample responses are only used in DEMO_MODE or when credentials are absent.
DEMO_ANSWERS = {
    QUESTIONS[0]: "Machine learning is a branch of AI in which systems learn patterns from data and use them to make predictions or decisions.",
    QUESTIONS[1]: "AI is the broader field of building systems that perform tasks requiring intelligence. Generative AI is a subset that creates new content such as text, images, audio, or code.",
    QUESTIONS[2]: "Three uses are: answering customer questions, summarizing documents, and helping developers write or explain code.",
}

def require_sdk():
    try:
        from openai import OpenAI
        from anthropic import Anthropic
        return OpenAI, Anthropic
    except ImportError as exc:
        raise SystemExit(
            "Missing SDK. Run: pip install -r requirements.txt"
        ) from exc

def demo_answer(prompt, system=None):
    return DEMO_ANSWERS.get(prompt, "This is a sample response generated in demo mode.")

def ask_openai(prompt):
    """Non-streaming OpenAI Chat Completions call."""
    if DEMO_MODE or not OPENAI_API_KEY:
        answer = demo_answer(prompt)
        return {"provider": "OpenAI", "model": OPENAI_MODEL, "text": answer,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "demo": True}

    OpenAI, _ = require_sdk()
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300,
    )
    return {
        "provider": "OpenAI",
        "model": response.model,
        "text": response.choices[0].message.content or "",
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        },
        "demo": False,
    }

def ask_claude(prompt, system="You are a helpful assistant."):
    """Non-streaming Anthropic Messages API call."""
    if DEMO_MODE or not ANTHROPIC_API_KEY:
        answer = demo_answer(prompt, system)
        return {"provider": "Anthropic", "model": ANTHROPIC_MODEL, "text": answer,
                "usage": {"input_tokens": 0, "output_tokens": 0}, "demo": True}

    _, Anthropic = require_sdk()
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
        system=system,
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return {
        "provider": "Anthropic",
        "model": response.model,
        "text": text,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
        "demo": False,
    }

def spinner(message, stop_event):
    for symbol in itertools.cycle("|/-\\"):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r{message} {symbol}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(message) + 4) + "\r")

def typing_print(text, delay=0.008):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()

def stream_openai(prompt):
    """Stream OpenAI deltas and retain partial text if the stream is interrupted."""
    if DEMO_MODE or not OPENAI_API_KEY:
        answer = demo_answer(prompt)
        first_token = None
        chunks = []
        for word in answer.split(" "):
            if first_token is None:
                first_token = time.perf_counter()
            chunk = word + " "
            chunks.append(chunk)
            print(chunk, end="", flush=True)
            time.sleep(0.025)
        print()
        return {"text": "".join(chunks).strip(), "first_token_s": None,
                "total_s": None, "usage": None, "demo": True}

    OpenAI, _ = require_sdk()
    client = OpenAI(api_key=OPENAI_API_KEY)
    started = time.perf_counter()
    first_token_s = None
    chunks = []
    usage = None
    try:
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    if first_token_s is None:
                        first_token_s = time.perf_counter() - started
                    chunks.append(content)
                    print(content, end="", flush=True)
            if getattr(chunk, "usage", None):
                usage = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens,
                }
    except Exception as exc:
        print(f"\n[Stream interrupted: {exc}]")
    total_s = time.perf_counter() - started
    print()
    return {"text": "".join(chunks), "first_token_s": first_token_s,
            "total_s": total_s, "usage": usage, "demo": False}

def stream_claude(prompt, system="You are a helpful assistant."):
    """Use Anthropic's messages.stream() helper and preserve partial output."""
    if DEMO_MODE or not ANTHROPIC_API_KEY:
        answer = demo_answer(prompt, system)
        chunks = []
        for word in answer.split(" "):
            chunks.append(word + " ")
            print(word + " ", end="", flush=True)
            time.sleep(0.025)
        print()
        return {"text": "".join(chunks).strip(), "first_token_s": None,
                "total_s": None, "usage": None, "demo": True}

    _, Anthropic = require_sdk()
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    started = time.perf_counter()
    first_token_s = None
    chunks = []
    usage = None
    try:
        with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
            system=system,
        ) as stream:
            for text in stream.text_stream:
                if text:
                    if first_token_s is None:
                        first_token_s = time.perf_counter() - started
                    chunks.append(text)
                    print(text, end="", flush=True)
            final_message = stream.get_final_message()
            usage = {
                "input_tokens": final_message.usage.input_tokens,
                "output_tokens": final_message.usage.output_tokens,
            }
    except Exception as exc:
        print(f"\n[Stream interrupted: {exc}]")
    total_s = time.perf_counter() - started
    print()
    return {"text": "".join(chunks), "first_token_s": first_token_s,
            "total_s": total_s, "usage": usage, "demo": False}

def print_result(result):
    print(f"Provider: {result['provider']}")
    print(f"Model: {result['model']}")
    print(f"Answer: {result['text']}")
    print(f"Token usage: {result['usage']}")
    if result["demo"]:
        print("Note: Demo response; no API request was made.")

def task1():
    print("\n========== TASK 1: SDK CALLS ==========")
    for index, question in enumerate(QUESTIONS, start=1):
        print(f"\n--- Question {index}: {question} ---")
        print_result(ask_openai(question))
        print()
        print_result(ask_claude(question))

def task2():
    print("\n========== TASK 2: STREAMING ==========")
    prompt = QUESTIONS[0]

    for provider, nonstream_fn, stream_fn in [
        ("OpenAI", ask_openai, stream_openai),
        ("Anthropic", ask_claude, stream_claude),
    ]:
        print(f"\n--- {provider} ---")
        start = time.perf_counter()
        nonstream = nonstream_fn(prompt)
        nonstream_total = time.perf_counter() - start
        print(f"Non-streaming completed in {nonstream_total:.3f}s")
        print(f"Non-streaming first output latency: {nonstream_total:.3f}s")

        print("Streaming response: ", end="", flush=True)
        streamed = stream_fn(prompt)
        if streamed["demo"]:
            print("Demo mode does not measure real API latency.")
        else:
            print(f"Time to first token: {streamed['first_token_s']:.3f}s"
                  if streamed["first_token_s"] is not None else "No token received.")
            print(f"Total streaming time: {streamed['total_s']:.3f}s")

        print("Collected stream matches non-stream response:",
              streamed["text"].strip() == nonstream["text"].strip())

def main():
    print("Week 5 - Day 1 | LLM Application Development")
    if DEMO_MODE:
        print("Running in DEMO_MODE: sample responses; no API keys required.")
    else:
        missing = []
        if not OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        if missing:
            print("Missing " + ", ".join(missing) + ". Those providers will use demo responses.")
            print("Add keys to .env and set DEMO_MODE=false for live API calls.")
    task1()
    task2()

if __name__ == "__main__":
    main()

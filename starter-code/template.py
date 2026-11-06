"""Day 01: five tasks and three bonuses. Run this file with --mode compare or chat."""
import argparse
import os
from pathlib import Path
import time
from typing import Any, Callable
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
OPENAI_MODEL = "gpt-4o"
OPENAI_MINI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = os.getenv("GEMINI_CHAT_MODEL") or "gemini-3.5-flash-lite"
GEMINI_CHAT_MODEL = GEMINI_MODEL
ANTHROPIC_MODEL = "claude-3-5-haiku"

# Paid text prices in USD per 1M tokens, checked 2026-11-06.
# https://developers.openai.com/api/docs/models/gpt-4o
# https://developers.openai.com/api/docs/models/gpt-4o-mini
# https://deepmind.google/models/model-cards/gemini-3-5-flash-lite/
LIVE_PRICING_1M_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
}
# Historical exercise models/rates ONLY for the original lab/test contract.
# CLI compare/batch use compare_live_models and LIVE_PRICING_1M_TOKENS instead.
LAB_GEMINI_MODEL = "gemini-2.5-flash"
PRICING_1M_TOKENS = {
    "gpt-4o": {"input": 5.00, "output": 20.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.300},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
}


# Task 1
def call_openai(prompt: str, model: str = OPENAI_MODEL, temperature: float = 0.7,
                top_p: float = 0.9, max_tokens: int = 256) -> tuple[str, float, dict]:
    """Return text, API latency in seconds, and token usage."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=20.0, max_retries=0)
    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=temperature, top_p=top_p, max_tokens=max_tokens,
    )
    latency = time.perf_counter() - start
    usage = response.usage
    return response.choices[0].message.content or "", latency, {
        "input_tokens": (usage.prompt_tokens or 0) if usage else 0,
        "output_tokens": (usage.completion_tokens or 0) if usage else 0,
    }


# Task 2 - Gemini 3.5 Flash Lite
def call_gemini(prompt: str, model: str = GEMINI_MODEL, temperature: float = 0.7,
                top_p: float = 0.9, max_tokens: int = 256) -> tuple[str, float, dict]:
    """Use the configured model with a 20-second HTTP timeout and no retry."""
    from google import genai
    from google.genai import types
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
        http_options=types.HttpOptions(timeout=20_000, retry_options=types.HttpRetryOptions(attempts=1)),
    )
    start = time.perf_counter()
    response = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature, top_p=top_p, max_output_tokens=max_tokens),
    )
    latency = time.perf_counter() - start
    usage = response.usage_metadata
    return response.text or "", latency, {
        "input_tokens": (usage.prompt_token_count or 0) if usage else 0,
        "output_tokens": (usage.candidates_token_count or 0) if usage else 0,
    }


# Task 3
def call_anthropic(prompt: str, model: str = ANTHROPIC_MODEL, temperature: float = 0.7,
                   top_p: float = 0.9, max_tokens: int = 256) -> tuple[str, float, dict]:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), timeout=20.0, max_retries=0)
    start = time.perf_counter()
    response = client.messages.create(
        model=model, messages=[{"role": "user", "content": prompt}],
        temperature=temperature, top_p=top_p, max_tokens=max_tokens,
    )
    latency = time.perf_counter() - start
    text = "".join(p.text for p in response.content if isinstance(getattr(p, "text", None), str))
    usage = response.usage
    return text, latency, {
        "input_tokens": (usage.input_tokens or 0) if usage else 0,
        "output_tokens": (usage.output_tokens or 0) if usage else 0,
    }


def _comparison(prompt: str, models: tuple, prices: dict, announce: bool = False) -> dict:
    for _, model, _ in models:
        if model not in prices:
            raise ValueError(f"Add pricing for {model} before comparing.")
    results = {}
    for key, model, call in models:
        if announce:
            print(f"Calling {model}...", flush=True)
        text, latency, usage = call(prompt, model=model)
        rates = prices[model]
        results[key] = {
            "model": model, "response": text, "latency": latency,
            "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"],
            "cost": (usage["input_tokens"] * rates["input"] + usage["output_tokens"] * rates["output"]) / 1_000_000,
        }
    return results


# Task 4 - historical exercise contract for the original mocked tests.
def compare_models(prompt: str) -> dict:
    """Original lab models/rates. Use compare_live_models for real API calls."""
    return _comparison(prompt, (
        ("gpt4o", OPENAI_MODEL, call_openai),
        ("gpt4o_mini", OPENAI_MINI_MODEL, call_openai),
        ("gemini_flash", LAB_GEMINI_MODEL, call_gemini),
    ), PRICING_1M_TOKENS)


def compare_live_models(prompt: str) -> dict:
    """Live Gemini 3.5 Flash Lite comparison with estimated paid text costs."""
    return _comparison(prompt, (
        ("gpt4o", OPENAI_MODEL, call_openai),
        ("gpt4o_mini", OPENAI_MINI_MODEL, call_openai),
        ("gemini_flash", GEMINI_MODEL, call_gemini),
    ), LIVE_PRICING_1M_TOKENS, announce=True)


# Task 5
def streaming_chatbot() -> None:
    """Stream replies and retain the last three completed conversation turns."""
    from google import genai
    from google.genai import types
    history = []
    client = None
    print(f"Gemini chatbot ({GEMINI_MODEL}) - type 'quit' or 'exit' to end.")
    print("HTTP timeout: 20s. Press Ctrl+C to stop while waiting.")
    try:
        while True:
            try:
                prompt = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if prompt.lower() in {"quit", "exit"}:
                break
            if not prompt:
                continue
            user_message = types.Content(role="user", parts=[types.Part(text=prompt)])
            try:
                if client is None:
                    client = genai.Client(
                        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
                        http_options=types.HttpOptions(timeout=20_000, retry_options=types.HttpRetryOptions(attempts=1)),
                    )
                print("Waiting for Gemini...", flush=True)
                print("Gemini: ", end="", flush=True)
                chunks = []
                for chunk in client.models.generate_content_stream(model=GEMINI_MODEL, contents=history + [user_message]):
                    if chunk.text:
                        print(chunk.text, end="", flush=True)
                        chunks.append(chunk.text)
                print()
            except KeyboardInterrupt:
                print()
                break
            except Exception as exc:
                if isinstance(exc, TimeoutError) or "timeout" in type(exc).__name__.lower():
                    print("\nGemini timed out (20s HTTP timeout). Please try again.")
                else:
                    print(f"\nAPI error: {exc}")
                continue
            if chunks:
                history.extend([user_message, types.Content(role="model", parts=[types.Part(text="".join(chunks))])])
                history = history[-6:]
            else:
                print("Gemini returned no text. Please try again.")
    finally:
        if client is not None:
            client.close()


# Bonus A
def retry_with_backoff(fn: Callable[[], Any], max_retries: int = 3, base_delay: float = 0.1) -> Any:
    """Retry after exponential delays and re-raise the final exception."""
    if max_retries < 0 or base_delay < 0:
        raise ValueError("max_retries and base_delay must be non-negative")
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception:
            if attempt == max_retries:
                raise
            time.sleep(base_delay * 2 ** attempt)


# Bonus B - original exercise function
def batch_compare(prompts: list[str]) -> list[dict]:
    return [{**compare_models(prompt), "prompt": prompt} for prompt in prompts]


# Bonus C
def format_comparison_table(results: list[dict]) -> str:
    def cell(value: str, limit: int | None = None) -> str:
        value = " ".join(value.split())
        if limit is not None and len(value) > limit:
            value = value[:limit - 3] + "..."
        return value.replace("|", "&#124;")
    rows = [
        "| Prompt | Model | Response (truncated) | Latency | Tokens (In/Out) | Cost (USD) |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    labels = {"gpt4o": "GPT-4o", "gpt4o_mini": "GPT-4o-Mini", "gemini_flash": "Gemini-Flash"}
    for result in results:
        for key, label in labels.items():
            stats = result[key]
            cost = "N/A" if stats["cost"] is None else f"${stats['cost']:.8f}"
            rows.append(
                f"| {cell(result['prompt'])} | {cell(stats.get('model', label))} | {cell(stats['response'], 50)} "
                f"| {stats['latency']:.3f}s | {stats['input_tokens']}/{stats['output_tokens']} | {cost} |"
            )
    return "\n".join(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 01 - LLM API Foundation")
    parser.add_argument("--mode", choices=["chat", "all", "compare", "batch", "openai", "gemini", "anthropic"], default="chat")
    parser.add_argument("--prompt", default="Hãy giải thích sự khác biệt giữa temperature và top_p bằng tiếng Việt ngắn gọn trong 2 câu.")
    args = parser.parse_args()
    if args.mode != "chat":
        try:
            if args.mode in {"all", "compare", "batch"}:
                print("Estimated paid text costs (USD); free-tier/cache discounts excluded.")
                prompts = [args.prompt]
                if args.mode == "batch":
                    prompts += ["Token trong LLM là gì?", "Streaming giúp ích gì cho chatbot?"]
                results = [{**compare_live_models(p), "prompt": p} for p in prompts]
                print(format_comparison_table(results))
                if args.mode != "batch":
                    for key in ("gpt4o", "gpt4o_mini", "gemini_flash"):
                        stats = results[0][key]
                        print(f"\n[{stats['model']}]\n{stats['response']}")
            else:
                call = {"openai": call_openai, "gemini": call_gemini, "anthropic": call_anthropic}[args.mode]
                text, latency, usage = call(args.prompt)
                print(text)
                print(f"Latency: {latency:.3f}s | Tokens: {usage}")
        except Exception as exc:
            print(f"API call failed: {exc}")
            if args.mode != "all":
                raise SystemExit(1)
    if args.mode in {"all", "chat"}:
        streaming_chatbot()

from __future__ import annotations

import json
import asyncio
import sys
from collections.abc import AsyncIterator

import httpx


async def stream_openai_compatible(
    *,
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    temperature: float,
    timeout_s: float = 60.0,
) -> AsyncIterator[str]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    max_attempts = 5  # Increase attempts for power free tier limits
    for attempt in range(max_attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    # Handle rate limiting (429) with VERY aggressive exponential backoff
                    if resp.status_code == 429:
                        # Wait times: 2, 5, 10, 20, 40+ seconds
                        wait_time = (2 ** (attempt + 1))  # 2, 4, 8, 16, 32 seconds
                        if attempt < max_attempts - 1:
                            print(f"\n[Groq:429] Rate limited! Waiting {wait_time}s before retry {attempt + 1}/{max_attempts}...", flush=True)
                            # Exit the context managers and retry
                            await asyncio.sleep(wait_time)
                            raise httpx.HTTPStatusError(
                                "Rate limited - will retry",
                                request=resp.request,
                                response=resp
                            )
                        else:
                            print(f"[Groq:429] Rate limited after {max_attempts} attempts - giving up", flush=True)
                            raise httpx.HTTPStatusError(
                                f"Rate limited (429) after {max_attempts} attempts. The Groq free tier has strict limits. Please try again in 30+ seconds.",
                                request=resp.request,
                                response=resp
                            )
                    
                    resp.raise_for_status()
                    
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        data = line[len("data:") :].strip()
                        if data == "[DONE]":
                            return
                        try:
                            event = json.loads(data)
                            delta = event.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                        except Exception:
                            continue
                    
                    # If we get here, streaming succeeded - exit retry loop
                    print("[Groq] Streaming completed successfully", flush=True)
                    return
        except httpx.HTTPStatusError as e:
            # Check if this is a retryable 429 error
            if hasattr(e, 'response') and e.response.status_code == 429 and attempt < max_attempts - 1:
                print(f"[Groq:429] Caught 429 exception, will retry... (attempt {attempt + 1}/{max_attempts})", flush=True)
                continue
            # Re-raise for last attempt, non-429 errors, or retry limit
            print(f"[Groq] HTTPStatusError raised: {e}", flush=True)
            raise
        except Exception as e:
            print(f"[Groq] Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {str(e)}", flush=True)
            # For other exceptions, don't retry - let them propagate
            raise

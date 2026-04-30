from __future__ import annotations

import importlib
import inspect
from typing import Any

from backend.config import get_settings


class LangfuseClient:
    def __init__(self) -> None:
        self._enabled = False
        self._client: Any | None = None
        self._error: Exception | None = None

        settings = get_settings()
        public_key = settings.langfuse_public_key
        secret_key = settings.langfuse_secret_key
        base_url = settings.langfuse_base_url or settings.langfuse_host

        print(f"🔍 [LANGFUSE] Initialization check:")
        print(f"   Public key: {'✓' if public_key else '✗'}")
        print(f"   Secret key: {'✓' if secret_key else '✗'}")
        print(f"   Base URL: {base_url if base_url else '✗'}")

        if not (public_key and secret_key and base_url):
            print(f"❌ [LANGFUSE] Missing credentials - tracing disabled")
            return

        try:
            module = importlib.import_module("langfuse")
            Langfuse = getattr(module, "Langfuse", None)
            if not Langfuse:
                print(f"❌ [LANGFUSE] Langfuse class not found in module")
                return

            init_kwargs: dict[str, str] = {}
            signature = getattr(Langfuse, "__init__", None)
            if signature is not None:
                params = list(inspect.signature(signature).parameters)
            else:
                params = []

            init_kwargs["public_key"] = public_key
            init_kwargs["secret_key"] = secret_key
            if "base_url" in params:
                init_kwargs["base_url"] = base_url
            elif "host" in params:
                init_kwargs["host"] = base_url
            elif "baseUrl" in params:
                init_kwargs["baseUrl"] = base_url
            else:
                init_kwargs["host"] = base_url

            self._client = Langfuse(**init_kwargs)
            self._enabled = True
            print(f"✅ [LANGFUSE] Successfully initialized with base_url={base_url}")
        except Exception as exc:
            self._error = exc
            self._enabled = False
            print(f"❌ [LANGFUSE] Failed to initialize: {type(exc).__name__}: {exc}")

    @property
    def enabled(self) -> bool:
        if not self._enabled and self._error:
            print(f"⚠️ [LANGFUSE] Client disabled - Error: {self._error}")
        return self._enabled

    @property
    def client(self) -> Any | None:
        return self._client


langfuse_client = LangfuseClient()

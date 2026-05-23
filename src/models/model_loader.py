"""Centralized model loader for RAG and imaging components.

Provides lazy-loaded singleton access to:
- Multilingual embedding model
- Cross-encoder reranker
- Local LLM model/tokenizer
- Imaging backbone model
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, List, Optional, Tuple

import torch

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
except Exception:  # pragma: no cover - optional dependency in some environments
    SentenceTransformer = None
    CrossEncoder = None

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception:  # pragma: no cover - optional dependency in some environments
    AutoModelForCausalLM = None
    AutoTokenizer = None

try:
    from torchvision import models
except Exception:  # pragma: no cover - optional dependency in some environments
    models = None

try:
    import requests
except Exception:  # pragma: no cover - optional dependency in some environments
    requests = None


class ModelLoader:
    """Singleton model manager with lazy loading and safe fallbacks."""

    _instance: Optional["ModelLoader"] = None

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.embedding_model_name = self._cfg(
            "EMBEDDING_MODEL", os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/biomed_roberta_base")
        )
        self.embedding_fallback_model_name = self._cfg(
            "EMBEDDING_FALLBACK_MODEL", os.getenv("EMBEDDING_FALLBACK_MODEL", "intfloat/multilingual-e5-base")
        )
        self.rerank_model_name = self._cfg(
            "RERANK_MODEL", os.getenv("RERANKER_MODEL_NAME", "cross-encoder/biomed-roberta-base")
        )
        self.llm_model_name = self._cfg("LLM_MODEL", os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"))
        self.llm_fallback_model_name = "mistralai/Mistral-7B-Instruct-v0.2"

        self.use_embedding_api = self._cfg_bool("USE_EMBEDDING_API", False)
        self.use_rerank_api = self._cfg_bool("USE_RERANK_API", False)
        self.use_llm_api = self._cfg_bool("USE_LLM_API", False)
        self.use_imaging_api = self._cfg_bool("USE_IMAGING_API", False)
        self.llm_enabled = self._cfg_bool("LLM_ENABLED", True)

        self.hf_token = self._cfg("HUGGINGFACE_TOKEN", "")
        self.openai_api_key = self._cfg("OPENAI_API_KEY", "")
        self.openai_base_url = self._cfg("OPENAI_BASE_URL", "")
        self.openrouter_api_key = self._cfg("OPENROUTER_API_KEY", "")
        self.gemini_api_key = self._cfg("GEMINI_API_KEY", "")
        self.openrouter_site_url = self._cfg("OPENROUTER_SITE_URL", "")
        self.openrouter_app_name = self._cfg("OPENROUTER_APP_NAME", "Healthcare AI Assistant")
        self.embedding_api_endpoint = self._cfg("EMBEDDING_API_ENDPOINT", "")
        self.rerank_api_endpoint = self._cfg("RERANK_API_ENDPOINT", "")
        self.llm_api_endpoint = self._cfg("LLM_API_ENDPOINT", "")
        self.llm_api_models = self._parse_models_csv(self._cfg("LLM_API_MODELS", ""))
        self.imaging_api_endpoint = self._cfg("IMAGING_API_ENDPOINT", "")
        self.imaging_explain_api_endpoint = self._cfg("IMAGING_EXPLAIN_API_ENDPOINT", "")
        self.imaging_api_key = self._cfg("IMAGING_API_KEY", "")

        self._embedding_model = None
        self._embedding_fallback_model = None
        self._reranker = None
        self._llm_model = None
        self._llm_tokenizer = None
        self._llm_loaded_name = None
        self._imaging_model = None
        
        # API latency tracking (in milliseconds)
        self.last_embedding_api_ms = 0.0
        self.last_rerank_api_ms = 0.0
        self.last_llm_api_ms = 0.0
        self.last_imaging_api_ms = 0.0

        logger.info("ModelLoader initialized on device=%s", self.device)
        logger.debug("Embeddings Mode: %s", self._mode_label(self.use_embedding_api))
        logger.debug("Reranker Mode: %s", self._mode_label(self.use_rerank_api))
        logger.debug("LLM Mode: %s", self._mode_label(self.use_llm_api))

    @staticmethod
    def _mode_label(use_api: bool) -> str:
        """Return standardized mode label for logs."""
        return "API" if bool(use_api) else "LOCAL"

    @staticmethod
    def _parse_models_csv(value: str) -> List[str]:
        """Parse comma-separated model names into a clean list."""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item and item.strip()]

    @classmethod
    def instance(cls) -> "ModelLoader":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _cfg(self, key: str, default: str) -> str:
        """Read config value from settings (if available), then environment."""
        try:
            from src.utils.config import settings

            value = getattr(settings, key, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        except Exception:
            pass

        env_value = os.getenv(key)
        if isinstance(env_value, str) and env_value.strip():
            return env_value.strip()
        return default

    def _cfg_bool(self, key: str, default: bool) -> bool:
        """Read boolean config values from settings/env."""
        try:
            from src.utils.config import settings

            value = getattr(settings, key, None)
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() == "true"
        except Exception:
            pass

        env_value = os.getenv(key)
        if env_value is None:
            return default
        return str(env_value).strip().lower() == "true"

    def _hf_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        return headers

    def _openai_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.openai_api_key:
            headers["Authorization"] = f"Bearer {self.openai_api_key}"
        return headers

    def _openrouter_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.openrouter_api_key:
            headers["Authorization"] = f"Bearer {self.openrouter_api_key}"
        if self.openrouter_site_url:
            headers["HTTP-Referer"] = self.openrouter_site_url
        if self.openrouter_app_name:
            headers["X-Title"] = self.openrouter_app_name
        return headers

    @staticmethod
    def _extract_chat_content(payload: Any) -> Optional[str]:
        """Extract assistant content from OpenAI-compatible chat response payload."""
        try:
            choices = payload.get("choices") if isinstance(payload, dict) else None
            if not choices:
                return None
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content.strip() or None
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(str(part.get("text", "")))
                merged = "\n".join([x for x in text_parts if x.strip()]).strip()
                return merged or None
        except Exception:
            return None
        return None

    @staticmethod
    def _extract_gemini_content(payload: Any) -> Optional[str]:
        """Extract assistant text from Google Gemini generateContent response."""
        try:
            candidates = payload.get("candidates") if isinstance(payload, dict) else None
            if not candidates:
                return None
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            texts = []
            for part in parts:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])
            merged = "\n".join([x for x in texts if x.strip()]).strip()
            return merged or None
        except Exception:
            return None

    def _imaging_headers(self) -> dict:
        headers = {}
        if self.imaging_api_key:
            headers["Authorization"] = f"Bearer {self.imaging_api_key}"
        return headers

    def get_embedding_model(self):
        """Get multilingual embedding model (lazy-loaded)."""
        if self._embedding_model is not None:
            return self._embedding_model

        if SentenceTransformer is None:
            logger.error("sentence-transformers is not available; embeddings disabled")
            return None

        try:
            logger.info("Loading embedding model: %s", self.embedding_model_name)
            self._embedding_model = SentenceTransformer(
                self.embedding_model_name,
                device=str(self.device),
            )
            logger.info(
                "Embedding model loaded (dim=%s)",
                self._embedding_model.get_sentence_embedding_dimension(),
            )
        except Exception as exc:
            logger.error("Failed to load embedding model %s: %s", self.embedding_model_name, exc)
            self._embedding_model = None

        return self._embedding_model

    def get_fallback_embedding_model(self):
        """Get multilingual fallback embedding model (lazy-loaded)."""
        if self._embedding_fallback_model is not None:
            return self._embedding_fallback_model

        if SentenceTransformer is None:
            logger.error("sentence-transformers is not available; fallback embeddings disabled")
            return None

        try:
            logger.info("Loading fallback embedding model: %s", self.embedding_fallback_model_name)
            self._embedding_fallback_model = SentenceTransformer(
                self.embedding_fallback_model_name,
                device=str(self.device),
            )
            logger.info(
                "Fallback embedding model loaded (dim=%s)",
                self._embedding_fallback_model.get_sentence_embedding_dimension(),
            )
        except Exception as exc:
            logger.error("Failed to load fallback embedding model %s: %s", self.embedding_fallback_model_name, exc)
            self._embedding_fallback_model = None

        return self._embedding_fallback_model

    @staticmethod
    def _is_english_language(language: Optional[str]) -> bool:
        if not language:
            return True
        code = str(language).strip().lower()
        return code.startswith("en")

    def get_reranker(self):
        """Get cross-encoder reranker model (lazy-loaded)."""
        if self._reranker is not None:
            return self._reranker

        if CrossEncoder is None:
            logger.error("sentence-transformers is not available; reranker disabled")
            return None

        try:
            logger.info("Loading reranker model: %s", self.rerank_model_name)
            self._reranker = CrossEncoder(
                self.rerank_model_name,
                device=str(self.device),
            )
            logger.info("Reranker model loaded")
        except Exception as exc:
            logger.error("Failed to load reranker model %s: %s", self.rerank_model_name, exc)
            self._reranker = None

        return self._reranker

    def _load_llm_from_name(self, model_name: str) -> Tuple[Any, Any]:
        """Load tokenizer+model for a specific model name."""
        if AutoTokenizer is None or AutoModelForCausalLM is None:
            raise RuntimeError("transformers is not available")

        logger.info("Loading LLM model: %s", model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

        torch_dtype = torch.float16 if self.device.type == "cuda" else torch.float32
        model_kwargs = {
            "dtype": torch_dtype,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }

        if self.device.type == "cuda":
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                **model_kwargs,
            )
        else:
            model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
            model.to(self.device)

        model.eval()
        return tokenizer, model

    def get_llm(self):
        """Get local LLM tokenizer+model with fallback to lighter model."""
        if self._llm_model is not None and self._llm_tokenizer is not None:
            return self._llm_tokenizer, self._llm_model, self._llm_loaded_name

        attempts = [self.llm_model_name]
        if self.llm_fallback_model_name not in attempts:
            attempts.append(self.llm_fallback_model_name)

        for candidate in attempts:
            try:
                tokenizer, model = self._load_llm_from_name(candidate)
                self._llm_tokenizer = tokenizer
                self._llm_model = model
                self._llm_loaded_name = candidate
                logger.info("LLM loaded successfully: %s", candidate)
                break
            except Exception as exc:
                logger.error("Failed to load LLM model %s: %s", candidate, exc)

        return self._llm_tokenizer, self._llm_model, self._llm_loaded_name

    def get_imaging_model(self, num_classes: int = 8, custom_weights_path: Optional[str] = None):
        """Get imaging backbone model with optional custom-weight loading."""
        if self._imaging_model is not None:
            return self._imaging_model

        if models is None:
            logger.error("torchvision is not available; imaging model disabled")
            return None

        try:
            logger.info("Loading imaging backbone: efficientnet_b0")
            weights = None
            if hasattr(models, "EfficientNet_B0_Weights"):
                weights = models.EfficientNet_B0_Weights.IMAGENET1K_V1
            model = models.efficientnet_b0(weights=weights)
            model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, num_classes)

            if custom_weights_path:
                weight_path = Path(custom_weights_path)
                if weight_path.exists():
                    try:
                        state_dict = torch.load(weight_path, map_location=self.device)
                        model.load_state_dict(state_dict, strict=False)
                        logger.info("Loaded custom imaging weights from %s", weight_path)
                    except Exception as exc:
                        logger.error("Failed to load custom imaging weights: %s", exc)
                else:
                    logger.warning("Custom imaging weights not found at %s", weight_path)

            model.to(self.device)
            model.eval()
            self._imaging_model = model
            logger.info("Imaging model ready on device=%s", self.device)
        except Exception as exc:
            logger.error("Failed to initialize imaging model: %s", exc)
            self._imaging_model = None

        return self._imaging_model

    def get_status(self) -> dict:
        """Return loaded-state summary for health checks."""
        return {
            "device": str(self.device),
            "embedding_model_loaded": self._embedding_model is not None,
            "embedding_fallback_model_loaded": self._embedding_fallback_model is not None,
            "reranker_loaded": self._reranker is not None,
            "llm_loaded": self._llm_model is not None and self._llm_tokenizer is not None,
            "imaging_model_loaded": self._imaging_model is not None,
            "llm_model_name": self._llm_loaded_name,
            "use_embedding_api": self.use_embedding_api,
            "use_rerank_api": self.use_rerank_api,
            "use_llm_api": self.use_llm_api,
            "use_imaging_api": self.use_imaging_api,
            "llm_enabled": self.llm_enabled,
            "last_embedding_api_ms": round(self.last_embedding_api_ms, 2),
            "last_rerank_api_ms": round(self.last_rerank_api_ms, 2),
            "last_llm_api_ms": round(self.last_llm_api_ms, 2),
            "last_imaging_api_ms": round(self.last_imaging_api_ms, 2),
        }

    def embed_texts(self, texts: List[str], normalize: bool = True, language: Optional[str] = None) -> Optional[Any]:
        """Unified embedding interface with API/local fallback."""
        if not texts:
            return None

        logger.debug("Embeddings Mode: %s", self._mode_label(self.use_embedding_api))

        if self.use_embedding_api and requests is not None:
            self.last_embedding_api_ms = 0.0
            for attempt in range(2):  # Try once, then 1 retry
                try:
                    endpoint = self.embedding_api_endpoint or (
                        f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.embedding_model_name}"
                    )
                    payload = {
                        "inputs": texts,
                        "options": {"wait_for_model": True},
                    }
                    api_start = time.perf_counter()
                    response = requests.post(endpoint, headers=self._hf_headers(), json=payload, timeout=10)
                    api_elapsed = (time.perf_counter() - api_start) * 1000.0
                    self.last_embedding_api_ms = api_elapsed
                    
                    if response.status_code == 200:
                        vectors = response.json()
                        arr = torch.tensor(vectors, dtype=torch.float32).cpu().numpy()
                        if arr.ndim == 3:
                            # HF feature-extraction may return token embeddings; mean-pool tokens.
                            arr = arr.mean(axis=1)
                        if arr.ndim == 1:
                            arr = arr.reshape(1, -1)
                        if normalize:
                            norms = (arr**2).sum(axis=1, keepdims=True) ** 0.5
                            arr = arr / (norms + 1e-12)
                        logger.info("Embedding API succeeded (%.2fms)", api_elapsed)
                        return arr
                    logger.warning("Embedding API returned status %s (attempt %d/2)", response.status_code, attempt + 1)
                except Exception as exc:
                    if attempt == 0:
                        logger.warning("Embedding API failed (attempt 1/2): %s; retrying...", exc)
                    else:
                        logger.warning("Embedding API failed (attempt 2/2), falling back to local model: %s", exc)

        # Hybrid strategy:
        # - English queries/docs -> biomedical encoder
        # - Non-English queries -> multilingual fallback
        model = self.get_embedding_model() if self._is_english_language(language) else self.get_fallback_embedding_model()
        if model is None and not self._is_english_language(language):
            # Safety fallback: if multilingual model unavailable, use primary model.
            model = self.get_embedding_model()
        if model is None:
            return None
        try:
            return model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
            )
        except Exception as exc:
            logger.error("Local embedding failed: %s", exc)
            return None

    def rerank_pairs(self, pairs: List[List[str]]) -> Optional[List[float]]:
        """Unified reranking interface with API/local fallback."""
        if not pairs:
            return []

        logger.debug("Reranker Mode: %s", self._mode_label(self.use_rerank_api))

        if self.use_rerank_api and requests is not None:
            self.last_rerank_api_ms = 0.0
            for attempt in range(2):  # Try once, then 1 retry
                try:
                    endpoint = self.rerank_api_endpoint or f"https://api-inference.huggingface.co/models/{self.rerank_model_name}"
                    hf_inputs = [{"text": q, "text_pair": d} for q, d in pairs]
                    payload = {"inputs": hf_inputs, "options": {"wait_for_model": True}}
                    api_start = time.perf_counter()
                    response = requests.post(endpoint, headers=self._hf_headers(), json=payload, timeout=10)
                    api_elapsed = (time.perf_counter() - api_start) * 1000.0
                    self.last_rerank_api_ms = api_elapsed
                    
                    if response.status_code == 200:
                        result = response.json()
                        scores: List[float] = []
                        for item in result:
                            if isinstance(item, list) and item:
                                best = max(item, key=lambda x: float(x.get("score", 0.0)))
                                scores.append(float(best.get("score", 0.0)))
                            elif isinstance(item, dict):
                                scores.append(float(item.get("score", 0.0)))
                            else:
                                scores.append(0.0)
                        logger.info("Rerank API succeeded (%.2fms)", api_elapsed)
                        return scores
                    logger.warning("Rerank API returned status %s (attempt %d/2)", response.status_code, attempt + 1)
                except Exception as exc:
                    if attempt == 0:
                        logger.warning("Rerank API failed (attempt 1/2): %s; retrying...", exc)
                    else:
                        logger.warning("Rerank API failed (attempt 2/2), falling back to local model: %s", exc)

        reranker = self.get_reranker()
        if reranker is None:
            return None
        try:
            return [float(x) for x in reranker.predict(pairs)]
        except Exception as exc:
            logger.error("Local reranker failed: %s", exc)
            return None

    def llm_chat(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float, top_p: float) -> Optional[str]:
        """Unified LLM interface: API-first when enabled, otherwise local model."""
        if not self.llm_enabled:
            return None

        logger.debug("LLM Mode: %s", self._mode_label(self.use_llm_api))

        if self.use_llm_api and requests is not None:
            self.last_llm_api_ms = 0.0
            # Try OpenAI-compatible API first (OpenAI/OpenRouter/custom chat-completions endpoint).
            llm_models = self.llm_api_models or [self.llm_model_name]

            # Try Google Gemini API when a Gemini key is configured.
            gemini_key = self.gemini_api_key
            if not gemini_key and self.openrouter_api_key.startswith("AIza"):
                # Backward-compatible fallback if Gemini key was put in OPENROUTER_API_KEY.
                gemini_key = self.openrouter_api_key

            if gemini_key:
                gemini_models = []
                for model_name in llm_models:
                    normalized = model_name.strip()
                    if normalized.lower().startswith("google/"):
                        normalized = normalized.split("/", 1)[1]
                    if "gemini" in normalized.lower():
                        gemini_models.append(normalized)
                if not gemini_models:
                    gemini_models = ["gemini-2.0-flash-001", "gemini-1.5-pro"]

                for model_name in gemini_models:
                    try:
                        endpoint = (
                            f"https://generativelanguage.googleapis.com/v1beta/models/"
                            f"{model_name}:generateContent?key={gemini_key}"
                        )
                        payload = {
                            "contents": [
                                {
                                    "role": "user",
                                    "parts": [
                                        {
                                            "text": (
                                                f"System instructions:\n{system_prompt}\n\n"
                                                f"User request:\n{prompt}"
                                            )
                                        }
                                    ],
                                }
                            ],
                            "generationConfig": {
                                "temperature": temperature,
                                "topP": top_p,
                                "maxOutputTokens": max_tokens,
                            },
                        }
                        api_start = time.perf_counter()
                        response = requests.post(
                            endpoint,
                            headers={"Content-Type": "application/json"},
                            json=payload,
                            timeout=20,
                        )
                        api_elapsed = (time.perf_counter() - api_start) * 1000.0
                        self.last_llm_api_ms = api_elapsed

                        if response.status_code == 200:
                            content = self._extract_gemini_content(response.json())
                            if content:
                                logger.info("Gemini LLM API succeeded via model=%s (%.2fms)", model_name, api_elapsed)
                                return content
                        else:
                            logger.warning(
                                "Gemini LLM API returned status %s for model=%s",
                                response.status_code,
                                model_name,
                            )
                    except Exception as exc:
                        logger.warning("Gemini LLM API failed for model=%s: %s", model_name, exc)

            skip_hf_fallback = bool(gemini_key and not self.llm_api_endpoint)

            openai_chat_endpoint = None
            if self.llm_api_endpoint and "chat/completions" in self.llm_api_endpoint:
                openai_chat_endpoint = self.llm_api_endpoint
            elif self.openai_base_url:
                openai_chat_endpoint = f"{self.openai_base_url.rstrip('/')}/chat/completions"
            elif self.openrouter_api_key:
                openai_chat_endpoint = "https://openrouter.ai/api/v1/chat/completions"

            endpoint_is_openrouter = bool(openai_chat_endpoint and "openrouter.ai" in openai_chat_endpoint)
            chat_headers = self._openrouter_headers() if endpoint_is_openrouter else self._openai_headers()

            if openai_chat_endpoint:
                for model_name in llm_models:
                    try:
                        payload = {
                            "model": model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "top_p": top_p,
                        }
                        api_start = time.perf_counter()
                        response = requests.post(openai_chat_endpoint, headers=chat_headers, json=payload, timeout=20)
                        api_elapsed = (time.perf_counter() - api_start) * 1000.0
                        self.last_llm_api_ms = api_elapsed

                        if response.status_code == 200:
                            content = self._extract_chat_content(response.json())
                            if content:
                                logger.info("Chat-completions LLM API succeeded via model=%s (%.2fms)", model_name, api_elapsed)
                                return content
                        else:
                            logger.warning(
                                "Chat-completions LLM API returned status %s for model=%s",
                                response.status_code,
                                model_name,
                            )
                    except Exception as exc:
                        logger.warning("Chat-completions LLM API failed for model=%s: %s", model_name, exc)

            if not skip_hf_fallback:
                for attempt in range(2):  # Try once, then 1 retry
                    try:
                        endpoint = self.llm_api_endpoint or f"https://api-inference.huggingface.co/models/{self.llm_model_name}"
                        # Skip HF fallback when endpoint is clearly chat-completions; already handled above.
                        if "chat/completions" in endpoint:
                            break
                        payload = {
                            "inputs": f"{system_prompt}\n\n{prompt}",
                            "parameters": {
                                "max_new_tokens": max_tokens,
                                "temperature": temperature,
                                "top_p": top_p,
                                "return_full_text": False,
                            },
                            "options": {"wait_for_model": True},
                        }
                        api_start = time.perf_counter()
                        response = requests.post(endpoint, headers=self._hf_headers(), json=payload, timeout=20)
                        api_elapsed = (time.perf_counter() - api_start) * 1000.0
                        self.last_llm_api_ms = api_elapsed

                        if response.status_code == 200:
                            data = response.json()
                            if isinstance(data, list) and data:
                                logger.info("HF LLM API succeeded (%.2fms)", api_elapsed)
                                return str(data[0].get("generated_text", "")).strip() or None
                        logger.warning("HF LLM API returned status %s (attempt %d/2)", response.status_code, attempt + 1)
                    except Exception as exc:
                        if attempt == 0:
                            logger.warning("HF LLM API failed (attempt 1/2): %s; retrying...", exc)
                        else:
                            logger.warning("HF LLM API failed (attempt 2/2), falling back to template answer: %s", exc)

            # In API mode, avoid loading heavy local LLM as fallback.
            return None

        tokenizer, model, _ = self.get_llm()
        if tokenizer is None or model is None:
            return None

        try:
            if hasattr(tokenizer, "apply_chat_template"):
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
                model_input = tokenizer.apply_chat_template(
                    messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt",
                )
            else:
                model_input = tokenizer(f"{system_prompt}\n\n{prompt}", return_tensors="pt").input_ids

            model_input = model_input.to(model.device)
            do_sample = temperature > 0.0
            with torch.no_grad():
                generated = model.generate(
                    model_input,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    pad_token_id=tokenizer.eos_token_id,
                )
            new_tokens = generated[0][model_input.shape[-1]:]
            return tokenizer.decode(new_tokens, skip_special_tokens=True).strip() or None
        except Exception as exc:
            logger.error("Local LLM generation failed: %s", exc)
            return None

    def imaging_classify_api(self, image_bytes: bytes, filename: str = "image.png", top_k: int = 3) -> Optional[dict]:
        """Call external trained imaging classification API when configured."""
        if not self.use_imaging_api or not self.imaging_api_endpoint or requests is None:
            return None

        self.last_imaging_api_ms = 0.0
        files = {"file": (filename, image_bytes, "application/octet-stream")}
        data = {"top_k": str(max(1, int(top_k)))}

        for attempt in range(2):
            try:
                api_start = time.perf_counter()
                response = requests.post(
                    self.imaging_api_endpoint,
                    headers=self._imaging_headers(),
                    files=files,
                    data=data,
                    timeout=10,
                )
                api_elapsed = (time.perf_counter() - api_start) * 1000.0
                self.last_imaging_api_ms = api_elapsed
                if response.status_code == 200:
                    logger.info("Imaging classify API succeeded (%.2fms)", api_elapsed)
                    payload = response.json()
                    return payload if isinstance(payload, dict) else None
                logger.warning("Imaging classify API returned status %s (attempt %d/2)", response.status_code, attempt + 1)
            except Exception as exc:
                if attempt == 0:
                    logger.warning("Imaging classify API failed (attempt 1/2): %s; retrying...", exc)
                else:
                    logger.warning("Imaging classify API failed (attempt 2/2): %s", exc)
        return None

    def imaging_explain_api(self, image_bytes: bytes, filename: str = "image.png") -> Optional[Tuple[bytes, str]]:
        """Call external trained imaging explain API and return (bytes, content_type)."""
        if not self.use_imaging_api or not self.imaging_explain_api_endpoint or requests is None:
            return None

        self.last_imaging_api_ms = 0.0
        files = {"file": (filename, image_bytes, "application/octet-stream")}

        for attempt in range(2):
            try:
                api_start = time.perf_counter()
                response = requests.post(
                    self.imaging_explain_api_endpoint,
                    headers=self._imaging_headers(),
                    files=files,
                    timeout=10,
                )
                api_elapsed = (time.perf_counter() - api_start) * 1000.0
                self.last_imaging_api_ms = api_elapsed
                if response.status_code == 200:
                    logger.info("Imaging explain API succeeded (%.2fms)", api_elapsed)
                    content_type = response.headers.get("Content-Type", "image/png")
                    return response.content, content_type
                logger.warning("Imaging explain API returned status %s (attempt %d/2)", response.status_code, attempt + 1)
            except Exception as exc:
                if attempt == 0:
                    logger.warning("Imaging explain API failed (attempt 1/2): %s; retrying...", exc)
                else:
                    logger.warning("Imaging explain API failed (attempt 2/2): %s", exc)
        return None


def get_model_loader() -> ModelLoader:
    """Convenience accessor for singleton loader."""
    return ModelLoader.instance()


def get_embedding_model():
    """Top-level accessor required by the model-loading contract."""
    return get_model_loader().get_embedding_model()


def get_reranker():
    """Top-level accessor required by the model-loading contract."""
    return get_model_loader().get_reranker()


def get_llm():
    """Top-level accessor required by the model-loading contract."""
    return get_model_loader().get_llm()


def get_imaging_model(num_classes: int = 8, custom_weights_path: Optional[str] = None):
    """Top-level accessor required by the model-loading contract."""
    return get_model_loader().get_imaging_model(
        num_classes=num_classes,
        custom_weights_path=custom_weights_path,
    )

# Demo Mode Configuration

## Overview
This guide shows how to configure the Healthcare AI system for optimal demo performance with API-first execution, BM25 + FAISS hybrid retrieval, and stable fallback behavior.

## 🎯 Recommended Demo Configuration

### Option 1: **Fast Demo Mode (Recommended for Live Demo)**
Best for presentations where you want instant responses without heavy model loading.

```bash
# Set these environment variables:
export LLM_ENABLED=false
export USE_EMBEDDING_API=true
export USE_RERANK_API=true
export USE_LLM_API=false
export HUGGINGFACE_TOKEN=your_hf_token_here

# Then start the server:
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Behavior:**
- ⚡ **Fast**: No heavy model loading (~5-10s per query from API)
- 🧠 **Smart**: Real embedding + reranking via APIs
- 🛡️ **Stable**: Falls back to local models if APIs timeout/fail
- 🎯 **Perfect**: Answer generation via templates

---

### Option 2: **Full Local Mode (For Offline/Long-Term Use)**
If you have GPU or want everything running locally.

```bash
export LLM_ENABLED=false
export USE_EMBEDDING_API=false
export USE_RERANK_API=false
export USE_LLM_API=false
```

**Behavior:**
- 🚀 No external dependencies
- 💻 Runs fully locally (requires sentence-transformers, cross-encoder)
- ⚠️ Slower (full model loading on first query)

---

### Option 3: **API-First with LLM (Full Feature Set)**
Uses APIs for embedding, reranking, AND text generation.

```bash
export LLM_ENABLED=true
export USE_EMBEDDING_API=true
export USE_RERANK_API=true
export USE_LLM_API=true
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-...
export HUGGINGFACE_TOKEN=hf_...
```

**Behavior:**
- 🤖 Full API-powered pipeline
- 🎨 High-quality generated answers
- ⚠️ Depends on external APIs (failure modes)

---

## 📊 API Configuration Details

### Hugging Face Inference API (DEFAULT)
Free tier for public models, but rate-limited.

```bash
export HUGGINGFACE_TOKEN=hf_your_token_here
# These are already configured to use HF by default:
# EMBEDDING_API_ENDPOINT: not set (uses HF)
# RERANK_API_ENDPOINT: not set (uses HF)
# LLM_API_ENDPOINT: not set (uses HF)
```

### OpenAI Compatible API
For custom or premium endpoints.

```bash
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-...
# Or custom endpoint:
export OPENAI_BASE_URL=https://your-llm-server.com/v1
export LLM_API_ENDPOINT=https://your-llm-server.com/v1/chat/completions
```

### Custom Endpoints
If using a different provider.

```bash
export EMBEDDING_API_ENDPOINT=https://your-api.com/v1/embeddings
export RERANK_API_ENDPOINT=https://your-api.com/v1/rerank
export LLM_API_ENDPOINT=https://your-api.com/v1/generate
```

---

## 🧪 Testing Your Configuration

### Quick Health Check
```bash
curl http://localhost:8000/health | jq '.ai_model'
```

Expected output (confirms API flags):
```json
{
  "api_first_mode": true,
  "llm_api_enabled": false,
  "embedding_api_enabled": true,
  "reranker_api_enabled": true,
  "api_endpoints": {
    "llm": "",
    "embeddings": "",
    "reranker": ""
  }
}
```

### Test RAG Query
```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What are symptoms of diabetes?","top_k":3}'
```

Expected response (should be instant with API mode):
```json
{
  "answer": "Based on available knowledge...",
  "confidence": 0.75,
  "language": "en",
  "sources": [...]
}
```

---

## 📈 Performance Characteristics

| Mode | Embedding | Reranking | LLM | Initial Load | Per-Query Time |
|------|-----------|-----------|-----|--------------|----------------|
| **API-First** | API (HF) | API (HF) | Template | 2-3s | 2-5s |
| **Full Local** | Local | Local | Template | 15-30s | 5-15s |
| **Hybrid** | API | API | Local | 10-15s | 5-10s |

---

## 🚨 Timeout Behavior

All API calls are configured with:
- **Timeout:** 10 seconds per request
- **Retry:** 1 automatic retry on timeout
- **Fallback:** Automatic switch to local model if API fails

Logs will show:
```
2026-03-29 14:41:38 | src.models.model_loader | INFO | Embedding API succeeded (125.45ms)
2026-03-29 14:41:38 | src.models.model_loader | INFO | Rerank API succeeded (234.67ms)
2026-03-29 14:41:38 | src.rag_system.rag | INFO | RAG timings | embedding_ms=125.45 vector_search_ms=45.23 retrieval_ms=543.21 rerank_ms=234.67 generation_ms=12.34 total_ms=960.90
```

---

## 🎬 Starting the Demo

### With Click & Run (PowerShell)
```powershell
$env:LLM_ENABLED='false'
$env:USE_EMBEDDING_API='true'
$env:USE_RERANK_API='true'
$env:HUGGINGFACE_TOKEN='your_token'
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker (Optional)
```bash
docker run -e LLM_ENABLED=false -e USE_EMBEDDING_API=true \
  -e HUGGINGFACE_TOKEN=your_token \
  -p 8000:8000 healthcare-ai:latest
```

---

## ✅ Demo Checklist

Before presenting:
- [ ] Verify `/health` endpoint shows API flags
- [ ] Run quick RAG query (should complete in <10s)
- [ ] Check logs for "API succeeded" messages
- [ ] Frontend loads at `http://localhost:3000`
- [ ] Chat page at `/chat` is responsive

---

## 🔧 Troubleshooting

### API calls timing out
→ Reduce `HUGGINGFACE_TOKEN` rate limit wait by checking your quota
→ Or switch to Option 1 (Local mode without API flags)

### "Failed to load embedding model"
→ Check HUGGINGFACE_TOKEN is set and valid
→ Or USE_EMBEDDING_API=false will use local model

### Slow responses
→ Check if LLM_ENABLED=true (disable to use template fallback)
→ Profile with `/metrics` endpoint

---

## 📊 Monitoring

Check aggregated API statistics:
```bash
curl http://localhost:8000/metrics | grep -i "api\|latency"
```

Or visit the Grafana dashboard:
```
http://localhost:3000  (username: admin, password: admin)
```

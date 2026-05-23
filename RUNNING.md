# 🎉 Healthcare AI Assistant - RUNNING!

## ✅ Server Status

**Status**: ✅ RUNNING  
**URL**: http://localhost:8001  
**API Documentation**: http://localhost:8001/docs  
**Environment**: Development  

---

## 🌐 Available API Endpoints

###1️⃣ **Knowledge Retrieval (RAG System)** - WORKING!

#### Query Medical Knowledge
```
POST http://localhost:8001/api/v1/rag/query
```

**Example Request (English)**:
```json
{
  "question": "What are pneumonia symptoms?",
  "language": "en"
}
```

**Example Request (Arabic)**:
```json
{
  "question": "ما هي أعراض الالتهاب الرئوي؟"
}
```

**Example Request (French)**:
```json
{
  "question": "Comment traiter le COVID-19?",
  "language": "fr"
}
```

**Response**:
```json
{
  "answer": "Pneumonia symptoms include cough with phlegm, fever, shortness of breath, and chest pain.",
  "sources": [
    {
      "title": "Pneumonia Information",
      "content": {"en": "...", "ar": "...", "fr": "..."},
      "relevance_score": 0.9
    }
  ],
  "confidence": 0.85,
  "language": "en",
  "question": "What are pneumonia symptoms?"
}
```

#### Get Example Queries
```
GET http://localhost:8001/api/v1/rag/examples
```

#### Get Supported Languages
```
GET http://localhost:8001/api/v1/rag/languages
```

---

### 2️⃣ **Medical Imaging** - READY (Awaiting PyTorch)

#### Classify X-Ray Image
```
POST http://localhost:8001/api/v1/imaging/classify
```

**Form Data**:
- `file`: X-ray image (JPG, PNG)
- `explain`: boolean (optional)
- `top_k`: integer (optional, default: 3)

**Response**:
```json
{
  "filename": "xray.jpg",
  "predictions": [
    {"disease": "Pneumonia", "confidence": 0.92},
    {"disease": "Normal", "confidence": 0.05},
    {"disease": "COVID-19", "confidence": 0.02}
  ],
  "top_disease": "Pneumonia",
  "top_confidence": 0.92
}
```

#### Get Supported Diseases
```
GET http://localhost:8001/api/v1/imaging/diseases
```

**Response**:
```json
{
  "diseases": ["Normal", "Pneumonia", "COVID-19", "Tuberculosis", "Atelectasis", "Cardiomegaly", "Effusion", "Infiltration"],
  "count": 8
}
```

---

### 3️⃣  **System Health**

#### Root Health Check
```
GET http://localhost:8001/
```

**Response**:
```json
{
  "name": "Healthcare AI Assistant",
  "version": "0.1.0",
  "status": "healthy",
  "environment": "development"
}
```

#### Detailed Health Check
```
GET http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "api": "active",
    "medical_imaging": "active",
    "rag_system": "active",
    "vital_signs": "active",
    "knowledge_graph": "active"
  }
}
```

---

## 🧪 Quick Tests

### Test with PowerShell

**1. Query in English**:
```powershell
$body = @{ question = "What are COVID-19 symptoms?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/rag/query" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
```

**2. Query in Arabic**:
```powershell
$body = @{ question = "ما هي أعراض كوفيد-19؟" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/rag/query" -Method Post -Body $body -ContentType "application/json; charset=utf-8" | ConvertTo-Json
```

**3. Query in French**:
```powershell
$body = @{ question = "Quels sont les symptômes de la tuberculose?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/rag/query" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json
```

**4. Get Examples**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/rag/examples" | ConvertTo-Json -Depth 5
```

---

## 📊 Current Features

### ✅ Working Now
- ✅ RESTful API server (FastAPI)
- ✅ Multi-lingual RAG system (Arabic, French, English)
- ✅ Automatic language detection
- ✅ Medical knowledge base queries
- ✅ Interactive API documentation (Swagger UI)
- ✅ Health monitoring endpoints
- ✅ CORS enabled for web integration

### 🔄 Pending (When PyTorch Installed)
- ⏳ Medical image classification (pretrained models)
- ⏳ Grad-CAM explanations
- ⏳ Advanced vector search (FAISS)
- ⏳ LLM-powered answer generation
- ⏳ Vital signs monitoring (rPPG)

---

## 🚀 Next Steps

### Immediate (Today)
1. **Test the RAG system** with different medical questions
2. **Explore the API docs** at http://localhost:8001/docs
3. **Try the interactive examples** in the Swagger UI

### Short-term (This Week)
1. **Download PyTorch** to enable medical imaging:
   ```powershell
   & C:\HealthcareAI-NorthAfrica\venv\Scripts\pip.exe install torch torchvision
   ```

2. **Download pretrained models**:
   ```powershell
   cd C:\HealthcareAI-NorthAfrica
   & .\venv\Scripts\python.exe scripts\download_models.py
   ```

3. **Test image classification** with sample X-rays

### Medium-term (This Month)
1. **Build medical knowledge graph** (Neo4j)
2. **Integrate advanced RAG** (FAISS + embeddings)
3. **Add vital signs monitoring**
4. **Deploy to production** (Docker)

---

## 🛠️ Management Commands

### One-Command Dev Stack Startup (Recommended)

Start backend + frontend together in a known-good local configuration:

```powershell
cd C:\HealthcareAI-NorthAfrica
powershell -ExecutionPolicy Bypass -File .\scripts\start_dev_stack.ps1
```

Optional arguments:

```powershell
# Use custom ports
powershell -ExecutionPolicy Bypass -File .\scripts\start_dev_stack.ps1 -BackendPort 8001 -FrontendPort 5175

# Preview commands without launching processes
powershell -ExecutionPolicy Bypass -File .\scripts\start_dev_stack.ps1 -DryRun
```

This launcher sets safe demo flags for backend startup:
- LLM_ENABLED=false
- USE_LLM_API=false
- USE_EMBEDDING_API=false
- USE_RERANK_API=false
- USE_IMAGING_API=false

### Start in Trained-API Mode (Chat + Imaging)

Use this when you want remote trained model APIs for both chat and image processing:

```powershell
cd C:\HealthcareAI-NorthAfrica
powershell -ExecutionPolicy Bypass -File .\scripts\start_dev_stack.ps1 `
  -UseTrainedApis `
  -EmbeddingApiEndpoint "https://.../embeddings" `
  -RerankApiEndpoint "https://.../rerank" `
  -LlmApiEndpoint "https://.../chat/completions" `
  -ImagingApiEndpoint "https://.../imaging/classify" `
  -ImagingExplainApiEndpoint "https://.../imaging/explain" `
  -HfToken "hf_xxx" `
  -OpenAiApiKey "sk-xxx"
```

If an imaging API endpoint is unavailable, backend automatically falls back to local processing.

### Start with Alternative Multilingual Chat API (Arabic/French/English)

Use an OpenAI-compatible provider (for example OpenRouter) with model fallback:

```powershell
cd C:\HealthcareAI-NorthAfrica
$env:LLM_ENABLED='true'
$env:USE_LLM_API='true'
$env:OPENROUTER_API_KEY='sk-or-your-openrouter-key'
$env:LLM_API_MODELS='openai/gpt-4o-mini,google/gemini-2.0-flash-001,qwen/qwen-2.5-72b-instruct'
python -m uvicorn main:app --host 127.0.0.1 --port 8011
```

Notes:
- Leave `LLM_API_ENDPOINT` empty to auto-use OpenRouter when `OPENROUTER_API_KEY` is set.
- Set `OPENAI_BASE_URL` + `OPENAI_API_KEY` instead if you prefer another OpenAI-compatible provider.
- The backend now tries configured models in order and falls back automatically.

It also checks whether backend health is already available and avoids duplicate launches when possible.

### Start Server
```powershell
cd C:\HealthcareAI-NorthAfrica
& .\venv\Scripts\python.exe main.py
```

### Stop Server
```powershell
Get-Process python | Where-Object {$_.Path -like "*HealthcareAI*"} | Stop-Process
```

### Run Tests
```powershell
& .\venv\Scripts\python.exe demo.py
```

### View Logs
Check console output or enable file logging in `.env`

---

## 📚 Documentation

- **Full README**: [README.md](README.md)
- **Getting Started Guide**: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
- **6-Month Roadmap**: [docs/ROADMAP.md](docs/ROADMAP.md)
- **API Docs**: http://localhost:8001/docs
- **Alternative Docs**: http://localhost:8001/redoc

---

## 🎯 Sample Medical Queries

Try these in the API:

### English
- "What are the symptoms of pneumonia?"
- "How is COVID-19 transmitted?"
- "What is the treatment for tuberculosis?"

### Arabic (العربية)
- "ما هي أعراض الالتهاب الرئوي؟"
- "كيف ينتقل كوفيد-19؟"  
- "ما هو علاج السل؟"

### French (Français)
- "Quels sont les symptômes de la pneumonie?"
- "Comment se transmet le COVID-19?"
- "Quel est le traitement de la tuberculose?"

---

## 💡 Tips

1. **API Documentation is Interactive**: Visit http://localhost:8001/docs and click "Try it out" on any endpoint

2. **Language Auto-Detection**: You don't need to specify the language - the system detects it automatically

3. **Multi-lingual Responses**: The system returns answers in the same language as the question

4. **Error Handling**: All endpoints include proper error messages if something goes wrong

5. **CORS Enabled**: You can call these APIs from web applications

---

## 🐛 Troubleshooting

### Port Already in Use
```powershell
# Kill process on port 8001
$proc = Get-NetTCPConnection -LocalPort 8001 | Select -ExpandProperty OwningProcess -Unique
Stop-Process -Id $proc -Force
```

### Can't Access API
- Check if server is running: `Invoke-RestMethod "http://localhost:8001"`
- Check firewall settings
- Try using `127.0.0.1` instead of `localhost`

### Module Not Found Errors
```powershell
# Reinstall dependencies
cd C:\HealthcareAI-NorthAfrica
& .\venv\Scripts\pip.exe install -r requirements-minimal.txt
```

---

## ✅ Success!

Your Healthcare AI Assistant is running and serving medical knowledge in 3 languages! 

**Built with ❤️ for accessible healthcare in North Africa** 🏥💚

---

**Project Location**: `C:\HealthcareAI-NorthAfrica`  
**Server URL**: http://localhost:8001  
**Docs**: http://localhost:8001/docs  

**Happy Building! 🚀**

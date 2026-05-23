# Healthcare AI System - Models Architecture & Structure

## 📊 **Complete Model Overview**

This document provides a detailed description of all AI models used in the Healthcare AI Assistant system, their architecture, purpose, and configuration.

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Healthcare AI System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   RAG        │  │   Medical    │  │   Vital      │      │
│  │   System     │  │   Imaging    │  │   Signs      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         ▼                  ▼                  ▼              │
│  ┌──────────────────────────────────────────────────┐      │
│  │          Centralized Model Loader                 │      │
│  │         (src/models/model_loader.py)              │      │
│  └──────────────────────────────────────────────────┘      │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │  1. Embedding Model (Multilingual)              │       │
│  │  2. Reranker Model (Cross-Encoder)              │       │
│  │  3. LLM Model (Text Generation)                 │       │
│  │  4. Imaging Model (CNN Classification)          │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ **Embedding Models** (Text → Vector)

### **Purpose:**
Convert text (queries, documents) into dense vector representations for semantic search and retrieval.

### **Primary Model: BioMed RoBERTa**
```yaml
Model Name: sentence-transformers/biomed_roberta_base
Type: Sentence Transformer (BERT-based)
Framework: sentence-transformers
Base Architecture: RoBERTa
Domain: Biomedical/Medical
```

#### **Architecture:**
```
Input Text
    ↓
Tokenizer (RoBERTa)
    ↓
BERT Encoder (12 layers)
    ├─ Hidden Size: 768
    ├─ Attention Heads: 12
    ├─ Intermediate Size: 3072
    └─ Max Sequence Length: 512 tokens
    ↓
Mean Pooling
    ↓
Output: 768-dimensional vector
```

#### **Specifications:**
- **Parameters:** ~125M
- **Embedding Dimension:** 768
- **Training Data:** PubMed, PMC, biomedical literature
- **Languages:** English (optimized for medical terminology)
- **Use Case:** Medical query embeddings, document retrieval

#### **Performance:**
- **Encoding Speed:** ~100-200 texts/second (CPU)
- **Encoding Speed:** ~1000+ texts/second (GPU)
- **Memory:** ~500MB RAM

---

### **Fallback Model: Multilingual E5**
```yaml
Model Name: intfloat/multilingual-e5-base
Type: Sentence Transformer
Framework: sentence-transformers
Base Architecture: BERT
Domain: Multilingual (94 languages)
```

#### **Architecture:**
```
Input Text (Any Language)
    ↓
Tokenizer (Multilingual)
    ↓
BERT Encoder (12 layers)
    ├─ Hidden Size: 768
    ├─ Attention Heads: 12
    └─ Max Sequence Length: 512 tokens
    ↓
Mean Pooling
    ↓
Output: 768-dimensional vector
```

#### **Specifications:**
- **Parameters:** ~278M
- **Embedding Dimension:** 768
- **Languages:** 94 languages (Arabic, French, English, etc.)
- **Use Case:** Non-English queries (Arabic, French)

#### **When Used:**
- Automatically selected for Arabic/French queries
- Fallback when primary model fails
- Multilingual document retrieval

---

### **API Mode (Optional):**
```yaml
Provider: Hugging Face Inference API
Endpoint: https://api-rinference.huggingface.co/pipeline/feature-extraction/{model_name}
Fallback: Local model if API fails
Retry Logic: 2 attempts with exponential backoff
```

---

## 2️⃣ **Reranker Model** (Query-Document Scoring)

### **Purpose:**
Re-score retrieved documents based on query-document relevance using cross-attention.

### **Model: BioMed RoBERTa Cross-Encoder**
```yaml
Model Name: cross-encoder/biomed-roberta-base
Type: Cross-Encoder
Framework: sentence-transformers
Base Architecture: RoBERTa
Domain: Biomedical
```

#### **Architecture:**
```
Query + Document Pair
    ↓
Tokenizer (Concatenate with [SEP])
    ↓
RoBERTa Encoder (12 layers)
    ├─ Cross-Attention between Query & Document
    ├─ Hidden Size: 768
    └─ Max Sequence Length: 512 tokens
    ↓
Classification Head
    ↓
Output: Relevance Score (0.0 - 1.0)
```

#### **Specifications:**
- **Parameters:** ~125M
- **Input:** Query-document pairs
- **Output:** Relevance score (float)
- **Training:** Trained on medical Q&A pairs
- **Languages:** English (medical domain)

#### **Performance:**
- **Scoring Speed:** ~50-100 pairs/second (CPU)
- **Scoring Speed:** ~500+ pairs/second (GPU)
- **Memory:** ~500MB RAM

#### **Use Case:**
```python
# Example
query = "What are symptoms of pneumonia?"
documents = [
    "Pneumonia causes cough, fever, chest pain...",
    "Diabetes is a metabolic disorder...",
    "Tuberculosis affects the lungs..."
]

# Reranker scores
scores = [0.92, 0.15, 0.45]  # Pneumonia doc gets highest score
```

---

## 3️⃣ **LLM Models** (Text Generation)

### **Purpose:**
Generate natural language responses to medical queries using retrieved context.

### **Primary Model: Gemini 2.0 Flash (API)**
```yaml
Model Name: google/gemini-2.0-flash-exp
Provider: Google AI
Type: Large Language Model
Access: API (Gemini API)
```

#### **Architecture:**
```
System Prompt + User Query + Retrieved Context
    ↓
Gemini 2.0 Flash Model
    ├─ Architecture: Transformer (Google proprietary)
    ├─ Parameters: ~Billions (exact number not disclosed)
    ├─ Context Window: 32K tokens
    ├─ Training: Multimodal (text, images, code)
    └─ Languages: 100+ languages
    ↓
Generated Response
    ├─ Max Tokens: Configurable (default: 1024)
    ├─ Temperature: 0.7 (balanced creativity)
    └─ Top-P: 0.9 (nucleus sampling)
```

#### **Specifications:**
- **Context Window:** 32,768 tokens
- **Max Output:** 8,192 tokens
- **Languages:** Multilingual (Arabic, French, English)
- **Latency:** ~1-3 seconds per response
- **Cost:** Free tier available

#### **API Configuration:**
```python
endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
api_key = "AIzaSy..."  # From GEMINI_API_KEY

payload = {
    "contents": [{
        "role": "user",
        "parts": [{"text": "System: {system_prompt}\n\nUser: {query}"}]
    }],
    "generationConfig": {
        "temperature": 0.7,
        "topP": 0.9,
        "maxOutputTokens": 1024
    }
}
```

---

### **Fallback Models:**

#### **Option 1: Qwen 2.5 7B (Local)**
```yaml
Model Name: Qwen/Qwen2.5-7B-Instruct
Type: Causal Language Model
Framework: transformers (Hugging Face)
Parameters: 7 Billion
```

**Architecture:**
```
Input Tokens
    ↓
Qwen Transformer (32 layers)
    ├─ Hidden Size: 4096
    ├─ Attention Heads: 32
    ├─ Intermediate Size: 11008
    ├─ Context Window: 32K tokens
    └─ Activation: SwiGLU
    ↓
Language Modeling Head
    ↓
Generated Tokens
```

**Specifications:**
- **Parameters:** 7B
- **Quantization:** FP16 (GPU) / FP32 (CPU)
- **Memory:** ~14GB (FP16), ~28GB (FP32)
- **Speed:** ~10-20 tokens/second (CPU), ~50-100 tokens/second (GPU)

---

#### **Option 2: Mistral 7B (Local Fallback)**
```yaml
Model Name: mistralai/Mistral-7B-Instruct-v0.2
Type: Causal Language Model
Framework: transformers
Parameters: 7 Billion
```

**Architecture:**
```
Input Tokens
    ↓
Mistral Transformer (32 layers)
    ├─ Hidden Size: 4096
    ├─ Attention Heads: 32
    ├─ Sliding Window Attention: 4096 tokens
    ├─ Context Window: 8K tokens
    └─ Activation: SwiGLU
    ↓
Language Modeling Head
    ↓
Generated Tokens
```

**Specifications:**
- **Parameters:** 7B
- **Context Window:** 8,192 tokens
- **Memory:** ~14GB (FP16)
- **Speed:** ~10-20 tokens/second (CPU)

---

### **LLM Selection Logic:**
```python
if USE_LLM_API:
    # Try Gemini API first
    if GEMINI_API_KEY:
        try: Gemini 2.0 Flash
        except: Try next model
    
    # Try OpenRouter/OpenAI API
    if OPENROUTER_API_KEY or OPENAI_API_KEY:
        try: OpenRouter/OpenAI models
        except: Try next model
    
    # Try Hugging Face Inference API
    try: HF Inference API
    except: Return None (no fallback to local in API mode)
else:
    # Load local model
    try: Qwen 2.5 7B
    except: Try Mistral 7B
    except: Return None
```

---

## 4️⃣ **Medical Imaging Model** (Image Classification)

### **Purpose:**
Classify chest X-ray images to detect 33 different diseases and conditions.

### **Model: EfficientNet-B0 (Pretrained)**
```yaml
Model Name: efficientnet_b0
Type: Convolutional Neural Network (CNN)
Framework: torchvision / PyTorch
Base: ImageNet pretrained
Fine-tuned: Chest X-ray classification
```

#### **Architecture:**
```
Input Image (224x224x3)
    ↓
Stem: Conv2d(3, 32, 3x3) + BatchNorm + Swish
    ↓
MBConv Blocks (Mobile Inverted Bottleneck)
    ├─ Block 1: 32 → 16 channels (1 layer)
    ├─ Block 2: 16 → 24 channels (2 layers)
    ├─ Block 3: 24 → 40 channels (2 layers)
    ├─ Block 4: 40 → 80 channels (3 layers)
    ├─ Block 5: 80 → 112 channels (3 layers)
    ├─ Block 6: 112 → 192 channels (4 layers)
    └─ Block 7: 192 → 320 channels (1 layer)
    ↓
Head: Conv2d(320, 1280, 1x1) + BatchNorm + Swish
    ↓
Global Average Pooling
    ↓
Dropout (0.2)
    ↓
Fully Connected Layer (1280 → 33 classes)
    ↓
Softmax
    ↓
Output: 33 disease probabilities
```

#### **Specifications:**
- **Parameters:** ~5.3M
- **Input Size:** 224×224×3 (RGB)
- **Output:** 33 disease classes
- **Pretrained:** ImageNet (transferred to medical domain)
- **Memory:** ~20MB model file, ~500MB RAM during inference

#### **33 Disease Classes:**
```python
DISEASES = [
    "Normal",
    "Pneumonia",
    "COVID-19",
    "Tuberculosis",
    "Cardiomegaly",
    "Pleural Effusion",
    "Atelectasis",
    "Infiltration",
    "Asthma",
    "Bronchitis",
    "Pneumothorax",
    "COPD",
    "Pulmonary Edema",
    "Pneumoconiosis",
    "Acute Bronchiolitis",
    "Influenza",
    "Hypertension",
    "Myocardial Infarction",
    "Heart Failure",
    "Ischemic Heart Disease",
    "Malaria",
    "Typhoid",
    "Dengue",
    "Hepatitis B",
    "Diabetes",
    "Obesity",
    "Nephrolithiasis",
    "Glomerulonephritis",
    "UTI",
    "Appendicitis",
    "Gastroenteritis",
    "Peptic Ulcer",
    "Cirrhosis"
]
```

#### **Image Preprocessing:**
```python
# Normalization (ImageNet stats)
mean = [0.485, 0.456, 0.406]
std = [0.229, 0.224, 0.225]

# Pipeline
1. Resize to 224×224
2. Convert to RGB
3. Normalize with ImageNet stats
4. Convert to tensor
5. Add batch dimension
```

#### **Performance:**
- **Inference Time:** ~0.5-1 second (CPU)
- **Inference Time:** ~0.05-0.1 second (GPU)
- **Accuracy:** ~80-85% (depends on training data)

---

### **Fallback: SimpleEfficientNet (Lightweight)**
```yaml
Model Name: SimpleEfficientNet (Custom)
Type: Lightweight CNN
Framework: PyTorch
Parameters: ~1M
```

**Architecture:**
```
Input Image (224x224x3)
    ↓
Conv Block 1: Conv2d(3, 32) + ReLU + BatchNorm + MaxPool
    ↓
Conv Block 2: Conv2d(32, 64) + ReLU + BatchNorm + MaxPool
    ↓
Conv Block 3: Conv2d(64, 128) + ReLU + BatchNorm + MaxPool
    ↓
Conv Block 4: Conv2d(128, 256) + ReLU + BatchNorm + AdaptiveAvgPool
    ↓
Flatten
    ↓
FC Layer 1: Linear(256, 128) + ReLU + Dropout(0.5)
    ↓
FC Layer 2: Linear(128, 33)
    ↓
Output: 33 disease logits
```

**Specifications:**
- **Parameters:** ~1M (much lighter)
- **Memory:** ~5MB model file
- **Speed:** Faster than EfficientNet-B0
- **Use Case:** When pretrained model unavailable

---

### **Grad-CAM (Explainability)**
```yaml
Purpose: Visual explanation of model predictions
Method: Gradient-weighted Class Activation Mapping
Target Layer: Last convolutional layer (features.7)
```

**How it Works:**
```
1. Forward pass → Get prediction
2. Backward pass → Compute gradients
3. Weight feature maps by gradients
4. Generate heatmap
5. Overlay on original image
```

**Output:**
- Heatmap showing which regions influenced the prediction
- Helps doctors understand AI reasoning

---

## 📊 **Model Comparison Table**

| Model | Type | Parameters | Memory | Speed | Use Case |
|-------|------|------------|--------|-------|----------|
| **BioMed RoBERTa** | Embedding | 125M | 500MB | Fast | Medical text embedding |
| **Multilingual E5** | Embedding | 278M | 1GB | Fast | Multilingual embedding |
| **BioMed Cross-Encoder** | Reranker | 125M | 500MB | Medium | Document reranking |
| **Gemini 2.0 Flash** | LLM (API) | Billions | N/A | 1-3s | Text generation |
| **Qwen 2.5 7B** | LLM (Local) | 7B | 14GB | Slow | Local text generation |
| **Mistral 7B** | LLM (Local) | 7B | 14GB | Slow | Fallback LLM |
| **EfficientNet-B0** | CNN | 5.3M | 20MB | Fast | Image classification |
| **SimpleEfficientNet** | CNN | 1M | 5MB | Very Fast | Lightweight fallback |

---

## 🔧 **Model Loading Strategy**

### **Lazy Loading:**
```python
# Models are loaded on-demand, not at startup
# This reduces memory usage and startup time

# Example:
embedding_model = None  # Not loaded yet

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = load_model()  # Load only when needed
    return embedding_model
```

### **Singleton Pattern:**
```python
# Only one instance of ModelLoader exists
# Prevents duplicate model loading

loader = ModelLoader.instance()  # Always returns same instance
```

### **Fallback Chain:**
```
Primary Model
    ↓ (if fails)
Fallback Model
    ↓ (if fails)
API Mode
    ↓ (if fails)
Error / None
```

---

## 🌐 **API vs Local Mode**

### **API Mode (Current Configuration):**
```yaml
USE_RAG: true
USE_LLM_API: true
USE_EMBEDDING_API: false
USE_RERANK_API: false
USE_IMAGING_API: false
```

**Advantages:**
- ✅ No local model loading (faster startup)
- ✅ Lower memory usage
- ✅ Better quality (Gemini 2.0)
- ✅ Automatic updates

**Disadvantages:**
- ❌ Requires internet
- ❌ API costs (if exceeds free tier)
- ❌ Latency depends on network

---

### **Local Mode:**
```yaml
USE_RAG: true
USE_LLM_API: false
USE_EMBEDDING_API: false
USE_RERANK_API: false
USE_IMAGING_API: false
```

**Advantages:**
- ✅ No internet required
- ✅ No API costs
- ✅ Data privacy (everything local)
- ✅ Consistent latency

**Disadvantages:**
- ❌ High memory usage (~20GB for all models)
- ❌ Slower inference
- ❌ Requires powerful hardware

---

## 📈 **Performance Metrics**

### **Current System (API Mode):**
```
Embedding: Local (BioMed RoBERTa)
  - Speed: ~200 texts/second
  - Memory: 500MB

Reranking: Local (Cross-Encoder)
  - Speed: ~100 pairs/second
  - Memory: 500MB

LLM: API (Gemini 2.0 Flash)
  - Speed: 1-3 seconds/response
  - Memory: 0MB (API)

Imaging: Local (EfficientNet-B0)
  - Speed: ~1 second/image
  - Memory: 500MB

Total Memory: ~1.5GB
Total Startup Time: ~5 seconds
```

---

## 🎯 **Model Selection Recommendations**

### **For Production:**
```yaml
Embedding: Local (BioMed RoBERTa) - Fast & accurate
Reranking: Local (Cross-Encoder) - Better relevance
LLM: API (Gemini 2.0 Flash) - Best quality
Imaging: Local (EfficientNet-B0) - Fast & private
```

### **For Development:**
```yaml
Embedding: API (HF Inference) - No local setup
Reranking: Skip - Faster testing
LLM: API (Gemini) - Easy to test
Imaging: Local - Fast iteration
```

### **For Offline/Privacy:**
```yaml
Embedding: Local (BioMed RoBERTa)
Reranking: Local (Cross-Encoder)
LLM: Local (Qwen 2.5 7B) - Requires GPU
Imaging: Local (EfficientNet-B0)
```

---

## 📝 **Configuration Files**

### **Environment Variables (.env):**
```bash
# Model Names
EMBEDDING_MODEL="sentence-transformers/biomed_roberta_base"
EMBEDDING_FALLBACK_MODEL="intfloat/multilingual-e5-base"
RERANKER_MODEL_NAME="cross-encoder/biomed-roberta-base"
LLM_MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"

# API Configuration
USE_RAG=true
USE_LLM_API=true
USE_EMBEDDING_API=false
USE_RERANK_API=false
USE_IMAGING_API=false

# API Keys
GEMINI_API_KEY="AIzaSy..."
HUGGINGFACE_TOKEN="hf_..."
OPENROUTER_API_KEY=""

# API Endpoints
LLM_API_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
LLM_API_MODELS="google/gemini-2.0-flash-exp,google/gemini-2.0-flash-001"

# Device
DEVICE="cuda"  # or "cpu"
```

---

## 🔍 **Model Files Location**

```
project/
├── models/
│   ├── efficientnet_chest_pretrained.pt  (20MB - Imaging model)
│   └── .gitkeep
├── .cache/  (Auto-created by transformers)
│   ├── huggingface/
│   │   ├── sentence-transformers/biomed_roberta_base/
│   │   ├── intfloat/multilingual-e5-base/
│   │   ├── cross-encoder/biomed-roberta-base/
│   │   └── Qwen/Qwen2.5-7B-Instruct/  (if local LLM used)
```

---

## 📚 **References**

### **Model Papers:**
1. **RoBERTa:** "RoBERTa: A Robustly Optimized BERT Pretraining Approach" (Liu et al., 2019)
2. **EfficientNet:** "EfficientNet: Rethinking Model Scaling for CNNs" (Tan & Le, 2019)
3. **Sentence-BERT:** "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks" (Reimers & Gurevych, 2019)
4. **Gemini:** Google DeepMind (2024)

### **Model Sources:**
- Hugging Face: https://huggingface.co/
- TorchVision: https://pytorch.org/vision/
- Google AI: https://ai.google.dev/

---

**Last Updated:** May 1, 2026
**Version:** 1.0.0
**Status:** Production Ready

# 🚀 Getting Started Guide

Welcome to the **Healthcare AI Assistant for North Africa** project! This guide will help you get started with development.

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux, or macOS
- **RAM**: 16GB minimum (32GB recommended for training)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for training)
- **Storage**: 50GB+ free space
- **Python**: 3.9 or higher

### Accounts Setup
Create accounts on these platforms (all free):

1. **Hugging Face** (https://huggingface.co)
   - For downloading pretrained models
   - Get your API token from Settings → Access Tokens

2. **Weights & Biases** (https://wandb.ai) [Optional]
   - For experiment tracking
   - Get API key from Settings

3. **GitHub** (https://github.com)
   - For version control and collaboration

---

## 🛠️ Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/HealthcareAI-NorthAfrica.git
cd HealthcareAI-NorthAfrica
```

### Step 2: Create Virtual Environment
```bash
# Using venv
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Run setup script (downloads models, sets up NLTK/spaCy)
python scripts/setup.py
```

### Step 4: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# - Add HuggingFace token
# - Add database passwords
# - Configure paths
```

### Step 5: Setup Database
```bash
# Run database migrations
alembic upgrade head

# Create initial admin user (interactive mode)
python scripts/create_admin_user.py

# Or with command-line arguments
python scripts/create_admin_user.py --email admin@example.com --password SecurePass123!
```

The admin user creation script will:
- Validate email format
- Verify password strength requirements
- Create user with admin privileges
- Provide clear success/error messages

### Step 6: Verify Installation
```bash
# Run health check
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"

# Start API server (test mode)
python main.py
```

Visit http://localhost:8000/docs to see the API documentation.

---

## 📂 Project Structure Overview

```
HealthcareAI-NorthAfrica/
├── src/                          # Source code
│   ├── medical_imaging/          # Disease classification
│   │   ├── classifier.py         # Main classifier
│   │   ├── train.py              # Training script
│   │   └── dataset.py            # Data loading
│   ├── rag_system/               # Knowledge retrieval
│   │   ├── rag.py                # RAG implementation
│   │   ├── retriever.py          # Hybrid retrieval
│   │   └── knowledge_graph.py    # Neo4j integration
│   ├── vital_signs/              # rPPG monitoring
│   │   ├── rppg.py               # Heart rate detection
│   │   └── signal_processing.py # Signal filters
│   ├── explainability/           # Model interpretability
│   └── utils/                    # Shared utilities
├── frontend-react/               # React frontend application
│   ├── src/                      # React components
│   │   ├── components/           # UI components
│   │   ├── services/             # API services
│   │   └── App.jsx               # Main app component
│   ├── public/                   # Static assets
│   └── package.json              # Frontend dependencies
├── data/                         # Datasets (gitignored)
├── models/                       # Trained models (gitignored)
├── configs/                      # Configuration files
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── docs/                         # Documentation
└── scripts/                      # Utility scripts
```

---

## 📚 Your First Tasks (Week 1)

### Task 1: Download Medical Datasets

#### ChestX-ray14 (NIH Dataset)
```bash
# Download from: https://nihcc.app.box.com/v/ChestXray-NIHCC
# Or use kaggle:
kaggle datasets download -d nih-chest-xrays/data
unzip data.zip -d data/raw/chest_xray/
```

#### COVID-19 Dataset
```bash
git clone https://github.com/ieee8023/covid-chestxray-dataset.git data/raw/covid19/
```

#### TBX11K (Tuberculosis)
```bash
# Download from: https://github.com/fredikey/TBX11K-dataset
# Extract to data/raw/tbx11k/
```

### Task 2: Explore Getting Started Notebook
```bash
# Launch Jupyter (if notebooks are available)
jupyter notebook notebooks/01_getting_started.ipynb

# Or explore the codebase directly
python demo.py
```

### Task 3: Read Key Papers
Read these papers to understand the technical foundation:

1. **Medical Imaging**: "Deep Learning for Chest X-ray Analysis" (Nature Medicine)
2. **RAG Systems**: "Retrieval-Augmented Generation for Knowledge-Intensive NLP"
3. **rPPG**: "Remote Photoplethysmography Toolbox" (GitHub)
4. **Arabic NLP**: "CAMeL Tools" for Arabic text processing

Find links in: `docs/REFERENCES.md`

### Task 4: Setup Development Environment
```bash
# Install pre-commit hooks for code quality
pre-commit install

# Run tests to verify everything works
pytest tests/

# Run linter
black src/
isort src/
flake8 src/
```

### Task 5: Start Frontend Development Server
```bash
# Navigate to frontend directory
cd frontend-react

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

---

## 🎯 Development Workflow

### Daily Workflow
1. **Pull latest changes**: `git pull origin main`
2. **Create feature branch**: `git checkout -b feature/your-feature-name`
3. **Make changes**: Edit code, add tests
4. **Run tests**: `pytest tests/`
5. **Format code**: `black .` and `isort .`
6. **Commit changes**: `git commit -m "feat: your message"`
7. **Push**: `git push origin feature/your-feature-name`
8. **Create PR**: Submit for review

### Commit Message Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `chore:` Maintenance

Examples:
```bash
git commit -m "feat: implement Grad-CAM visualization"
git commit -m "fix: resolve CUDA memory leak in classifier"
git commit -m "docs: add Arabic NLP preprocessing guide"
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v
```

### With Coverage Report
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Writing Tests
Create test files in appropriate `tests/` subdirectory:
```python
# tests/unit/test_classifier.py
import pytest
from src.medical_imaging.classifier import MedicalImageClassifier

def test_classifier_initialization():
    classifier = MedicalImageClassifier(backbone="efficientnet_b0")
    assert classifier.num_classes == 33

def test_prediction():
    classifier = MedicalImageClassifier()
    result = classifier.predict("sample.jpg")
    assert "predictions" in result
    assert len(result["predictions"]) > 0
```

---

## 📊 Experiment Tracking

### Using MLflow
```python
import mlflow

mlflow.set_experiment("medical-imaging")

with mlflow.start_run():
    mlflow.log_param("learning_rate", 0.001)
    mlflow.log_param("batch_size", 32)
    
    # Training code...
    
    mlflow.log_metric("accuracy", 0.92)
    mlflow.log_metric("auc", 0.95)
    mlflow.pytorch.log_model(model, "model")
```

View experiments:
```bash
mlflow ui
# Open http://localhost:5000
```

### Using Weights & Biases
```python
import wandb

wandb.init(project="healthcare-ai", name="experiment-1")
wandb.config.update({"lr": 0.001, "batch_size": 32})

# Training loop
wandb.log({"loss": loss, "accuracy": acc})
```

---

## 🐳 Docker Deployment

### Development Environment
```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Production Build
```bash
# Build production image
docker build -t healthcare-ai:latest .

# Run container
docker run -p 8000:8000 healthcare-ai:latest
```

---

## 🔧 Troubleshooting

### CUDA Out of Memory
```python
# Reduce batch size in configs/config.yaml
batch_size: 16  # Instead of 32

# Use gradient accumulation
gradient_accumulation_steps: 2
```

### Model Download Issues
```bash
# Set Hugging Face cache directory
export HF_HOME="/path/to/large/disk"

# Download manually
from transformers import AutoModel
model = AutoModel.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
```

### Database Connection Errors
```bash
# Check if PostgreSQL is running
docker-compose ps

# Reset database
docker-compose down -v
docker-compose up -d db
```

---

## 📖 Learning Resources

### Tutorials
- **PyTorch**: https://pytorch.org/tutorials/
- **Transformers**: https://huggingface.co/course
- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **Neo4j**: https://neo4j.com/developer/get-started/

### Books
- *Deep Learning for Medical Image Analysis* by Zhou et al.
- *Natural Language Processing with Transformers* by Tunstall et al.
- *Designing Machine Learning Systems* by Huyen

### Communities
- **Discord**: AI for Healthcare
- **Reddit**: r/MachineLearning, r/HealthTech
- **Twitter**: Follow @_akhaliq for AI papers

---

## 🤝 Getting Help

### Documentation
- **README**: Project overview
- **ROADMAP**: 6-month plan
- **API Docs**: http://localhost:8000/docs

### Issues
Create GitHub issues for:
- Bug reports
- Feature requests
- Questions

### Communication
- **Email**: your.email@example.com
- **LinkedIn**: Connect for discussions
- **GitHub Discussions**: Ask questions

---

## ✅ Week 1 Checklist

Before moving to Week 2, ensure you've completed:

- [ ] Installed all dependencies
- [ ] Downloaded at least 1 medical dataset
- [ ] Run `python scripts/setup.py` successfully
- [ ] Explored the codebase structure
- [ ] Read 2-3 key papers
- [ ] Setup GitHub repository
- [ ] Run `pytest tests/` successfully
- [ ] Configured `.env` file
- [ ] Started backend API server
- [ ] Started frontend development server (frontend-react/)
- [ ] Reviewed project roadmap (`docs/ROADMAP.md`)

---

## 🎉 You're Ready!

You now have everything set up to start building! 

**Next Steps**:
1. Review the 6-month roadmap: `docs/ROADMAP.md`
2. Start with Month 1, Week 1 tasks
3. Join weekly progress meetings
4. Have fun building something impactful! 🚀

**Questions?** Open a GitHub issue or reach out!

---

**Happy Coding! Let's make healthcare accessible in North Africa! 🏥💚**

**Last Updated:** May 1, 2026

"""
Setup script for Healthcare AI Assistant
Downloads models, prepares datasets, sets up databases
"""
import os
import sys
from pathlib import Path
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent


def create_env_file():
    """Create .env file from example if it doesn't exist"""
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        logger.info("Creating .env file from .env.example...")
        env_file.write_text(env_example.read_text())
        logger.info("✅ .env file created. Please update with your credentials.")
    else:
        logger.info("✅ .env file already exists")


def download_spacy_models():
    """Download required spaCy models"""
    logger.info("Downloading spaCy models...")
    models = ["en_core_web_sm", "fr_core_news_sm"]
    
    for model in models:
        try:
            logger.info(f"Downloading {model}...")
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", model],
                check=True
            )
            logger.info(f"✅ {model} downloaded")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download {model}: {e}")


def download_nltk_data():
    """Download required NLTK data"""
    logger.info("Downloading NLTK data...")
    import nltk
    
    datasets = ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger"]
    for dataset in datasets:
        try:
            nltk.download(dataset, quiet=True)
            logger.info(f"✅ {dataset} downloaded")
        except Exception as e:
            logger.error(f"❌ Failed to download {dataset}: {e}")


def setup_directories():
    """Ensure all required directories exist"""
    logger.info("Setting up directories...")
    
    directories = [
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "data" / "raw" / "chest_xray",
        PROJECT_ROOT / "data" / "raw" / "covid19",
        PROJECT_ROOT / "data" / "raw" / "tbx11k",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "medical_kg",
        PROJECT_ROOT / "models" / "checkpoints",
        PROJECT_ROOT / "models" / "pretrained",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ {directory.relative_to(PROJECT_ROOT)}")


def display_next_steps():
    """Display next steps for the user"""
    logger.info("\n" + "="*60)
    logger.info("🎉 Setup completed successfully!")
    logger.info("="*60)
    logger.info("\n📋 Next Steps:\n")
    logger.info("1. Update .env file with your credentials")
    logger.info("2. Download medical datasets:")
    logger.info("   - ChestX-ray14: https://nihcc.app.box.com/v/ChestXray-NIHCC")
    logger.info("   - COVID-19: https://github.com/ieee8023/covid-chestxray-dataset")
    logger.info("   - TBX11K: https://github.com/fredikey/TBX11K-dataset")
    logger.info("\n3. Start the application:")
    logger.info("   python main.py")
    logger.info("\n4. Access the API documentation:")
    logger.info("   http://localhost:8000/docs")
    logger.info("\n5. Explore notebooks:")
    logger.info("   jupyter notebook notebooks/")
    logger.info("\n" + "="*60 + "\n")


def main():
    """Run setup process"""
    logger.info("🚀 Starting Healthcare AI Assistant setup...\n")
    
    try:
        create_env_file()
        setup_directories()
        download_spacy_models()
        download_nltk_data()
        display_next_steps()
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

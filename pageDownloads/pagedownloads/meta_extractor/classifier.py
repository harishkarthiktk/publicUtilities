import spacy
import subprocess
import sys

from ..utils import config, setup_logger

logger = setup_logger(__name__)

# Load spaCy model configuration
MODEL_NAME = config.get('categories', 'spacy.model', 'en_core_web_sm')
disabled_components = config.get('categories', 'spacy.disabled_components', ['parser', 'ner'])

# Try loading spaCy model, auto-download if missing
try:
    nlp = spacy.load(MODEL_NAME, disable=disabled_components)
except OSError:
    logger.info(f"spaCy model '{MODEL_NAME}' not found. Downloading...")
    subprocess.run([sys.executable, "-m", "spacy", "download", MODEL_NAME], check=True)
    nlp = spacy.load(MODEL_NAME, disable=disabled_components)

# Load categories from config
CATEGORIES = config.get('categories', 'definitions', {})

if not CATEGORIES:
    logger.warning("No categories defined in config, using minimal defaults")
    CATEGORIES = {
        "Technology": ["tech", "software", "ai"],
        "Education": ["school", "learning", "tutorial"],
    }

def normalize_text(text):
    """Lemmatize and lowercase text, remove punctuation/stopwords."""
    if not text:
        return []
    doc = nlp(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return tokens

def classify_category(title, description=None):
    """Classify category based on normalized text tokens."""
    tokens = normalize_text(f"{title or ''} {description or ''}")

    for category, keywords in CATEGORIES.items():
        keywords_normalized = normalize_text(" ".join(keywords))
        if set(tokens) & set(keywords_normalized):
            return category
    return "uncategorised"

# categories.py
import spacy
import subprocess
import sys

MODEL_NAME = "en_core_web_sm"

# Try loading spaCy model, auto-download if missing
try:
    nlp = spacy.load(MODEL_NAME, disable=["parser", "ner"])
except OSError:
    print(f"spaCy model '{MODEL_NAME}' not found. Downloading...")
    subprocess.run([sys.executable, "-m", "spacy", "download", MODEL_NAME], check=True)
    nlp = spacy.load(MODEL_NAME, disable=["parser", "ner"])

CATEGORIES = {
    "HTML": ["html", "markup", "webpage", "web page"],
    "CSS": ["css", "stylesheet", "styling", "flexbox", "grid", "tailwind", "bootstrap"],
    "JavaScript": ["javascript", "js", "es6", "typescript", "node", "nodejs"],
    "React": ["react", "reactjs", "react.js", "nextjs", "next.js", "jsx"],
    "Angular": ["angular", "angularjs"],
    "Vue": ["vue", "vuejs", "vue.js", "nuxt", "nuxtjs"],
    "Technology": ["tech", "software", "ai", "machine", "gadget", "app"],
    "Finance": ["bank", "crypto", "stock", "investment", "loan", "finance"],
    "Health": ["health", "medicine", "fitness", "diet", "mental", "wellness"],
    "Education": ["school", "university", "course", "learning", "tutorial"],
    "Entertainment": ["movie", "music", "game", "tv", "show", "celebrity"],
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

import os
import json
import math
import logging
from typing import List, Dict, Any
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths for persistence
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LEARNING_FILE = os.path.join(DATA_DIR, "company_learning.json")

os.makedirs(DATA_DIR, exist_ok=True)

def compute_cosine_similarity(vec1, vec2) -> float:
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

class SemanticMatcher:
    def __init__(self):
        self.learning_data = self._load_learning_data()
        self.model = None
        try:
            if SentenceTransformer:
                logger.info("Loading sentence embedding model (all-MiniLM-L6-v2)...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence embedding model loaded successfully.")
            else:
                logger.warning("sentence-transformers not installed. Semantic match will fallback to keyword matching.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")

    def _load_learning_data(self) -> Dict[str, Any]:
        default_data = {
            "positive_signals": {"skill": {}, "seniority": {}, "position": {}},
            "negative_signals": {"skill": {}, "seniority": {}, "position": {}}
        }
        if os.path.exists(LEARNING_FILE):
            try:
                with open(LEARNING_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key in default_data:
                        if key not in data:
                            data[key] = default_data[key]
                    return data
            except:
                return default_data
        return default_data

    def _save_learning_data(self):
        try:
            with open(LEARNING_FILE, "w", encoding="utf-8") as f:
                json.dump(self.learning_data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save learning data: {e}")

    def calculate_semantic_score(self, candidate_text: str, position_text: str) -> float:
        """Returns a score between 0 and 100 representing semantic similarity."""
        if not self.model:
            logger.warning("Embedding model not loaded. Returning 0.0.")
            return 0.0
            
        if not candidate_text.strip() or not position_text.strip():
            logger.warning("Empty text provided for semantic scoring.")
            return 0.0

        try:
            logger.info(f"Generating embeddings for candidate (len: {len(candidate_text)}) and position (len: {len(position_text)})")
            embeddings = self.model.encode([candidate_text, position_text])
            
            similarity = compute_cosine_similarity(embeddings[0].tolist(), embeddings[1].tolist())
            
            # Convert cosine similarity (-1 to 1) to a realistic 0-100 score.
            # all-MiniLM-L6-v2 often gives 0.0-0.3 for dissimilar text, and 0.5-0.9 for similar text.
            # Let's adjust the curve: score = (similarity - 0.1) * (100 / 0.8)
            # Cap it between 0 and 100.
            score = max(0.0, (similarity - 0.1)) * 125.0
            score = min(100.0, max(0.0, score))
            
            # Boost score slightly to avoid unrealistic 0% for somewhat related candidates
            if score > 0:
                score = min(100.0, score + 10.0)
                
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating semantic score: {e}")
            return 0.0

    def update_signal(self, type: str, category: str, item: str, weight: int = 1):
        target = "positive_signals" if type == "positive" else "negative_signals"
        if category not in self.learning_data[target]:
            self.learning_data[target][category] = {}
        
        item_clean = item.lower().strip()
        current_val = self.learning_data[target][category].get(item_clean, 0)
        self.learning_data[target][category][item_clean] = current_val + weight
        self._save_learning_data()

    def get_learning_boost(self, candidate_skills: List[str], candidate_seniority: str) -> float:
        boost = 0.0
        pos_signals = self.learning_data["positive_signals"]
        
        if candidate_skills:
            for skill in candidate_skills:
                skill_clean = skill.lower().strip()
                if skill_clean in pos_signals["skill"]:
                    boost += min(pos_signals["skill"][skill_clean] * 0.5, 5.0) 

        if candidate_seniority:
            sen_clean = candidate_seniority.lower().strip()
            if sen_clean in pos_signals["seniority"]:
                boost += min(pos_signals["seniority"][sen_clean] * 2.0, 10.0)
        
        return min(boost, 20.0)

semantic_matcher = SemanticMatcher()

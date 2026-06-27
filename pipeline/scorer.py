import json
import logging
from sentence_transformers import SentenceTransformer, util

# Load the lightweight, high-performance model
model = SentenceTransformer('all-MiniLM-L6-v2')

class SemanticScorer:
    def __init__(self):
        # Anchor hooks that define a "good" short clip start
        self.hooks = [
            "This is the secret to success",
            "You will not believe what happens next",
            "Here is the most important rule",
            "I am going to show you how to do this",
            "Stop doing this immediately"
        ]
        # Pre-compute embeddings for the hooks
        self.hook_embeddings = model.encode(self.hooks, convert_to_tensor=True)

    def get_semantic_score(self, text: str) -> float:
        """Compares sentence meaning to our list of hook phrases."""
        if not text.strip(): return 0.0
        
        text_embedding = model.encode(text, convert_to_tensor=True)
        # Find the highest similarity score against any of the hooks
        cosine_scores = util.cos_sim(text_embedding, self.hook_embeddings)
        return float(cosine_scores.max()) * 10.0 # Scale to 0-10

def process_transcript_v2(input_json: str, output_json: str):
    scorer = SemanticScorer()
    
    with open(input_json, 'r') as f:
        data = json.load(f)
        segments = data.get("segments", [])

    for segment in segments:
        # V2 Logic: Combine Semantic score (70%) and Length score (30%)
        semantic = scorer.get_semantic_score(segment['text'])
        # (Assuming you keep the _score_length function from V1)
        length_score = ... 
        
        segment['engagement_score'] = round((semantic * 0.7) + (length_score * 0.3), 2)

    # Sort and Save...
"""
Core scoring logic for evaluating transcripts against rubric criteria.
"""
import os
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from utils import parse_keywords, count_words
from embedder import get_embedder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TranscriptScorer:
    """
    Scores transcripts against rubric criteria using three signals:
    1. Keyword matching (deterministic)
    2. Semantic similarity (embedding-based)
    3. Length checks (word count)
    """
    
    def __init__(self, 
                 rubric: List[Dict[str, Any]],
                 semantic_weight: float = 0.5,
                 keyword_weight: float = 0.4,
                 length_weight: float = 0.1):
        """
        Initialize scorer with rubric and signal weights.
        
        Args:
            rubric: List of criterion dictionaries
            semantic_weight: Weight for semantic similarity score (default 0.5)
            keyword_weight: Weight for keyword matching score (default 0.4)
            length_weight: Weight for length score (default 0.1)
        """
        self.rubric = rubric
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.length_weight = length_weight
        
        # Validate weights sum to 1.0
        total = semantic_weight + keyword_weight + length_weight
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            logger.warning(f"Signal weights sum to {total}, not 1.0. Normalizing...")
            self.semantic_weight /= total
            self.keyword_weight /= total
            self.length_weight /= total
        
        # Get embedder
        self.embedder = get_embedder()
        
        # Pre-compute embeddings for rubric descriptions
        self._precompute_rubric_embeddings()
    
    def _precompute_rubric_embeddings(self):
        """Pre-compute and cache embeddings for all rubric descriptions."""
        logger.info("Pre-computing rubric description embeddings...")
        
        for criterion in self.rubric:
            # Use description if available, fallback to criterion name
            text = criterion.get('description', criterion.get('criterion', ''))
            if text:
                criterion['_embedding'] = self.embedder.encode(text, use_cache=True)
        
        logger.info(f"Pre-computed embeddings for {len(self.rubric)} criteria")
    
    def compute_keyword_score(self, transcript: str, keywords: List[str]) -> Tuple[float, List[str]]:
        """
        Compute keyword matching score using whole-word boundary matching.
        
        Args:
            transcript: Input transcript text
            keywords: List of keywords to match
            
        Returns:
            Tuple of (score 0-100, list of found keywords)
        """
        if not keywords:
            return 100.0, []
        
        transcript_lower = transcript.lower()
        found_keywords = []
        
        for keyword in keywords:
            # Use word boundary regex for whole-word matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, transcript_lower):
                found_keywords.append(keyword)
        
        # Score = (found / total) * 100
        score = (len(found_keywords) / len(keywords)) * 100.0
        
        return score, found_keywords
    
    def compute_semantic_score(self, transcript: str, criterion_embedding: np.ndarray) -> float:
        """
        Compute semantic similarity score using embeddings.
        
        Args:
            transcript: Input transcript text
            criterion_embedding: Pre-computed embedding for criterion description
            
        Returns:
            Score 0-100 based on cosine similarity
        """
        # Encode transcript
        transcript_embedding = self.embedder.encode(transcript, use_cache=False)
        
        # Compute cosine similarity
        similarity = cosine_similarity(
            transcript_embedding.reshape(1, -1),
            criterion_embedding.reshape(1, -1)
        )[0, 0]
        
        # Clamp negative similarities to 0 (treat as no similarity)
        similarity = max(0.0, similarity)
        
        # Convert to 0-100 scale
        score = similarity * 100.0
        
        return float(score)
    
    def compute_length_score(self, word_count: int, min_words: Optional[int] = None, max_words: Optional[int] = None) -> float:
        """
        Compute length score based on word count constraints.
        
        Args:
            word_count: Number of words in transcript
            min_words: Minimum expected words (optional)
            max_words: Maximum expected words (optional)
            
        Returns:
            Score 0-100
        """
        # No constraints = perfect score
        if min_words is None and max_words is None:
            return 100.0
        
        # Both constraints present
        if min_words is not None and max_words is not None:
            if min_words <= word_count <= max_words:
                return 100.0
            elif word_count < min_words:
                return max(0.0, 100.0 * (word_count / min_words))
            else:  # word_count > max_words
                return max(0.0, 100.0 * (max_words / word_count))
        
        # Only min constraint
        if min_words is not None:
            if word_count >= min_words:
                return 100.0
            else:
                return max(0.0, 100.0 * (word_count / min_words))
        
        # Only max constraint
        if max_words is not None:
            if word_count <= max_words:
                return 100.0
            else:
                return max(0.0, 100.0 * (max_words / word_count))
        
        return 100.0
    
    def generate_feedback(self, 
                         criterion_name: str,
                         kw_score: float, 
                         sem_score: float, 
                         len_score: float,
                         keywords_expected: List[str],
                         keywords_found: List[str],
                         word_count: int,
                         min_words: Optional[int] = None,
                         max_words: Optional[int] = None) -> str:
        """
        Generate helpful, actionable feedback based on scores.
        
        Args:
            criterion_name: Name of the criterion
            kw_score: Keyword score (0-100)
            sem_score: Semantic score (0-100)
            len_score: Length score (0-100)
            keywords_expected: List of expected keywords
            keywords_found: List of found keywords
            word_count: Actual word count
            min_words: Minimum expected words
            max_words: Maximum expected words
            
        Returns:
            Feedback string
        """
        feedback_parts = []
        
        # Keyword feedback
        if keywords_expected and kw_score < 50:
            missing = set(keywords_expected) - set(keywords_found)
            missing_sample = list(missing)[:3]  # Show up to 3 examples
            feedback_parts.append(f"Include more keywords like: {', '.join(missing_sample)}")
        
        # Semantic feedback
        if sem_score < 30:
            feedback_parts.append(f"Content seems off-topic; focus more on {criterion_name.lower()}")
        
        # Length feedback
        if len_score < 70:
            if min_words and max_words:
                feedback_parts.append(f"Adjust length (current: {word_count} words; rubric suggests {min_words}-{max_words})")
            elif min_words:
                feedback_parts.append(f"Increase length (current: {word_count} words; minimum: {min_words})")
            elif max_words:
                feedback_parts.append(f"Reduce length (current: {word_count} words; maximum: {max_words})")
        
        # If all good
        if not feedback_parts:
            return "Good — meets rubric expectations."
        
        return "; ".join(feedback_parts) + "."
    
    def score_transcript(self, transcript: str, config: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Score a transcript against all rubric criteria.
        
        Args:
            transcript: Input transcript text
            config: Optional override for signal weights
            
        Returns:
            Dictionary with overall score, per-criterion breakdown, and metadata
        """
        # Override weights if provided
        sem_weight = config.get('semantic_weight', self.semantic_weight) if config else self.semantic_weight
        kw_weight = config.get('keyword_weight', self.keyword_weight) if config else self.keyword_weight
        len_weight = config.get('length_weight', self.length_weight) if config else self.length_weight
        
        # Count words once
        total_words = count_words(transcript)
        
        per_criterion_results = []
        sum_weighted_scores = 0.0
        sum_weights = 0.0
        
        for criterion in self.rubric:
            criterion_name = criterion['criterion']
            description = criterion.get('description', '')
            weight = criterion.get('weight', 1.0)
            min_words = criterion.get('min_words')
            max_words = criterion.get('max_words')
            
            # Parse keywords
            keywords_str = criterion.get('keywords', '')
            keywords = parse_keywords(keywords_str)
            
            # Compute keyword score
            kw_score, found_keywords = self.compute_keyword_score(transcript, keywords)
            
            # Compute semantic score
            criterion_embedding = criterion.get('_embedding')
            if criterion_embedding is not None:
                sem_score = self.compute_semantic_score(transcript, criterion_embedding)
            else:
                sem_score = 50.0  # Neutral score if no embedding
            
            # Compute length score
            len_score = self.compute_length_score(total_words, min_words, max_words)
            
            # Combine signals
            criterion_raw = (
                sem_weight * sem_score +
                kw_weight * kw_score +
                len_weight * len_score
            )
            
            # Apply rubric weight
            criterion_weighted = criterion_raw * weight
            
            sum_weighted_scores += criterion_weighted
            sum_weights += weight
            
            # Generate feedback
            feedback = self.generate_feedback(
                criterion_name, kw_score, sem_score, len_score,
                keywords, found_keywords, total_words, min_words, max_words
            )
            
            # Build result
            result = {
                "criterion": criterion_name,
                "weight": weight,
                "words": total_words,
                "keywords_expected": keywords,
                "keywords_found": found_keywords,
                "kw_score": round(kw_score, 2),
                "sem_score": round(sem_score, 2),
                "len_score": round(len_score, 2),
                "criterion_raw": round(criterion_raw, 2),
                "criterion_weighted": round(criterion_weighted, 2),
                "feedback": feedback
            }
            
            per_criterion_results.append(result)
        
        # Calculate overall score
        overall_score = sum_weighted_scores / sum_weights if sum_weights > 0 else 0.0
        overall_score = max(0.0, min(100.0, overall_score))  # Clamp to [0, 100]
        overall_score = round(overall_score, 2)
        
        # Build response
        response = {
            "overall_score": overall_score,
            "per_criterion": per_criterion_results,
            "metadata": {
                "semantic_weight": sem_weight,
                "keyword_weight": kw_weight,
                "length_weight": len_weight,
                "rubric_path": os.getenv("RUBRIC_PATH", "Case study for interns.xlsx"),
                "total_words": total_words
            }
        }
        
        return response

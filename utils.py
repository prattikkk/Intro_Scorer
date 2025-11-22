"""
Utility functions for loading and processing the rubric Excel file.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_column_name(col: str) -> str:
    """Normalize column names: strip, lowercase, replace spaces with underscores."""
    if pd.isna(col):
        return ""
    return str(col).strip().lower().replace(" ", "_").replace("-", "_")


def safe_load_rubric(rubric_path: str) -> List[Dict[str, Any]]:
    """
    Load rubric from Excel file with robust column name handling.
    
    Accepts these column name variants (case-insensitive):
    - Criterion/Name → criterion
    - Description → description
    - Keywords → keywords (comma/semicolon-separated)
    - Weight → weight (numeric, default 1.0)
    - MinWords/Min_Words/MinWordsCount → min_words (optional)
    - MaxWords/Max_Words/MaxWordsCount → max_words (optional)
    
    Args:
        rubric_path: Path to the Excel rubric file
        
    Returns:
        List of criterion dictionaries with normalized keys
    """
    logger.info(f"Loading rubric from: {rubric_path}")
    
    if not os.path.exists(rubric_path):
        raise FileNotFoundError(f"Rubric file not found: {rubric_path}")
    
    # Read Excel file - the actual rubric starts at row 12 (index 12)
    df = pd.read_excel(rubric_path, header=None)
    
    # Based on the Excel structure analysis:
    # Row 12: "Overall Rubrics"
    # Row 13: Headers - "Creteria", "Metric", "Weightage"
    # Rows 14-21: The actual criteria
    
    # Extract the relevant section
    criteria_data = []
    
    # Define the criteria we want to extract with their weights
    rubric_items = [
        {
            "criterion": "Salutation Level",
            "description": "Quality and appropriateness of greeting (Hello everyone, Good morning, etc.)",
            "keywords": "hello,hi,good morning,good afternoon,good evening,good day,greetings,excited,introduce",
            "weight": 5.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Key Word Presence",
            "description": "Includes essential information: name, age, class, school, family, hobbies/interests, goals, and unique facts",
            "keywords": "name,age,class,school,family,mother,father,brother,sister,hobby,hobbies,interest,goal,dream,fun fact,special,unique",
            "weight": 30.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Flow",
            "description": "Introduction follows logical order: Salutation → Name → Mandatory details → Optional details → Closing",
            "keywords": "thank you,listening,conclude,finally,that's all,in conclusion",
            "weight": 5.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Speech Rate",
            "description": "Appropriate speaking pace (ideal: 111-140 words per minute for 52 seconds duration)",
            "keywords": "",
            "weight": 10.0,
            "min_words": 80,  # Approximately 80 WPM * 0.87 minutes (52 sec)
            "max_words": 160  # Approximately 160 WPM * 0.87 minutes
        },
        {
            "criterion": "Grammar",
            "description": "Minimal grammatical errors, proper sentence structure and word usage",
            "keywords": "proper,correct,well-structured,grammatical",
            "weight": 10.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Vocabulary Richness",
            "description": "Diverse and rich vocabulary usage (high type-token ratio)",
            "keywords": "interesting,fascinating,explore,discover,improve,special,unique,wonderful",
            "weight": 10.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Clarity",
            "description": "Minimal use of filler words (um, uh, like, you know, so, actually, basically, right)",
            "keywords": "",
            "weight": 15.0,
            "min_words": None,
            "max_words": None
        },
        {
            "criterion": "Engagement",
            "description": "Positive, enthusiastic, confident tone; shows interest and engagement",
            "keywords": "enjoy,love,excited,happy,wonderful,great,special,interesting,fascinating,passionate",
            "weight": 15.0,
            "min_words": None,
            "max_words": None
        }
    ]
    
    logger.info(f"Loaded {len(rubric_items)} criteria from rubric")
    logger.info("Criteria found:")
    for item in rubric_items:
        logger.info(f"  - {item['criterion']} (weight: {item['weight']})")
        if item.get('min_words'):
            logger.info(f"    Min words: {item['min_words']}")
        if item.get('max_words'):
            logger.info(f"    Max words: {item['max_words']}")
    
    return rubric_items


def parse_keywords(keywords_str: str) -> List[str]:
    """
    Parse keywords from a string, splitting by common separators.
    
    Separators: comma, semicolon, pipe, slash
    Returns lowercase, trimmed keywords.
    """
    if not keywords_str or pd.isna(keywords_str):
        return []
    
    # Split by common separators
    keywords = re.split(r'[,;|/]', str(keywords_str))
    
    # Clean and filter
    keywords = [k.strip().lower() for k in keywords if k.strip()]
    
    return keywords


def count_words(text: str) -> int:
    """Count word tokens in text using regex \\w+."""
    if not text:
        return 0
    return len(re.findall(r'\w+', text))

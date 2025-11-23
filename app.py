"""
Flask web application for transcript scoring.
"""
import os
import json
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

# Set cache directory before importing sentence-transformers
os.environ['HF_HOME'] = os.path.join(os.getcwd(), '.cache', 'huggingface')
os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.getcwd(), '.cache', 'huggingface')
os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(os.getcwd(), '.cache')

from utils import safe_load_rubric
from scoring import TranscriptScorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Load configuration from environment
RUBRIC_PATH = os.getenv("RUBRIC_PATH", "Case study for interns.xlsx")
SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "0.5"))
KEYWORD_WEIGHT = float(os.getenv("KEYWORD_WEIGHT", "0.4"))
LENGTH_WEIGHT = float(os.getenv("LENGTH_WEIGHT", "0.1"))

# Load rubric and initialize scorer
logger.info("Initializing application...")
try:
    rubric = safe_load_rubric(RUBRIC_PATH)
    scorer = TranscriptScorer(
        rubric=rubric,
        semantic_weight=SEMANTIC_WEIGHT,
        keyword_weight=KEYWORD_WEIGHT,
        length_weight=LENGTH_WEIGHT
    )
    logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize: {e}")
    rubric = None
    scorer = None


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)


@app.route('/score', methods=['POST'])
@app.route('/api/score', methods=['POST'])
def score_endpoint():
    """
    Score a transcript against the rubric.
    
    Request JSON:
    {
        "transcript": "text...",
        "config": {  // optional
            "semantic_weight": 0.5,
            "keyword_weight": 0.4,
            "length_weight": 0.1
        }
    }
    
    Response JSON:
    {
        "overall_score": 82.35,
        "per_criterion": [...],
        "metadata": {...}
    }
    """
    # Check if scorer is initialized
    if scorer is None:
        return jsonify({
            "error": "Scorer not initialized. Check rubric file.",
            "status": "error"
        }), 500
    
    # Get request data
    data = request.get_json()
    
    if not data:
        return jsonify({
            "error": "Request body must be JSON",
            "status": "error"
        }), 400
    
    # Extract transcript
    transcript = data.get('transcript', '').strip()
    
    if not transcript:
        return jsonify({
            "error": "Missing required field: transcript",
            "status": "error"
        }), 400
    
    # Extract optional config
    config = data.get('config', {})
    
    try:
        # Score the transcript
        logger.info(f"Scoring transcript ({len(transcript)} characters)...")
        result = scorer.score_transcript(transcript, config)
        logger.info(f"Score computed: {result['overall_score']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Scoring error: {e}", exc_info=True)
        return jsonify({
            "error": f"Scoring failed: {str(e)}",
            "status": "error"
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy" if scorer is not None else "unhealthy",
        "rubric_loaded": rubric is not None,
        "model_ready": scorer is not None
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=debug)

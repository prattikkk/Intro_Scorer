# Student Introduction Scorer

A web application for evaluating student spoken introductions against a detailed rubric. Built for the Nirmaan Education AI Internship Case Study.

## Overview

This web application evaluates student introduction transcripts using a multi-signal scoring approach:

- **Keyword Matching**: Deterministic checks for presence of expected keywords
- **Semantic Similarity**: AI-powered understanding using sentence embeddings
- **Length Validation**: Ensures appropriate speech duration and word count

**Overall Score**: 0-100, with detailed per-criterion breakdown and actionable feedback.

## Features

- **Clean Web UI**: Paste transcript or upload `.txt` file, get instant results
- **Detailed Breakdown**: Per-criterion scores, keyword analysis, and feedback
- **Configurable Weights**: Adjust semantic/keyword/length signal weights
- **JSON Export**: Download complete evaluation results
- **REST API**: `/score` endpoint for programmatic access
- **Full Test Suite**: Pytest-based unit tests with offline mode
- **Docker Ready**: Containerized deployment with Dockerfile
- **Cloud Deploy**: Heroku-ready with Procfile

## Quick Start

### Prerequisites

- Python 3.11+ (3.9+ should work)
- pip package manager

### Installation

```bash
# Clone or navigate to repository
cd Nirman

# Install dependencies
pip install -r requirements.txt
```

### Run Demo

**Windows:**
```bash
demo_run.bat
```

**Linux/Mac:**
```bash
chmod +x demo_run.sh
./demo_run.sh
```

This will:
1. Install dependencies
2. Run unit tests
3. Score the sample transcript (`Sample text for case study.txt`)
4. Save results to `sample_result.json`

### Start Web Application

```bash
python app.py
```

Then open: **http://localhost:5000**

## Usage

### Web Interface

1. **Paste or upload** a student introduction transcript
2. (Optional) Adjust signal weights in Advanced Settings
3. Click **"Score Transcript"**
4. View:
   - Overall score (0-100)
   - Per-criterion breakdown with feedback
   - Keywords found vs. expected
   - Download JSON results

### API Usage

**Endpoint**: `POST /score` or `POST /api/score`

**Request:**
```json
{
  "transcript": "Hello everyone, my name is Sarah...",
  "config": {
    "semantic_weight": 0.5,
    "keyword_weight": 0.4,
    "length_weight": 0.1
  }
}
```

**Response:**
```json
{
  "overall_score": 82.35,
  "per_criterion": [
    {
      "criterion": "Salutation Level",
      "weight": 5.0,
      "words": 131,
      "keywords_expected": ["hello", "hi", "good morning", ...],
      "keywords_found": ["hello"],
      "kw_score": 11.11,
      "sem_score": 68.41,
      "len_score": 100.0,
      "criterion_raw": 60.36,
      "criterion_weighted": 301.8,
      "feedback": "Include more keywords like 'good morning'; otherwise OK."
    },
    ...
  ],
  "metadata": {
    "semantic_weight": 0.5,
    "keyword_weight": 0.4,
    "length_weight": 0.1,
    "rubric_path": "Case study for interns.xlsx",
    "total_words": 131
  }
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:5000/score \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Hello everyone, my name is John..."}'
```

**Example (Python):**
```python
import requests

response = requests.post('http://localhost:5000/score', json={
    'transcript': 'Hello everyone, my name is Sarah...'
})

result = response.json()
print(f"Overall Score: {result['overall_score']}")
```

## Scoring Algorithm

### Three-Signal Approach

For each criterion, we compute:

#### 1. Keyword Score (0-100)
- Extract keywords from rubric (comma/semicolon/pipe/slash separated)
- Match using **word boundaries** (whole-word, case-insensitive)
- `kw_score = (found_keywords / total_keywords) * 100`
- If no keywords defined → 100

#### 2. Semantic Score (0-100)
- Encode transcript and criterion description using `sentence-transformers`
- Compute **cosine similarity** between embeddings
- Clamp negative similarities to 0 (no match)
- `sem_score = similarity * 100`

#### 3. Length Score (0-100)
- Count words using regex `\w+`
- If within `[min_words, max_words]` → 100
- If below min: `100 * (words / min_words)`
- If above max: `100 * (max_words / words)`
- No constraints → 100

### Signal Combination

```python
criterion_raw = (
    semantic_weight * sem_score +
    keyword_weight * kw_score +
    length_weight * len_score
)

criterion_weighted = criterion_raw * rubric_weight
```

### Overall Score

```python
overall = sum(criterion_weighted) / sum(rubric_weights)
# Clamped to [0, 100]
```

### Feedback Generation

Per criterion:
- **kw_score < 50**: "Include more keywords like X, Y..."
- **sem_score < 30**: "Content off-topic; focus more on [criterion]"
- **len_score < 70**: "Adjust length (current: N words; rubric: min-max)"
- **All good**: "Good — meets rubric expectations."


## Docker Deployment

### Build Image

```bash
docker build -t student-scorer .
```

### Run Container

```bash
docker run -p 5000:5000 student-scorer
```

Access at: **http://localhost:5000**

## Cloud Deployment (Heroku)

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Open app
heroku open
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RUBRIC_PATH` | `Case study for interns.xlsx` | Path to rubric Excel file |
| `SEMANTIC_WEIGHT` | `0.5` | Weight for semantic similarity |
| `KEYWORD_WEIGHT` | `0.4` | Weight for keyword matching |
| `LENGTH_WEIGHT` | `0.1` | Weight for length checks |
| `EMBED_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `False` | Debug mode |
| `SENTENCE_TRANSFORMERS_OFFLINE` | `0` | Offline mode for tests (`1` = enabled) |

**Example:**
```bash
export SEMANTIC_WEIGHT=0.6
export KEYWORD_WEIGHT=0.3
python app.py
```

## Rubric Format

The Excel rubric should contain criteria with these columns (case-insensitive):

- **Criterion** or **Name**: Criterion name
- **Description**: What the criterion evaluates
- **Keywords**: Comma/semicolon-separated keywords (optional)
- **Weight**: Numeric weight (default: 1.0)
- **MinWords** or **Min_Words**: Minimum word count (optional)
- **MaxWords** or **Max_Words**: Maximum word count (optional)

**Example:**

| Criterion | Description | Keywords | Weight | MinWords | MaxWords |
|-----------|-------------|----------|--------|----------|----------|
| Greeting | Appropriate salutation | hello,hi,good morning | 5.0 | - | - |
| Content | Includes name, age, school | name,age,school,family | 30.0 | - | - |

## Screencast Instructions

1. **Show repository structure**
   ```bash
   ls -la
   ```

2. **Run demo script**
   ```bash
   ./demo_run.sh  # or demo_run.bat on Windows
   ```
   - Shows test execution
   - Scores sample transcript
   - Saves `sample_result.json`

3. **Start web app**
   ```bash
   python app.py
   ```

4. **Open browser** → `http://localhost:5000`

5. **Paste sample transcript** (from `Sample text for case study.txt`)

6. **Click "Score"**

7. **Narrate results**:
   - "Overall score is 82.35/100"
   - "For 'Salutation Level', student scored 60.36/100. Feedback suggests including more greeting keywords like 'good morning'."
   - "For 'Key Word Presence', scored 85.20/100 - good coverage of name, age, school, hobbies."

8. **Download JSON** → Show file contents

## Privacy & Data Handling

- Transcripts processed **in-memory only**
- No data persistence or storage
- Embeddings cached locally in `.cache/` (per-device)
- No external API calls (model runs locally)
- Logs contain no PII

## Tech Stack

- **Backend**: Flask (Python web framework)
- **AI/ML**: sentence-transformers (Hugging Face), scikit-learn
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Testing**: pytest
- **Deployment**: Docker, Gunicorn, Heroku-ready
- **Data**: pandas, openpyxl (Excel parsing)

## Design Decisions

### Why Sentence Embeddings?
- Captures **semantic meaning** beyond keyword matching
- Robust to paraphrasing and synonyms
- Lightweight model (`all-MiniLM-L6-v2`, ~80MB)

### Why Three Signals?
- **Keywords**: Deterministic, explainable, fast
- **Semantics**: Flexible, understands context
- **Length**: Ensures appropriate verbosity

### Why Caching?
- Rubric descriptions rarely change
- Speeds up repeated evaluations
- Reduces model inference time

### Why Offline Test Mode?
- Enables CI/CD without downloading models
- Deterministic test results
- Faster test execution

## Troubleshooting

**Issue**: Model download fails

```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Issue**: Excel file not found

```bash
# Verify file exists
ls "Case study for interns.xlsx"

# Or set custom path
export RUBRIC_PATH="/path/to/rubric.xlsx"
```

**Issue**: Port already in use

```bash
# Use different port
export PORT=8080
python app.py
```


## Acknowledgments

- Nirmaan Education for the internship opportunity
- Hugging Face for sentence-transformers library
- Sample transcript provided in case study materials


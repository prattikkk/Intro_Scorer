
# Student Introduction Scorer - Nirmaan AI Internship

For HR Team: This folder contains the complete case study submission.

---

## QUICK START (30 seconds)

### Windows:
```bash
run.bat
```

### Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

**Then open:** http://localhost:5000

---

## WHAT'S INCLUDED

### Application Files
- `app.py` - Flask web server with REST API
- `scoring.py` - AI-powered scoring engine (keyword + semantic + length)
- `embedder.py` - Sentence transformer wrapper
- `utils.py` - Rubric loader from Excel
- `templates/index.html` - Web interface
- `static/style.css` - UI styling
- `static/script.js` - Frontend logic

### Case Study Materials  
- `Case study for interns.xlsx` - Evaluation rubric (8 criteria)
- `Sample text for case study.txt` - Sample transcript
- `Nirmaan AI intern Case study instructions.pdf` - Requirements

### Documentation
- `README.md` - Complete documentation
- `SUBMISSION.md` - Detailed submission guide
- `requirements.txt` - Python dependencies

### Deployment
- `run.bat` / `run.sh` - Easy launchers
- `Dockerfile` - Container deployment
- `Procfile` - Heroku deployment

---

## HOW IT WORKS

1. **Loads rubric** from Excel (8 criteria with weights)
2. **Analyzes transcript** using three signals:
   - Keyword matching (40%)
   - AI semantic similarity (50%)
   - Length validation (10%)
3. **Produces detailed score** (0-100) with:
   - Overall score
   - Per-criterion breakdown
   - Found/missing keywords
   - Actionable feedback

---

## KEY FEATURES

- Web UI - Clean interface with JSON export  
- REST API - `/score` endpoint for automation  
- Local AI - No API costs, runs offline  
- Production Ready - Docker + Heroku deployment  
- Well Documented - README + inline comments  

---

## TECH STACK

- **Backend**: Flask (Python)
- **AI Model**: sentence-transformers (all-MiniLM-L6-v2)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Docker, Heroku

---

## SAMPLE OUTPUT

```json
{
  "overall_score": 65.8,
  "per_criterion": [
    {
      "criterion": "Key Word Presence",
      "criterion_raw": 57.6,
      "found_keywords": ["class", "school", "family"],
      "feedback": "Missing keywords: hello, introduce"
    }
  ],
  "metadata": {
    "total_words": 134
  }
}
```

---

## TROUBLESHOOTING

**Dependencies won't install?**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Port 5000 already in use?**  
Edit `app.py`, change to `port=5001`

**Model won't download?**
```bash
set HF_HOME=.cache
python app.py
```


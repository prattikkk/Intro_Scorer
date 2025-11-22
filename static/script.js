// Global variable to store the latest result
let latestResult = null;

// DOM elements
const transcriptInput = document.getElementById('transcriptInput');
const fileUpload = document.getElementById('fileUpload');
const scoreButton = document.getElementById('scoreButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const overallScore = document.getElementById('overallScore');
const overallScoreBar = document.getElementById('overallScoreBar');
const criteriaResults = document.getElementById('criteriaResults');
const metadataContent = document.getElementById('metadataContent');
const downloadButton = document.getElementById('downloadButton');

// Configuration inputs
const semanticWeight = document.getElementById('semanticWeight');
const keywordWeight = document.getElementById('keywordWeight');
const lengthWeight = document.getElementById('lengthWeight');

// File upload handler
fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        const text = await file.text();
        transcriptInput.value = text;
    }
});

// Score button handler
scoreButton.addEventListener('click', async () => {
    const transcript = transcriptInput.value.trim();
    
    if (!transcript) {
        alert('Please enter or upload a transcript first.');
        return;
    }
    
    // Prepare config
    const config = {
        semantic_weight: parseFloat(semanticWeight.value),
        keyword_weight: parseFloat(keywordWeight.value),
        length_weight: parseFloat(lengthWeight.value)
    };
    
    // Validate weights sum to 1.0
    const sum = config.semantic_weight + config.keyword_weight + config.length_weight;
    if (Math.abs(sum - 1.0) > 0.01) {
        alert(`Weights must sum to 1.0 (current sum: ${sum.toFixed(2)})`);
        return;
    }
    
    // Show loading, hide results
    scoreButton.disabled = true;
    loadingSpinner.style.display = 'block';
    resultsSection.style.display = 'none';
    
    try {
        // Call API
        const response = await fetch('/score', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                transcript: transcript,
                config: config
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Scoring failed');
        }
        
        const result = await response.json();
        latestResult = result;
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        alert(`Error: ${error.message}`);
        console.error(error);
    } finally {
        scoreButton.disabled = false;
        loadingSpinner.style.display = 'none';
    }
});

// Display results
function displayResults(result) {
    // Show results section
    resultsSection.style.display = 'block';
    
    // Overall score
    overallScore.textContent = result.overall_score;
    overallScoreBar.style.width = `${result.overall_score}%`;
    
    // Per-criterion results
    criteriaResults.innerHTML = '';
    result.per_criterion.forEach((criterion, index) => {
        const card = createCriterionCard(criterion, index);
        criteriaResults.appendChild(card);
    });
    
    // Metadata
    displayMetadata(result.metadata);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Create criterion card
function createCriterionCard(criterion, index) {
    const card = document.createElement('div');
    card.className = 'criterion-card';
    card.id = `criterion-${index}`;
    
    // Get color based on score
    const scoreColor = getScoreColor(criterion.criterion_raw);
    
    card.innerHTML = `
        <div class="criterion-header">
            <div class="criterion-name">${criterion.criterion}</div>
            <div class="criterion-score" style="color: ${scoreColor}">${criterion.criterion_raw}/100</div>
        </div>
        <div class="criterion-details">
            <div class="detail-row">
                <div class="detail-label">Weight:</div>
                <div class="detail-value">${criterion.weight}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Weighted Score:</div>
                <div class="detail-value">${criterion.criterion_weighted}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Keyword Score:</div>
                <div class="detail-value">${criterion.kw_score}/100</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Semantic Score:</div>
                <div class="detail-value">${criterion.sem_score}/100</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Length Score:</div>
                <div class="detail-value">${criterion.len_score}/100</div>
            </div>
            ${criterion.keywords_expected.length > 0 ? `
            <div class="detail-row">
                <div class="detail-label">Keywords:</div>
                <div class="detail-value">
                    <div class="keywords-list">
                        ${criterion.keywords_expected.map(kw => 
                            `<span class="keyword-tag ${criterion.keywords_found.includes(kw) ? 'found' : ''}">${kw}</span>`
                        ).join('')}
                    </div>
                </div>
            </div>
            ` : ''}
            <div class="feedback-box">
                <strong>Feedback:</strong> ${criterion.feedback}
            </div>
        </div>
    `;
    
    // Toggle details on click
    card.querySelector('.criterion-header').addEventListener('click', () => {
        card.classList.toggle('expanded');
    });
    
    return card;
}

// Display metadata
function displayMetadata(metadata) {
    metadataContent.innerHTML = `
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="metadata-label">Semantic Weight:</div>
                <div class="metadata-value">${metadata.semantic_weight}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Keyword Weight:</div>
                <div class="metadata-value">${metadata.keyword_weight}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Length Weight:</div>
                <div class="metadata-value">${metadata.length_weight}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Total Words:</div>
                <div class="metadata-value">${metadata.total_words}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Rubric File:</div>
                <div class="metadata-value">${metadata.rubric_path}</div>
            </div>
        </div>
    `;
}

// Get color based on score
function getScoreColor(score) {
    if (score >= 80) return '#059669'; // Green
    if (score >= 60) return '#d97706'; // Orange
    return '#dc2626'; // Red
}

// Download JSON button
downloadButton.addEventListener('click', () => {
    if (!latestResult) {
        alert('No results to download');
        return;
    }
    
    const blob = new Blob([JSON.stringify(latestResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript_score_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

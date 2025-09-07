/**
 * SEO Audit Tool - Enhanced Frontend JavaScript (Race Condition Fixed)
 * Handles form submission and progress tracking
 */

// Global variables
let currentAnalysisId = null;
let progressInterval = null;
let isAnalyzing = false;
let statusCheckRetries = 0;
const MAX_STATUS_RETRIES = 5;
const STATUS_CHECK_INTERVAL = 3000;

// DOM elements
const analysisForm = document.getElementById('analysis-form');
const progressContainer = document.getElementById('progress-container');
const resultsContainer = document.getElementById('results-container');
const progressBar = document.getElementById('progress');
const progressText = document.getElementById('progress-text');
const startButton = document.getElementById('start-analysis');

console.log('🔍 SEO Audit Tool Frontend Loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 SEO Audit Tool initialized (Race Condition Fixed)');

    if (analysisForm) {
        analysisForm.addEventListener('submit', handleFormSubmit);
        addInputValidation();
    }
});

async function handleFormSubmit(event) {
    event.preventDefault();

    if (isAnalyzing) return;

    console.log('📊 Starting SEO analysis...');

    const formData = new FormData(analysisForm);
    const websiteUrl = formData.get('website_url')?.trim();
    const targetKeyword = formData.get('target_keyword')?.trim();
    const maxPages = parseInt(formData.get('max_pages')) || 10;

    if (!websiteUrl || !targetKeyword) {
        showError('Please fill in all required fields');
        return;
    }

    if (!isValidUrl(websiteUrl)) {
        showError('Please enter a valid website URL');
        return;
    }

    const requestData = {
        website_url: websiteUrl,
        target_keyword: targetKeyword,
        max_pages: Math.min(Math.max(1, maxPages), 100)
    };

    try {
        await startAnalysis(requestData);
    } catch (error) {
        console.error('❌ Analysis failed:', error);
        showError('Failed to start analysis: ' + error.message);
        resetUI();
    }
}

async function startAnalysis(data) {
    isAnalyzing = true;
    statusCheckRetries = 1;

    updateUI('starting');
    showProgress('Starting analysis...', 0);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }

        if (!result.analysis_id) {
            throw new Error('No analysis ID received from server');
        }

        currentAnalysisId = result.analysis_id;
        console.log(`✅ Analysis started with ID: ${currentAnalysisId}`);

        if (result.race_condition_fixed) {
            console.log('🔧 Race condition fix detected');
        }

        updateUI('running');

        // Add delay before starting status polling
        setTimeout(() => {
            startProgressPolling();
        }, 2000);

        if (result.estimated_duration_seconds) {
            const minutes = Math.ceil(result.estimated_duration_seconds / 60);
            showProgress(`Analysis started! Estimated time: ${minutes} minute${minutes !== 1 ? 's' : ''}`, 5);
        }

    } catch (error) {
        console.error('❌ Failed to start analysis:', error);
        throw error;
    }
}

function startProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    progressInterval = setInterval(async () => {
        try {
            await checkProgress();
        } catch (error) {
            console.error('❌ Progress check failed:', error);

            // Enhanced race condition handling
            if (error.message.includes('404') || error.message.includes('Analysis not found')) {
                statusCheckRetries++;
                if (statusCheckRetries <= MAX_STATUS_RETRIES) {
                    console.warn(`⚠️ Analysis not found, retry ${statusCheckRetries}/${MAX_STATUS_RETRIES}`);
                    showProgress(`Initializing analysis... (attempt ${statusCheckRetries}/${MAX_STATUS_RETRIES})`, Math.min(10, statusCheckRetries * 2));
                    return;
                } else {
                    console.error(`❌ Analysis not found after ${MAX_STATUS_RETRIES} attempts`);
                    stopProgressPolling();
                    showError('Analysis initialization failed. Please try starting a new analysis.');
                    resetUI();
                }
            } else {
                stopProgressPolling();
                showError('Connection error: ' + error.message);
                resetUI();
            }
        }
    }, STATUS_CHECK_INTERVAL);
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

async function checkProgress() {
    if (!currentAnalysisId) return;

    const response = await fetch(`/api/status/${currentAnalysisId}`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}`);
    }

    statusCheckRetries = 0;

    switch (result.status) {
        case 'queued':
            showProgress('Analysis queued...', 5);
            break;

        case 'running':
            const pct = result.progress_info?.percentage || 10;
            const step = result.progress_info?.current_step || 1;
            const total = result.progress_info?.total_steps || 5;
            const desc = result.progress || 'Processing...';
            showProgress(`Step ${step}/${total}: ${desc}`, Math.min(95, Math.max(10, pct)));
            break;

        case 'completed':
            showProgress('Analysis completed! 🎉', 100);
            stopProgressPolling();
            await loadResults();
            break;

        case 'error':
            console.error(`Analysis ${currentAnalysisId} failed:`, result.error);
            stopProgressPolling();
            showError(`Analysis failed: ${result.error || 'Unknown error'}`);
            resetUI();
            break;

        default:
            console.warn('📊 Unknown status:', result.status);
            break;
    }
}

async function loadResults() {
    if (!currentAnalysisId) return;

    try {
        const response = await fetch(`/api/report/${currentAnalysisId}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }

        displayResults(result);

    } catch (error) {
        console.error('❌ Failed to load results:', error);
        showError('Failed to load results: ' + error.message);
    }
}

function displayResults(data) {
    const report = data.report || '';
    const meta = data.metadata || {};
    const html = markdownToHtml(report);

    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <div class="card analysis-results">
                <div class="card-header bg-success text-white">
                    <h4 class="card-title mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        Analysis Complete
                    </h4>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <strong>Website:</strong> ${meta.website_url || 'N/A'}
                        </div>
                        <div class="col-md-6">
                            <strong>Keyword:</strong> ${meta.target_keyword || 'N/A'}
                        </div>
                    </div>
                    <div class="analysis-content">
                        ${html}
                    </div>
                </div>
            </div>
        `;

        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }
}

function showProgress(text, percentage) {
    if (progressText) progressText.textContent = text;
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.textContent = Math.round(percentage) + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
}

function updateUI(state) {
    const formElements = analysisForm?.querySelectorAll('input, select, button');

    switch (state) {
        case 'starting':
        case 'running':
            if (formElements) {
                formElements.forEach(el => el.disabled = true);
            }
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
            if (resultsContainer) {
                resultsContainer.style.display = 'none';
            }
            break;

        case 'completed':
        case 'error':
            if (formElements) {
                formElements.forEach(el => el.disabled = false);
            }
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
            isAnalyzing = false;
            break;
    }
}

function resetUI() {
    updateUI('completed');
    currentAnalysisId = null;
    stopProgressPolling();
}

function showError(message) {
    alert('Error: ' + message);
}

function addInputValidation() {
    const form = analysisForm;
    if (!form) return;

    form.classList.add('needs-validation');

    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });
}

function isValidUrl(string) {
    try {
        new URL(string.startsWith('http') ? string : 'https://' + string);
        return true;
    } catch (_) {
        return false;
    }
}

function markdownToHtml(markdown) {
    return markdown
        // Headers
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Lists
        .replace(/^\* (.+)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
        // Links
        .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
        // Line breaks
        .replace(/\n/g, '<br>');
}

console.log('🚀 SEO Audit Tool JavaScript loaded successfully');

/**
 * Enhanced SEO Audit Tool V3.0 - JavaScript
 * Advanced frontend functionality with enhanced features
 */

// Global variables
let currentAnalysisId = null;
let progressInterval = null;
let statusCheckRetries = 0;
const MAX_STATUS_RETRIES = 10;

// Enhanced configuration
const CONFIG = {
    statusCheckInterval: 3000,
    maxRetries: 10,
    timeoutDuration: 300000, // 5 minutes
    endpoints: {
        analyze: '/api/analyze',
        status: '/api/status',
        report: '/api/report',
        downloadCsv: '/api/download-csv',
        health: '/api/health',
        cacheStats: '/api/admin/cache-stats',
        clearCache: '/api/admin/clear-cache'
    }
};

// Enhanced Form Handling
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Enhanced SEO Audit Tool V3.0 loaded successfully!');

    // Initialize components
    initializeEnhancedForm();
    initializeAnalysisTypeSelection();
    initializeAdvancedOptions();

    // Check system health
    checkSystemHealth();
});

function initializeEnhancedForm() {
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.addEventListener('submit', handleEnhancedFormSubmit);

        // Enhanced form validation
        const inputs = analysisForm.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', validateField);
            input.addEventListener('input', clearFieldError);
        });
    }
}

function initializeAnalysisTypeSelection() {
    const analysisTypeCards = document.querySelectorAll('.analysis-type-card');
    const maxPagesSection = document.getElementById('max-pages-section');
    const wholeWebsiteWarning = document.getElementById('whole-website-warning');

    analysisTypeCards.forEach(card => {
        card.addEventListener('click', function() {
            const type = this.dataset.type;
            const radio = this.querySelector('input[type="radio"]');

            if (radio) {
                radio.checked = true;
                updateAnalysisTypeUI(type);
            }
        });
    });

    function updateAnalysisTypeUI(type) {
        // Update card styling
        analysisTypeCards.forEach(c => {
            c.classList.remove('border-primary', 'bg-light');
        });

        const selectedCard = document.querySelector(`[data-type="${type}"]`);
        if (selectedCard) {
            selectedCard.classList.add('border-primary', 'bg-light');
        }

        // Show/hide sections based on selection
        if (type === 'whole') {
            if (maxPagesSection) maxPagesSection.style.display = 'none';
            if (wholeWebsiteWarning) wholeWebsiteWarning.style.display = 'block';
        } else {
            if (maxPagesSection) maxPagesSection.style.display = 'block';
            if (wholeWebsiteWarning) wholeWebsiteWarning.style.display = 'none';
        }
    }
}

function initializeAdvancedOptions() {
    const advancedToggle = document.querySelector('[data-bs-target="#advanced-options"]');
    if (advancedToggle) {
        advancedToggle.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon) {
                setTimeout(() => {
                    const isExpanded = document.getElementById('advanced-options').classList.contains('show');
                    icon.className = isExpanded ? 'fas fa-cog-up me-1' : 'fas fa-cog me-1';
                }, 200);
            }
        });
    }
}

async function handleEnhancedFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);

    // Enhanced validation
    if (!form.checkValidity()) {
        event.stopPropagation();
        form.classList.add('was-validated');
        return;
    }

    const websiteUrl = formData.get('website_url').trim();
    const targetKeyword = formData.get('target_keyword').trim();
    const analysisType = formData.get('analysis_type');
    const maxPages = analysisType === 'whole' ? null : parseInt(formData.get('max_pages'));
    const wholeWebsite = analysisType === 'whole';

    // Enhanced validation
    if (!validateUrl(websiteUrl)) {
        showFieldError('website_url', 'Please enter a valid website URL');
        return;
    }

    if (!validateKeyword(targetKeyword)) {
        showFieldError('target_keyword', 'Please enter a valid target keyword');
        return;
    }

    const requestData = {
        website_url: websiteUrl,
        target_keyword: targetKeyword,
        max_pages: maxPages || 10,
        whole_website: wholeWebsite,
        serp_analysis: formData.get('serp_analysis') === 'on',
        use_cache: formData.get('use_cache') === 'on'
    };

    try {
        await startEnhancedAnalysis(requestData);
    } catch (error) {
        console.error('Enhanced analysis failed:', error);
        showError('Failed to start enhanced analysis: ' + error.message);
    }
}

async function startEnhancedAnalysis(data) {
    console.log('🚀 Starting enhanced analysis...', data);

    // Update UI for enhanced analysis
    updateUI('starting');
    showProgress('Initializing enhanced SEO analysis...', 0);

    try {
        const response = await fetch(CONFIG.endpoints.analyze, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            // Handle different error types
            if (response.status === 502) {
                throw new Error('Server is temporarily unavailable. Please try again in a few minutes.');
            }
            
            let errorMessage;
            try {
                const result = await response.json();
                errorMessage = result.error || `HTTP ${response.status}: ${response.statusText}`;
            } catch (e) {
                errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();
        currentAnalysisId = result.analysis_id;
        console.log(`✅ Enhanced analysis started: ${currentAnalysisId}`);

        updateUI('running');

        // Enhanced progress polling
        setTimeout(() => {
            startEnhancedProgressPolling();
        }, 2000);

        // Update progress based on analysis type
        if (data.whole_website) {
            showProgress('Starting comprehensive website discovery...', 5);
            updateProgressDetails('Discovering all pages on your website...');
        } else {
            showProgress(`Analyzing ${data.max_pages} pages with enhanced features...`, 5);
            updateProgressDetails('Enhanced crawling with caching enabled...');
        }

    } catch (error) {
        console.error('❌ Enhanced analysis failed:', error);
        updateUI('idle');
        throw error;
    }
}

function startEnhancedProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }

    progressInterval = setInterval(async () => {
        try {
            await checkEnhancedProgress();
        } catch (error) {
            console.error('❌ Progress check failed:', error);
            handleProgressError(error);
        }
    }, CONFIG.statusCheckInterval);
}

async function checkEnhancedProgress() {
    if (!currentAnalysisId) return;

    const response = await fetch(`${CONFIG.endpoints.status}/${currentAnalysisId}`);
    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    // Enhanced progress display
    const pct = result.progress_info?.percentage || 0;
    const desc = result.progress || 'Processing...';

    showProgress(desc, pct);

    // Update enhanced statistics
    if (result.metadata || result.enhanced_summary) {
        updateEnhancedStats(result.metadata || {}, result.enhanced_summary || {});
    }

    // Update progress details
    if (result.progress_info) {
        const details = `Step ${result.progress_info.current_step}/${result.progress_info.total_steps} • ${result.progress_info.elapsed_time} elapsed`;
        updateProgressDetails(details);
    }

    switch (result.status) {
        case 'completed':
            showProgress('Enhanced analysis completed! 🎉', 100);
            stopProgressPolling();
            setTimeout(() => loadEnhancedResults(), 1000);
            break;
        case 'error':
            stopProgressPolling();
            showError(`Enhanced analysis failed: ${result.error || 'Unknown error'}`);
            updateUI('idle');
            break;
        case 'running':
            statusCheckRetries = 0; // Reset retry counter on successful status
            break;
    }
}

function updateEnhancedStats(metadata, enhancedSummary) {
    const elements = {
        'pages-analyzed': metadata.pages_analyzed || enhancedSummary.pages_analyzed || 0,
        'issues-found': metadata.issues_found || enhancedSummary.issues_found || 0,
        'cache-hits': metadata.cached_pages || enhancedSummary.pages_from_cache || 0
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            animateValue(element, parseInt(element.textContent) || 0, value, 500);
        }
    });

    // Update elapsed time
    if (metadata.elapsed_seconds || metadata.elapsed_formatted) {
        const timeElement = document.getElementById('elapsed-time');
        if (timeElement) {
            timeElement.textContent = metadata.elapsed_formatted || formatDuration(metadata.elapsed_seconds || 0);
        }
    }
}

async function loadEnhancedResults() {
    console.log('📊 Loading enhanced results...');
    
    if (!currentAnalysisId) {
        console.error('No analysis ID available');
        return;
    }

    try {
        // Show results section
        updateUI('completed');
        
        // Fetch the report
        const response = await fetch(`${CONFIG.endpoints.report}/${currentAnalysisId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load results: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display the report
        displayEnhancedReport(data);
        
        // Scroll to results
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
    } catch (error) {
        console.error('❌ Error loading results:', error);
        showError('Failed to load results: ' + error.message);
    }
}

function displayEnhancedReport(data) {
    console.log('📋 Displaying enhanced report...', data);
    
    // Update report content
    const reportContent = document.getElementById('report-content');
    if (reportContent && data.report) {
        // Convert markdown to HTML (simple conversion)
        const htmlReport = convertMarkdownToHTML(data.report);
        reportContent.innerHTML = htmlReport;
    }
    
    // Update metadata
    const metadata = data.metadata || {};
    const enhanced = data.enhanced_features || {};
    
    // Update SEO score
    const seoScore = metadata.seo_score || 0;
    updateSEOScoreDisplay(seoScore);
    
    // Update statistics
    updateFinalStats(metadata, enhanced);
    
    // Show download button if CSV is available
    const downloadBtn = document.getElementById('download-csv-btn');
    if (downloadBtn && data.enhanced_features?.has_csv_export) {
        downloadBtn.style.display = 'inline-block';
        downloadBtn.onclick = () => downloadCSV(currentAnalysisId);
    }
    
    // Update analysis info
    updateAnalysisInfo(data);
}

function convertMarkdownToHTML(markdown) {
    return markdown
        // Headers
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        // Bold and italic
        .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*)\*/gim, '<em>$1</em>')
        // Lists
        .replace(/^\- (.*$)/gim, '<li>$1</li>')
        // Line breaks
        .replace(/\n$/gim, '<br>')
        // Tables (basic)
        .replace(/\|/g, '</td><td>')
        .replace(/^(.*\|.*)/gim, '<tr><td>$1</td></tr>')
        // Wrap table rows
        .replace(/(<tr>.*<\/tr>)/gim, '<table class="table table-striped">$1</table>');
}

function updateSEOScoreDisplay(score) {
    const scoreElement = document.getElementById('seo-score');
    const scoreBar = document.getElementById('seo-score-bar');
    const scoreText = document.getElementById('seo-score-text');
    
    if (scoreElement) {
        animateValue(scoreElement, 0, score, 1000);
    }
    
    if (scoreBar) {
        scoreBar.style.width = score + '%';
        scoreBar.className = `progress-bar ${getScoreColor(score)}`;
    }
    
    if (scoreText) {
        scoreText.textContent = getScoreDescription(score);
        scoreText.className = `badge ${getScoreColor(score).replace('bg-', 'bg-')}`;
    }
}

function getScoreColor(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-warning';
    return 'bg-danger';
}

function getScoreDescription(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Needs Work';
    return 'Poor';
}

function updateFinalStats(metadata, enhanced) {
    const stats = {
        'final-pages': metadata.pages_analyzed || 0,
        'final-issues': metadata.issues_found || 0,
        'final-duration': formatDuration(metadata.crawl_duration || 0),
        'final-cache': metadata.cached_pages || 0
    };
    
    Object.entries(stats).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            if (typeof value === 'number') {
                animateValue(element, 0, value, 800);
            } else {
                element.textContent = value;
            }
        }
    });
}

function updateAnalysisInfo(data) {
    const infoElement = document.getElementById('analysis-info');
    if (infoElement && data.metadata) {
        const info = [
            `Analysis Type: ${data.metadata.whole_website_analysis ? 'Whole Website' : 'Selective Pages'}`,
            `SERP Analysis: ${data.metadata.serp_results_count > 0 ? 'Enabled' : 'Disabled'}`,
            `Caching: ${data.metadata.cached_pages > 0 ? 'Used' : 'Not Used'}`,
            `Generated: ${new Date().toLocaleString()}`
        ];
        infoElement.innerHTML = info.map(i => `<small class="text-muted d-block">${i}</small>`).join('');
    }
}

// Utility functions
function updateUI(state) {
    const elements = {
        form: document.getElementById('analysis-form'),
        progress: document.getElementById('progress-section'),
        results: document.getElementById('results-section'),
        startBtn: document.getElementById('start-analysis')
    };

    switch (state) {
        case 'idle':
            if (elements.form) elements.form.style.display = 'block';
            if (elements.progress) elements.progress.style.display = 'none';
            if (elements.results) elements.results.style.display = 'none';
            if (elements.startBtn) {
                elements.startBtn.disabled = false;
                elements.startBtn.innerHTML = '<i class="fas fa-search me-2"></i>Start Enhanced Analysis';
            }
            break;
        case 'starting':
        case 'running':
            if (elements.form) elements.form.style.display = 'none';
            if (elements.progress) elements.progress.style.display = 'block';
            if (elements.results) elements.results.style.display = 'none';
            if (elements.startBtn) {
                elements.startBtn.disabled = true;
                elements.startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
            }
            break;
        case 'completed':
            if (elements.form) elements.form.style.display = 'none';
            if (elements.progress) elements.progress.style.display = 'none';
            if (elements.results) elements.results.style.display = 'block';
            break;
    }
}

function showProgress(message, percentage) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    if (progressBar) {
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = message;
    }
}

function updateProgressDetails(details) {
    const detailsElement = document.getElementById('progress-details');
    if (detailsElement) {
        detailsElement.textContent = details;
    }
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function handleProgressError(error) {
    statusCheckRetries++;
    if (statusCheckRetries >= MAX_STATUS_RETRIES) {
        stopProgressPolling();
        showError('Analysis status check failed after multiple retries. Please refresh the page and try again.');
        updateUI('idle');
    }
}

function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
}

function showFieldError(fieldName, message) {
    const field = document.getElementById(fieldName);
    if (field) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
    }
}

function clearFieldError(event) {
    const field = event.target;
    field.classList.remove('is-invalid');
    
    const feedback = field.parentElement.querySelector('.invalid-feedback');
    if (feedback) {
        feedback.remove();
    }
}

function validateField(event) {
    const field = event.target;
    const value = field.value.trim();
    
    if (field.id === 'website_url' && !validateUrl(value)) {
        showFieldError(field.id, 'Please enter a valid website URL');
    } else if (field.id === 'target_keyword' && !validateKeyword(value)) {
        showFieldError(field.id, 'Please enter a valid target keyword');
    }
}

function validateUrl(url) {
    try {
        new URL(url.startsWith('http') ? url : 'https://' + url);
        return true;
    } catch {
        return false;
    }
}

function validateKeyword(keyword) {
    return keyword.length >= 2 && keyword.length <= 100;
}

function animateValue(element, start, end, duration) {
    const startTimestamp = performance.now();
    const step = (timestamp) => {
        const elapsed = timestamp - startTimestamp;
        const progress = Math.min(elapsed / duration, 1);
        const current = start + (end - start) * progress;
        
        element.textContent = Math.floor(current);
        
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    };
    requestAnimationFrame(step);
}

function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}m ${remainingSeconds}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

function startNewAnalysis() {
    currentAnalysisId = null;
    statusCheckRetries = 0;
    stopProgressPolling();
    updateUI('idle');
    
    // Clear form
    const form = document.getElementById('analysis-form');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
    }
    
    // Clear any error messages
    document.querySelectorAll('.alert').forEach(alert => alert.remove());
    document.querySelectorAll('.is-invalid').forEach(field => {
        field.classList.remove('is-invalid');
    });
    document.querySelectorAll('.invalid-feedback').forEach(feedback => feedback.remove());
}

async function downloadCSV(analysisId) {
    try {
        const response = await fetch(`${CONFIG.endpoints.downloadCsv}/${analysisId}`);
        
        if (!response.ok) {
            throw new Error('Failed to download CSV');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `seo-analysis-${analysisId}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
    } catch (error) {
        console.error('❌ CSV download failed:', error);
        showError('Failed to download CSV: ' + error.message);
    }
}

// Admin functions
async function clearCache() {
    if (!confirm('Are you sure you want to clear the analysis cache? This will remove all cached page data.')) {
        return;
    }

    try {
        const response = await fetch(CONFIG.endpoints.clearCache, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Cache cleared successfully! ${result.pages_cleared} pages removed.`);
        } else {
            throw new Error(result.error || 'Failed to clear cache');
        }
    } catch (error) {
        alert('Error clearing cache: ' + error.message);
    }
}

async function checkSystemHealth() {
    try {
        const response = await fetch(CONFIG.endpoints.health);
        const health = await response.json();

        console.log('🏥 System health check:', health);

        // Update status indicator if present
        const statusIndicator = document.querySelector('.status-indicator .badge');
        if (statusIndicator) {
            if (health.status === 'healthy') {
                statusIndicator.className = 'badge bg-success';
                statusIndicator.innerHTML = '<i class="fas fa-check-circle me-1"></i>Online';
            } else {
                statusIndicator.className = 'badge bg-danger';
                statusIndicator.innerHTML = '<i class="fas fa-exclamation-circle me-1"></i>Issues';
            }
        }
    } catch (error) {
        console.warn('❌ Health check failed:', error);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to start analysis
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const form = document.getElementById('analysis-form');
        if (form && !document.getElementById('start-analysis').disabled) {
            form.dispatchEvent(new Event('submit'));
        }
    }

    // Escape to cancel/reset
    if (event.key === 'Escape' && currentAnalysisId) {
        if (confirm('Cancel the current analysis?')) {
            startNewAnalysis();
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopProgressPolling();
});

console.log('🎯 Enhanced SEO Audit Tool V3.0 JavaScript loaded successfully!');

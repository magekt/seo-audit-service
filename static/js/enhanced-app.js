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

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
        }

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
            timeElement.textContent = metadata.elapsed_formatted || formatDuration(metadata.elapsed_seconds);
        }
    }
}

async function loadEnhancedResults() {
    if (!currentAnalysisId) return;

    try {
        const response = await fetch(`${CONFIG.endpoints.report}/${currentAnalysisId}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        displayEnhancedResults(result);

    } catch (error) {
        console.error('❌ Failed to load enhanced results:', error);
        showError('Failed to load enhanced results: ' + error.message);
    }
}

function displayEnhancedResults(data) {
    const report = data.report || '';
    const metadata = data.metadata || {};
    const enhancedFeatures = data.enhanced_features || {};

    // Enhanced HTML conversion with better styling
    const html = markdownToHtml(report);

    const resultsContainer = document.getElementById('results-container');
    const resultsContent = document.getElementById('results-content');

    if (resultsContent) {
        resultsContent.innerHTML = `
            <div class="enhanced-results fade-in">
                <!-- Enhanced metadata display -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="stat-card text-center p-3 bg-primary text-white rounded">
                            <div class="stat-value">${metadata.seo_score || 0}/100</div>
                            <div class="stat-label">SEO Score</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center p-3 bg-info text-white rounded">
                            <div class="stat-value">${metadata.pages_analyzed || 0}</div>
                            <div class="stat-label">Pages Analyzed</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center p-3 bg-warning text-white rounded">
                            <div class="stat-value">${metadata.issues_found || 0}</div>
                            <div class="stat-label">Issues Found</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card text-center p-3 bg-success text-white rounded">
                            <div class="stat-value">${metadata.cached_pages || 0}</div>
                            <div class="stat-label">Cache Hits</div>
                        </div>
                    </div>
                </div>

                <!-- Enhanced features summary -->
                ${enhancedFeatures.whole_website_analysis ? `
                    <div class="alert alert-info mb-4">
                        <h6 class="alert-heading"><i class="fas fa-globe me-2"></i>Whole Website Analysis</h6>
                        <p class="mb-0">Comprehensive analysis completed with ${enhancedFeatures.pages_from_cache || 0} pages loaded from cache.</p>
                    </div>
                ` : ''}

                <!-- Enhanced report content -->
                <div class="report-content">
                    ${html}
                </div>
            </div>
        `;
    }

    if (resultsContainer) {
        resultsContainer.style.display = 'block';
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    updateUI('completed');
}

// Enhanced utility functions
function showProgress(message, percentage) {
    const progressBar = document.getElementById('progress');
    const progressText = document.getElementById('progress-text');

    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
        progressBar.setAttribute('aria-valuenow', percentage);

        const progressSpan = progressBar.querySelector('.progress-text');
        if (progressSpan) {
            progressSpan.textContent = `${percentage.toFixed(1)}%`;
        }
    }

    if (progressText) {
        progressText.textContent = message;
    }
}

function updateProgressDetails(details) {
    const progressDetails = document.getElementById('progress-details');
    if (progressDetails) {
        progressDetails.innerHTML = `<i class="fas fa-info-circle me-1"></i>${details}`;
    }
}

function updateUI(state) {
    const button = document.getElementById('start-analysis');
    const spinner = button?.querySelector('.spinner-border');
    const buttonText = button?.querySelector('.btn-text');
    const progressContainer = document.getElementById('progress-container');
    const resultsContainer = document.getElementById('results-container');

    switch (state) {
        case 'starting':
            if (button) {
                button.disabled = true;
                if (spinner) spinner.style.display = 'inline-block';
                if (buttonText) buttonText.textContent = 'Starting Analysis...';
            }
            if (progressContainer) progressContainer.style.display = 'block';
            if (resultsContainer) resultsContainer.style.display = 'none';
            break;

        case 'running':
            if (button) {
                button.disabled = true;
                if (buttonText) buttonText.textContent = 'Analysis Running...';
            }
            break;

        case 'completed':
            if (button) {
                button.disabled = false;
                if (spinner) spinner.style.display = 'none';
                if (buttonText) buttonText.textContent = 'Start Enhanced SEO Analysis';
            }
            if (progressContainer) progressContainer.style.display = 'none';
            break;

        case 'idle':
        default:
            if (button) {
                button.disabled = false;
                if (spinner) spinner.style.display = 'none';
                if (buttonText) buttonText.textContent = 'Start Enhanced SEO Analysis';
            }
            if (progressContainer) progressContainer.style.display = 'none';
            break;
    }
}

function stopProgressPolling() {
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
}

function downloadCSV() {
    if (currentAnalysisId) {
        const downloadUrl = `${CONFIG.endpoints.downloadCsv}/${currentAnalysisId}`;
        window.open(downloadUrl, '_blank');
    } else {
        showError('No analysis data available for download');
    }
}

function downloadReport() {
    if (currentAnalysisId) {
        const reportContent = document.querySelector('.report-content');
        if (reportContent) {
            downloadAsFile(reportContent.innerText, `seo-audit-report-${currentAnalysisId}.txt`, 'text/plain');
        }
    }
}

function startNewAnalysis() {
    // Reset form and UI
    currentAnalysisId = null;
    stopProgressPolling();
    updateUI('idle');

    const form = document.getElementById('analysis-form');
    if (form) {
        form.reset();
        form.classList.remove('was-validated');
    }

    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }

    // Scroll to form
    const formCard = document.querySelector('.card');
    if (formCard) {
        formCard.scrollIntoView({ behavior: 'smooth' });
    }
}

// Enhanced validation functions
function validateUrl(url) {
    const urlPattern = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;
    return urlPattern.test(url);
}

function validateKeyword(keyword) {
    return keyword && keyword.trim().length >= 2 && keyword.trim().length <= 100;
}

function validateField(event) {
    const field = event.target;
    const value = field.value.trim();

    if (field.hasAttribute('required') && !value) {
        showFieldError(field.id, 'This field is required');
        return false;
    }

    if (field.type === 'url' && value && !validateUrl(value)) {
        showFieldError(field.id, 'Please enter a valid URL');
        return false;
    }

    if (field.name === 'target_keyword' && value && !validateKeyword(value)) {
        showFieldError(field.id, 'Please enter a valid keyword (2-100 characters)');
        return false;
    }

    clearFieldError(field.id);
    return true;
}

function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.classList.add('is-invalid');

        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }
    }
}

function clearFieldError(event) {
    const field = event.target || event;
    if (field.classList) {
        field.classList.remove('is-invalid');
    }
}

// Enhanced utility functions
function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

function downloadAsFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

function markdownToHtml(markdown) {
    // Enhanced markdown to HTML conversion
    let html = markdown
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
        .replace(/^##### (.*$)/gim, '<h5>$1</h5>')
        .replace(/^###### (.*$)/gim, '<h6>$1</h6>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/gim, '<em>$1</em>')
        .replace(/\`(.*?)\`/gim, '<code>$1</code>')
        .replace(/^\* (.*$)/gim, '<li>$1</li>')
        .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
        .replace(/^\| (.*) \|$/gim, '<tr><td>$1</td></tr>')
        .replace(/\n/g, '<br>');

    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

    // Simple table conversion
    html = html.replace(/\|(.+?)\|/g, (match, content) => {
        const cells = content.split('|').map(cell => `<td>${cell.trim()}</td>`).join('');
        return `<tr>${cells}</tr>`;
    });

    // Wrap tables
    html = html.replace(/(<tr>.*<\/tr>)/gs, '<table class="table table-striped">$1</table>');

    return html;
}

function showError(message) {
    // Create enhanced error alert
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Insert at top of form card
    const formCard = document.querySelector('.card-body');
    if (formCard) {
        formCard.insertAdjacentHTML('afterbegin', alertHtml);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            const alert = formCard.querySelector('.alert-danger');
            if (alert) {
                alert.remove();
            }
        }, 10000);
    }
}

// Enhanced error handling
function handleProgressError(error) {
    if (error.message.includes('404') || error.message.includes('Analysis not found')) {
        statusCheckRetries++;
        if (statusCheckRetries <= MAX_STATUS_RETRIES) {
            showProgress(`Initializing enhanced analysis... (attempt ${statusCheckRetries}/${MAX_STATUS_RETRIES})`, Math.min(10, statusCheckRetries * 2));
            return;
        }
    }

    stopProgressPolling();
    showError('Enhanced analysis error: ' + error.message);
    updateUI('idle');
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

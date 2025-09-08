/**
 * Enhanced SEO Audit Tool V3.0 - FINAL FIXED JavaScript Implementation
 * Production-ready frontend with correct results handling
 */

console.log("🎯 Enhanced SEO Audit Tool V3.0 JavaScript loaded successfully!");

// Configuration and State Management
const CONFIG = {
    API_BASE: window.location.origin,
    STATUS_POLL_INTERVAL: 2000,
    MAX_RETRIES: 5,
    RETRY_DELAY: 2000
};

const ANALYSIS_STATE = {
    currentAnalysisId: null,
    isRunning: false,
    statusPolling: null,
    retryCount: 0
};

// DOM Elements
let DOM = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Enhanced SEO Audit Tool V3.0 loaded successfully!");
    initializeDOMElements();
    setupEventListeners();
    performHealthCheck();
    updateUI();
});

function initializeDOMElements() {
    DOM = {
        // Form elements
        seoForm: document.getElementById('enhanced-seo-form'),
        websiteUrlInput: document.getElementById('website-url'),
        targetKeywordInput: document.getElementById('target-keyword'),
        maxPagesInput: document.getElementById('max-pages'),
        wholeWebsiteToggle: document.getElementById('whole-website'),
        serpAnalysisToggle: document.getElementById('serp-analysis'),

        // UI sections
        formSection: document.getElementById('form-section'),
        progressSection: document.getElementById('progress-section'),
        resultsSection: document.getElementById('results-section'),

        // Progress elements
        progressBar: document.getElementById('progress-bar'),
        progressFill: document.getElementById('progress-fill'),
        progressText: document.getElementById('progress-text'),
        progressDetails: document.getElementById('progress-details'),

        // Results elements
        reportContent: document.getElementById('report-content'),
        csvDownloadBtn: document.getElementById('csv-download-btn'),

        // Control buttons
        startBtn: document.getElementById('start-analysis-btn'),
        cancelBtn: document.getElementById('cancel-analysis-btn'),
        newAnalysisBtn: document.getElementById('new-analysis-btn'),

        // Status elements
        analysisStatus: document.getElementById('analysis-status'),
        errorMessage: document.getElementById('error-message'),
        systemStatus: document.getElementById('system-status')
    };

    console.log("DOM Elements initialized:", DOM);
}

function setupEventListeners() {
    // Form submission
    if (DOM.seoForm) {
        DOM.seoForm.addEventListener('submit', handleEnhancedFormSubmit);
        console.log("✅ Form submit listener added");
    }

    // Control buttons
    if (DOM.startBtn) {
        DOM.startBtn.addEventListener('click', handleStartAnalysis);
    }

    if (DOM.cancelBtn) {
        DOM.cancelBtn.addEventListener('click', handleCancelAnalysis);
    }

    if (DOM.newAnalysisBtn) {
        DOM.newAnalysisBtn.addEventListener('click', handleNewAnalysis);
    }

    if (DOM.csvDownloadBtn) {
        DOM.csvDownloadBtn.addEventListener('click', handleCSVDownload);
    }

    // Toggle functionality
    if (DOM.wholeWebsiteToggle) {
        DOM.wholeWebsiteToggle.addEventListener('change', handleWholeWebsiteToggle);
        console.log("✅ Whole website toggle listener added");
        setTimeout(handleWholeWebsiteToggle, 100);
    }
}

async function handleEnhancedFormSubmit(event) {
    event.preventDefault();
    console.log("🚀 Starting enhanced analysis...");

    try {
        showError('');
        const formData = getFormData();
        console.log("📋 Form data collected:", formData);

        const validationResult = validateFormData(formData);
        if (!validationResult.isValid) {
            showError(validationResult.message);
            return;
        }

        await startEnhancedAnalysis(formData);
    } catch (error) {
        console.error('Enhanced analysis failed:', error);
        showError(`Analysis failed: ${error.message}`);
        resetToFormState();
    }
}

function handleWholeWebsiteToggle() {
    console.log("🔄 Toggle changed");

    if (!DOM.wholeWebsiteToggle || !DOM.maxPagesInput) return;

    const isWholeWebsite = DOM.wholeWebsiteToggle.checked;
    const maxPagesGroup = DOM.maxPagesInput.closest('.form-group');

    console.log("🎯 Whole website mode:", isWholeWebsite);

    if (maxPagesGroup) {
        if (isWholeWebsite) {
            maxPagesGroup.style.opacity = '0.5';
            DOM.maxPagesInput.disabled = true;
        } else {
            maxPagesGroup.style.opacity = '1';
            DOM.maxPagesInput.disabled = false;
        }
    }

    if (DOM.startBtn) {
        DOM.startBtn.innerHTML = isWholeWebsite ? 
            '🌐 Start Whole Website Analysis' : 
            '🚀 Start Enhanced SEO Analysis';
    }
}

function getFormData() {
    const formData = {
        website_url: DOM.websiteUrlInput?.value?.trim() || '',
        target_keyword: DOM.targetKeywordInput?.value?.trim() || '',
        max_pages: parseInt(DOM.maxPagesInput?.value) || 10,
        whole_website: DOM.wholeWebsiteToggle?.checked || false,
        serp_analysis: DOM.serpAnalysisToggle?.checked !== false,
        use_cache: true
    };

    console.log("📝 Form data:", formData);
    return formData;
}

function validateFormData(data) {
    if (!data.website_url) {
        return { isValid: false, message: 'Please enter a website URL' };
    }

    if (!data.target_keyword) {
        return { isValid: false, message: 'Please enter a target keyword' };
    }

    try {
        new URL(data.website_url);
    } catch (e) {
        return { isValid: false, message: 'Please enter a valid URL (include https://)' };
    }

    return { isValid: true };
}

async function startEnhancedAnalysis(formData) {
    try {
        showProgressState();
        updateProgress(0, 'Starting analysis...', 'Initializing enhanced SEO analysis');

        ANALYSIS_STATE.isRunning = true;
        ANALYSIS_STATE.retryCount = 0;

        const response = await fetch(`${CONFIG.API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        console.log("🎉 Analysis started:", result);

        ANALYSIS_STATE.currentAnalysisId = result.analysis_id;

        updateProgress(10, 'Analysis started successfully!', 'Beginning website crawling and analysis...');

        // Start polling for status
        startStatusPolling();

    } catch (error) {
        console.error('Failed to start analysis:', error);
        showError(`Failed to start analysis: ${error.message}`);
        resetToFormState();
    }
}

function startStatusPolling() {
    if (ANALYSIS_STATE.statusPolling) {
        clearInterval(ANALYSIS_STATE.statusPolling);
    }

    ANALYSIS_STATE.statusPolling = setInterval(async () => {
        try {
            await checkAnalysisStatus();
        } catch (error) {
            console.error('Status polling error:', error);
            ANALYSIS_STATE.retryCount++;

            if (ANALYSIS_STATE.retryCount >= CONFIG.MAX_RETRIES) {
                clearInterval(ANALYSIS_STATE.statusPolling);
                ANALYSIS_STATE.statusPolling = null;
                showError('Lost connection to analysis. Please refresh and check results manually.');
                resetToFormState();
            }
        }
    }, CONFIG.STATUS_POLL_INTERVAL);

    setTimeout(checkAnalysisStatus, 1000);
}

async function checkAnalysisStatus() {
    if (!ANALYSIS_STATE.currentAnalysisId || !ANALYSIS_STATE.isRunning) {
        return;
    }

    const response = await fetch(`${CONFIG.API_BASE}/api/status/${ANALYSIS_STATE.currentAnalysisId}`);

    if (!response.ok) {
        throw new Error(`Status check failed: ${response.status}`);
    }

    const status = await response.json();
    console.log("📊 Analysis status:", status);

    ANALYSIS_STATE.retryCount = 0;

    // Update progress
    const progress = status.progress || 50;
    const message = status.message || status.status || 'Processing...';
    const details = status.elapsed_formatted ? 
        `Elapsed: ${status.elapsed_formatted} | Pages: ${status.pages_analyzed || 0}` : 
        'Running analysis...';

    updateProgress(progress, message, details);

    // Handle completion
    if (status.status === 'completed') {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
        ANALYSIS_STATE.isRunning = false;

        updateProgress(100, '✅ Analysis Complete!', 'Loading comprehensive results...');

        setTimeout(() => {
            loadEnhancedResults();
        }, 1000);

    } else if (status.status === 'failed' || status.status === 'error') {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
        ANALYSIS_STATE.isRunning = false;

        showError(`❌ Analysis failed: ${status.error_message || status.error || 'Unknown error'}`);
        resetToFormState();
    }
}

async function loadEnhancedResults() {
    try {
        showMessage('Loading comprehensive results...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/report/${ANALYSIS_STATE.currentAnalysisId}`);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to load results');
        }

        const result = await response.json();
        console.log("📊 Enhanced results loaded:", result);

        displayResults(result);

    } catch (error) {
        console.error('Error loading results:', error);
        showError(`Failed to load results: ${error.message}`);
        resetToFormState();
    }
}

// FIXED: Completely rewritten results display function
function displayResults(result) {
    showResultsState();

    if (!DOM.reportContent) {
        console.error("❌ Report content element not found");
        return;
    }

    try {
        // Handle different result structures
        let pages = [];
        let summary = {};

        // Extract pages data from various possible structures
        if (result.results && result.results.pages) {
            pages = result.results.pages;
            summary = result.results.metadata || {};
        } else if (result.results && Array.isArray(result.results)) {
            pages = result.results;
        } else if (result.pages) {
            pages = result.pages;
        } else {
            console.log("Using fallback results structure");
        }

        console.log("📄 Processing pages:", pages.length);

        // Generate comprehensive HTML report
        const htmlContent = generateComprehensiveReport(pages, summary, result);
        DOM.reportContent.innerHTML = htmlContent;

        // Enable CSV download
        if (DOM.csvDownloadBtn) {
            DOM.csvDownloadBtn.style.display = 'inline-block';
        }

        // Show success message
        const pagesAnalyzed = pages.length || result.metadata?.total_pages || 'Unknown';
        showMessage(`🎉 Analysis completed! Analyzed ${pagesAnalyzed} pages`, 'success');

    } catch (error) {
        console.error("Error displaying results:", error);
        DOM.reportContent.innerHTML = `
            <div class="alert alert-warning">
                <h4>⚠️ Results Processing Issue</h4>
                <p>The analysis completed successfully, but there was an issue displaying the results.</p>
                <p><strong>Analysis ID:</strong> ${ANALYSIS_STATE.currentAnalysisId}</p>
                <p>You can download the CSV report or refresh the page to try again.</p>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;

        // Still enable CSV download
        if (DOM.csvDownloadBtn) {
            DOM.csvDownloadBtn.style.display = 'inline-block';
        }
    }
}

// FIXED: Generate comprehensive HTML report from results
function generateComprehensiveReport(pages, summary, fullResult) {
    const totalPages = pages.length;
    const websiteUrl = pages[0]?.url || 'Unknown';

    let html = `
        <div class="results-container">
            <div class="results-header">
                <h2>📊 SEO Analysis Results</h2>
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-number">${totalPages}</span>
                        <span class="stat-label">Pages Analyzed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">${summary.crawl_duration ? Math.round(summary.crawl_duration) + 's' : 'N/A'}</span>
                        <span class="stat-label">Crawl Time</span>
                    </div>
                </div>
            </div>

            <div class="analysis-overview">
                <h3>🔍 Analysis Overview</h3>
                <p><strong>Website:</strong> ${websiteUrl}</p>
                <p><strong>Analysis Type:</strong> ${summary.analysis_type || 'Comprehensive SEO Audit'}</p>
                <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
            </div>

            <div class="pages-results">
                <h3>📄 Page-by-Page Results</h3>
                ${generatePagesTable(pages)}
            </div>

            <div class="analysis-summary">
                <h3>📈 Key Findings</h3>
                ${generateSummaryInsights(pages)}
            </div>
        </div>
    `;

    return html;
}

function generatePagesTable(pages) {
    if (!pages || pages.length === 0) {
        return '<p>No pages data available.</p>';
    }

    let tableHtml = `
        <div class="table-responsive">
            <table class="results-table">
                <thead>
                    <tr>
                        <th>URL</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Word Count</th>
                        <th>Issues</th>
                        <th>Load Time</th>
                    </tr>
                </thead>
                <tbody>
    `;

    pages.forEach((page, index) => {
        // Handle both object and dictionary formats
        const url = page.url || page.URL || `Page ${index + 1}`;
        const title = page.title || page.Title || 'No Title';
        const status = page.status_code || page.Status_Code || 'Unknown';
        const wordCount = page.word_count || page.Word_Count || 0;
        const loadTime = page.load_time || page.Load_Time || 0;
        const issues = page.seo_issues?.length || page.Issues?.split(';').length || 0;

        const statusColor = status === 200 || status === '200' ? 'green' : 'red';
        const loadTimeFormatted = loadTime ? `${loadTime.toFixed(2)}s` : 'N/A';

        tableHtml += `
            <tr>
                <td><a href="${url}" target="_blank" title="${url}">${url.length > 50 ? url.substring(0, 50) + '...' : url}</a></td>
                <td title="${title}">${title.length > 40 ? title.substring(0, 40) + '...' : title}</td>
                <td><span style="color: ${statusColor}">${status}</span></td>
                <td>${wordCount.toLocaleString()}</td>
                <td>${issues} issues</td>
                <td>${loadTimeFormatted}</td>
            </tr>
        `;
    });

    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    return tableHtml;
}

function generateSummaryInsights(pages) {
    if (!pages || pages.length === 0) {
        return '<p>No insights available.</p>';
    }

    const totalPages = pages.length;
    const avgWordCount = pages.reduce((sum, page) => sum + (page.word_count || page.Word_Count || 0), 0) / totalPages;
    const pagesWithIssues = pages.filter(page => (page.seo_issues?.length || 0) > 0).length;
    const avgLoadTime = pages.reduce((sum, page) => sum + (page.load_time || page.Load_Time || 0), 0) / totalPages;

    return `
        <div class="insights-grid">
            <div class="insight-card">
                <h4>📝 Content Analysis</h4>
                <p><strong>Average Word Count:</strong> ${Math.round(avgWordCount).toLocaleString()}</p>
                <p><strong>Pages with Content:</strong> ${pages.filter(p => (p.word_count || p.Word_Count || 0) > 100).length}/${totalPages}</p>
            </div>
            <div class="insight-card">
                <h4>🔍 SEO Issues</h4>
                <p><strong>Pages with Issues:</strong> ${pagesWithIssues}/${totalPages}</p>
                <p><strong>Issue Rate:</strong> ${Math.round((pagesWithIssues / totalPages) * 100)}%</p>
            </div>
            <div class="insight-card">
                <h4>⚡ Performance</h4>
                <p><strong>Average Load Time:</strong> ${avgLoadTime.toFixed(2)}s</p>
                <p><strong>Fast Pages (&lt;3s):</strong> ${pages.filter(p => (p.load_time || p.Load_Time || 0) < 3).length}/${totalPages}</p>
            </div>
        </div>
    `;
}

// Control Functions
function handleStartAnalysis() {
    if (DOM.seoForm) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        DOM.seoForm.dispatchEvent(event);
    }
}

function handleCancelAnalysis() {
    console.log("🛑 Cancelling analysis...");

    if (ANALYSIS_STATE.statusPolling) {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
    }

    ANALYSIS_STATE.currentAnalysisId = null;
    ANALYSIS_STATE.isRunning = false;
    ANALYSIS_STATE.retryCount = 0;

    resetToFormState();
    showError('Analysis cancelled by user.');
}

function handleNewAnalysis() {
    console.log("🆕 Starting new analysis...");

    ANALYSIS_STATE.currentAnalysisId = null;
    ANALYSIS_STATE.isRunning = false;
    ANALYSIS_STATE.retryCount = 0;

    if (DOM.seoForm) {
        DOM.seoForm.reset();
    }

    resetToFormState();
    showError('');

    setTimeout(handleWholeWebsiteToggle, 100);
}

async function handleCSVDownload() {
    if (!ANALYSIS_STATE.currentAnalysisId) {
        showError('No analysis ID available for CSV download');
        return;
    }

    try {
        showMessage('Preparing CSV download...', 'info');

        const response = await fetch(`${CONFIG.API_BASE}/api/download-csv/${ANALYSIS_STATE.currentAnalysisId}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `seo_analysis_${ANALYSIS_STATE.currentAnalysisId}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showMessage('CSV downloaded successfully!', 'success');
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'CSV download failed');
        }
    } catch (error) {
        console.error('CSV download error:', error);
        showError(`CSV download failed: ${error.message}`);
    }
}

// UI State Management
function showProgressState() {
    setUIState('progress');
}

function showResultsState() {
    setUIState('results');
}

function resetToFormState() {
    setUIState('form');
}

function setUIState(state) {
    const sections = ['form-section', 'progress-section', 'results-section'];
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    });

    const targetSection = document.getElementById(`${state}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    updateButtonStates(state);
}

function updateButtonStates(state) {
    const buttons = {
        start: DOM.startBtn,
        cancel: DOM.cancelBtn,
        new: DOM.newAnalysisBtn,
        csvDownload: DOM.csvDownloadBtn
    };

    Object.values(buttons).forEach(btn => {
        if (btn) btn.style.display = 'none';
    });

    switch (state) {
        case 'form':
            if (buttons.start) buttons.start.style.display = 'inline-block';
            break;
        case 'progress':
            if (buttons.cancel) buttons.cancel.style.display = 'inline-block';
            break;
        case 'results':
            if (buttons.new) buttons.new.style.display = 'inline-block';
            if (buttons.csvDownload) buttons.csvDownload.style.display = 'inline-block';
            break;
    }
}

function updateProgress(percentage, message, details) {
    if (DOM.progressText) {
        DOM.progressText.textContent = message || 'Processing...';
    }

    if (DOM.progressDetails) {
        DOM.progressDetails.textContent = details || '';
    }

    if (DOM.progressFill && percentage !== null) {
        const safePercentage = Math.min(100, Math.max(0, percentage));
        DOM.progressFill.style.width = `${safePercentage}%`;
    }
}

function showError(message) {
    showMessage(message, 'error');
}

function showMessage(message, type = 'info') {
    if (!DOM.errorMessage) return;

    if (!message) {
        DOM.errorMessage.style.display = 'none';
        return;
    }

    DOM.errorMessage.textContent = message;
    DOM.errorMessage.className = `alert alert-${type}`;
    DOM.errorMessage.style.display = 'block';

    if (type === 'success') {
        setTimeout(() => {
            if (DOM.errorMessage) {
                DOM.errorMessage.style.display = 'none';
            }
        }, 8000);
    }
}

// System Health Check
async function performHealthCheck() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/health`);
        const health = await response.json();

        console.log("🏥 System health check:", health);

        if (DOM.systemStatus) {
            if (health.status === 'healthy') {
                DOM.systemStatus.innerHTML = '🟢 System Online';
                DOM.systemStatus.style.color = '#27ae60';
            } else {
                DOM.systemStatus.innerHTML = '🟡 System Issues';
                DOM.systemStatus.style.color = '#f39c12';
            }
        }
    } catch (error) {
        console.error('Health check failed:', error);
        if (DOM.systemStatus) {
            DOM.systemStatus.innerHTML = '🔴 Connection Error';
            DOM.systemStatus.style.color = '#e74c3c';
        }
    }
}

function updateUI() {
    resetToFormState();
    setTimeout(handleWholeWebsiteToggle, 100);
}

// Export for global access
window.EnhancedSEOAudit = {
    startAnalysis: handleStartAnalysis,
    cancelAnalysis: handleCancelAnalysis,
    downloadCSV: handleCSVDownload,
    healthCheck: performHealthCheck,
    state: ANALYSIS_STATE,
    config: CONFIG
};

console.log("✅ Enhanced SEO Audit Tool V3.0 JavaScript initialization complete!");

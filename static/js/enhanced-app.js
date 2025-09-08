/**
 * Enhanced SEO Audit Tool V3.0 - Complete JavaScript Implementation
 * Production-ready frontend with progress tracking and error handling
 */

console.log("🎯 Enhanced SEO Audit Tool V3.0 JavaScript loaded successfully!");

// Configuration and State Management
const CONFIG = {
    API_BASE: window.location.origin,
    STATUS_POLL_INTERVAL: 2000, // Reduced to 2 seconds for better responsiveness
    MAX_RETRIES: 3,
    RETRY_DELAY: 2000
};

const ANALYSIS_STATE = {
    currentAnalysisId: null,
    isRunning: false,
    statusPolling: null,
    retryCount: 0
};

// DOM Elements (will be initialized when DOM loads)
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

        // Health check
        systemStatus: document.getElementById('system-status')
    };

    // Debug: Log which elements were found
    console.log("DOM Elements initialized:", {
        formFound: !!DOM.seoForm,
        toggleFound: !!DOM.wholeWebsiteToggle,
        maxPagesFound: !!DOM.maxPagesInput
    });
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

    // FIXED: Toggle functionality with proper event handling
    if (DOM.wholeWebsiteToggle) {
        DOM.wholeWebsiteToggle.addEventListener('change', handleWholeWebsiteToggle);
        DOM.wholeWebsiteToggle.addEventListener('click', handleWholeWebsiteToggle);
        console.log("✅ Whole website toggle listener added");

        // Initialize toggle state
        setTimeout(() => {
            handleWholeWebsiteToggle();
        }, 100);
    } else {
        console.error("❌ Whole website toggle not found!");
    }
}

async function handleEnhancedFormSubmit(event) {
    event.preventDefault();
    console.log("🚀 Starting enhanced analysis...", getFormData());

    try {
        showError(''); // Clear any previous errors

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

async function handleStartAnalysis() {
    if (DOM.seoForm) {
        const event = new Event('submit', { bubbles: true, cancelable: true });
        DOM.seoForm.dispatchEvent(event);
    }
}

function handleCancelAnalysis() {
    console.log("🛑 Cancelling analysis...");

    // Stop polling
    if (ANALYSIS_STATE.statusPolling) {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
    }

    // Reset state
    ANALYSIS_STATE.currentAnalysisId = null;
    ANALYSIS_STATE.isRunning = false;
    ANALYSIS_STATE.retryCount = 0;

    // Reset UI
    resetToFormState();
    showError('Analysis cancelled by user.');
}

function handleNewAnalysis() {
    console.log("🆕 Starting new analysis...");

    // Reset state
    ANALYSIS_STATE.currentAnalysisId = null;
    ANALYSIS_STATE.isRunning = false;
    ANALYSIS_STATE.retryCount = 0;

    // Clear form
    if (DOM.seoForm) {
        DOM.seoForm.reset();
    }

    // Reset UI
    resetToFormState();
    showError('');

    // Re-initialize toggle state
    setTimeout(() => {
        handleWholeWebsiteToggle();
    }, 100);
}

// FIXED: Improved toggle handling with visual feedback
function handleWholeWebsiteToggle() {
    console.log("🔄 Toggle changed");

    if (!DOM.wholeWebsiteToggle || !DOM.maxPagesInput) {
        console.error("❌ Toggle elements not found");
        return;
    }

    const isWholeWebsite = DOM.wholeWebsiteToggle.checked;
    const maxPagesGroup = DOM.maxPagesInput.closest('.form-group');

    console.log("🎯 Whole website mode:", isWholeWebsite);

    if (maxPagesGroup) {
        if (isWholeWebsite) {
            maxPagesGroup.style.opacity = '0.5';
            maxPagesGroup.style.pointerEvents = 'none';
            DOM.maxPagesInput.disabled = true;

            // Show whole website message
            let helpText = maxPagesGroup.querySelector('small');
            if (helpText) {
                helpText.textContent = 'Whole website mode: Will discover and analyze ALL pages';
                helpText.style.color = '#e67e22';
                helpText.style.fontWeight = 'bold';
            }
        } else {
            maxPagesGroup.style.opacity = '1';
            maxPagesGroup.style.pointerEvents = 'auto';
            DOM.maxPagesInput.disabled = false;

            // Restore original message
            let helpText = maxPagesGroup.querySelector('small');
            if (helpText) {
                helpText.textContent = 'For focused analysis, start with 5-20 pages';
                helpText.style.color = '';
                helpText.style.fontWeight = '';
            }
        }
    }

    // Update button text based on mode
    if (DOM.startBtn) {
        if (isWholeWebsite) {
            DOM.startBtn.innerHTML = '🌐 Start Whole Website Analysis';
            DOM.startBtn.style.background = '#e67e22';
        } else {
            DOM.startBtn.innerHTML = '🚀 Start Enhanced SEO Analysis';
            DOM.startBtn.style.background = '';
        }
    }
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

    // URL validation
    try {
        new URL(data.website_url);
    } catch (e) {
        return { isValid: false, message: 'Please enter a valid URL (include https://)' };
    }

    // Pages validation (only for non-whole website mode)
    if (!data.whole_website && (data.max_pages < 1 || data.max_pages > 100)) {
        return { isValid: false, message: 'Pages to analyze must be between 1 and 100' };
    }

    return { isValid: true };
}

async function startEnhancedAnalysis(formData) {
    try {
        showProgressState();
        updateProgress(0, 'Starting analysis...', 'Initializing enhanced SEO analysis');

        ANALYSIS_STATE.isRunning = true;
        ANALYSIS_STATE.retryCount = 0;

        // Add analysis mode to progress message
        const analysisType = formData.whole_website ? 'Whole Website Analysis' : 'Selective Page Analysis';
        updateProgress(5, `Starting ${analysisType}...`, `Preparing to analyze ${formData.website_url}`);

        const response = await fetchWithRetry(`${CONFIG.API_BASE}/api/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage;

            try {
                const errorData = JSON.parse(errorText);
                errorMessage = errorData.error || `HTTP ${response.status}: ${response.statusText}`;
            } catch (e) {
                // Response is not JSON (likely HTML error page)
                if (errorText.includes('<html')) {
                    errorMessage = `Server error (${response.status}). Please try again.`;
                } else {
                    errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`;
                }
            }

            // Handle specific status codes
            if (response.status === 429) {
                errorMessage = 'Rate limit exceeded. Please wait before trying again.';
            } else if (response.status === 400) {
                errorMessage = errorMessage || 'Invalid request. Please check your input.';
            }

            throw new Error(errorMessage);
        }

        const result = await response.json();
        console.log("🎉 Analysis started:", result);

        // Store the analysis ID
        ANALYSIS_STATE.currentAnalysisId = result.analysis_id;

        // Start status polling
        startStatusPolling();

        // Update progress
        updateProgress(10, 'Analysis queued successfully!', 
                      `Analysis ID: ${result.analysis_id}\nEstimated duration: ${Math.round(result.estimated_duration_seconds / 60)} minutes`);

    } catch (error) {
        console.error('Error starting analysis:', error);
        ANALYSIS_STATE.isRunning = false;
        throw error;
    }
}

async function fetchWithRetry(url, options, retries = CONFIG.MAX_RETRIES) {
    for (let i = 0; i < retries; i++) {
        try {
            return await fetch(url, options);
        } catch (error) {
            console.warn(`Fetch attempt ${i + 1} failed:`, error);
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, CONFIG.RETRY_DELAY * (i + 1)));
        }
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
                showError('Lost connection to analysis. Please refresh the page and check results manually.');
                resetToFormState();
            }
        }
    }, CONFIG.STATUS_POLL_INTERVAL);

    // Also check immediately
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

    // Reset retry count on successful response
    ANALYSIS_STATE.retryCount = 0;

    // Update progress with enhanced information
    if (status.progress_info) {
        updateProgress(
            status.progress_info.percentage,
            status.progress,
            `Step ${status.progress_info.current_step}/${status.progress_info.total_steps} | ${status.progress_info.elapsed_time} elapsed | ~${status.progress_info.estimated_remaining} remaining`
        );
    } else {
        updateProgress(null, status.progress || 'Processing...', status.status || 'Running analysis...');
    }

    // Handle completion
    if (status.status === 'completed') {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
        ANALYSIS_STATE.isRunning = false;

        updateProgress(100, '✅ Analysis Complete!', 'Loading comprehensive results...');

        setTimeout(() => {
            loadEnhancedResults();
        }, 1000);

    } else if (status.status === 'error') {
        clearInterval(ANALYSIS_STATE.statusPolling);
        ANALYSIS_STATE.statusPolling = null;
        ANALYSIS_STATE.isRunning = false;

        showError(`❌ Analysis failed: ${status.error || 'Unknown error occurred'}`);
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

function displayResults(result) {
    showResultsState();

    // Display the report content
    if (DOM.reportContent && result.report) {
        // Enhanced markdown to HTML conversion
        const htmlContent = convertMarkdownToHTML(result.report);
        DOM.reportContent.innerHTML = htmlContent;

        // Add some styling to the results
        DOM.reportContent.style.maxHeight = 'none';
        DOM.reportContent.style.overflow = 'visible';
    }

    // Enable CSV download if available
    if (DOM.csvDownloadBtn && result.metadata && result.metadata.status === 'success') {
        DOM.csvDownloadBtn.style.display = 'inline-block';
    }

    // Show enhanced completion message
    const pagesAnalyzed = result.metadata?.pages_analyzed || 'Unknown';
    const duration = result.metadata?.crawl_duration ? 
        ` in ${Math.round(result.metadata.crawl_duration)}s` : '';

    showMessage(`🎉 Analysis completed successfully! Analyzed ${pagesAnalyzed} pages${duration}`, 'success');
}

// Enhanced markdown to HTML conversion
function convertMarkdownToHTML(markdown) {
    return markdown
        // Headers
        .replace(/^# (.*$)/gm, '<h1 class="seo-h1">$1</h1>')
        .replace(/^## (.*$)/gm, '<h2 class="seo-h2">$1</h2>')
        .replace(/^### (.*$)/gm, '<h3 class="seo-h3">$1</h3>')
        .replace(/^#### (.*$)/gm, '<h4 class="seo-h4">$1</h4>')

        // Bold and italic
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')

        // Lists (improved)
        .replace(/^\* (.*$)/gm, '<li>$1</li>')
        .replace(/^- (.*$)/gm, '<li>$1</li>')
        .replace(/(- .*<\/li>)/s, '<ul>$1</ul>')

        // Tables (improved)
        .replace(/^\|(.*)\|$/gm, function(match, content) {
            const cells = content.split('|').map(cell => `<td>${cell.trim()}</td>`).join('');
            return `<tr>${cells}</tr>`;
        })
        .replace(/(<tr>.*<\/tr>\s*)+/gs, function(match) {
            return `<table class="seo-table">${match}</table>`;
        })

        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')

        // Wrap in paragraphs
        .replace(/^(?!<[h|u|t|l])/gm, '<p>')
        .replace(/(.*?)$/gm, '$1</p>')

        // Clean up empty paragraphs
        .replace(/<p><\/p>/g, '')
        .replace(/<p>(<[^>]*>)/g, '$1')
        .replace(/(<\/[^>]*>)<\/p>/g, '$1');
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
    // Hide all sections
    const sections = ['form-section', 'progress-section', 'results-section'];
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.style.display = 'none';
    });

    // Show appropriate section
    const targetSection = document.getElementById(`${state}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
    }

    // Update button states
    updateButtonStates(state);
}

function updateButtonStates(state) {
    const buttons = {
        start: DOM.startBtn,
        cancel: DOM.cancelBtn,
        new: DOM.newAnalysisBtn,
        csvDownload: DOM.csvDownloadBtn
    };

    // Hide all buttons first
    Object.values(buttons).forEach(btn => {
        if (btn) btn.style.display = 'none';
    });

    // Show appropriate buttons based on state
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

        // Enhanced visual feedback
        if (safePercentage < 100) {
            DOM.progressFill.style.background = 'linear-gradient(45deg, #3498db, #2ecc71)';
        } else {
            DOM.progressFill.style.background = 'linear-gradient(45deg, #27ae60, #2ecc71)';
        }
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

    // Auto-hide success messages
    if (type === 'success') {
        setTimeout(() => {
            if (DOM.errorMessage) {
                DOM.errorMessage.style.display = 'none';
            }
        }, 8000); // Increased to 8 seconds
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

// Update UI based on current state
function updateUI() {
    // Set initial state
    resetToFormState();

    // Configure whole website toggle
    setTimeout(() => {
        handleWholeWebsiteToggle();
    }, 100);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
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

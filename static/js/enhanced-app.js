/**
* Start analysis
*/
function startAnalysis(formData) {
   console.log('🔄 Starting analysis with data:', formData);
   
   // Update UI state
   isAnalysisRunning = true;
   updateSubmitButton(true);
   showLoading();
   enableForm(false);
   hideAlert();
   hideResults();
   
   // Send analysis request
   fetch('/api/analyze', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
       },
       body: JSON.stringify(formData),
       timeout: CONFIG.API_TIMEOUT
   })
   .then(response => {
       if (!response.ok) {
           throw new Error(`HTTP ${response.status}: ${response.statusText}`);
       }
       return response.json();
   })
   .then(data => {
       console.log('✅ Analysis started:', data);
       
       if (data.error) {
           throw new Error(data.error);
       }
       
       currentAnalysisId = data.analysis_id;
       submitInProgress = false;
       
       // Start status checking
       startStatusChecking();
       
       showAlert(`Analysis started successfully! ID: ${data.analysis_id}`, 'success');
       
   })
   .catch(error => {
       console.error('❌ Analysis start failed:', error);
       
       submitInProgress = false;
       isAnalysisRunning = false;
       
       showAlert(`Failed to start analysis: ${error.message}`, 'error');
       resetAnalysisState();
   });
}

/**
* Start status checking
*/
function startStatusChecking() {
   if (!currentAnalysisId) {
       console.error('No analysis ID available for status checking');
       return;
   }
   
   console.log('🔍 Starting status checks for analysis:', currentAnalysisId);
   
   // Clear any existing interval
   if (statusCheckInterval) {
       clearInterval(statusCheckInterval);
   }
   
   statusCheckCount = 0;
   showProgress();
   
   // Check status immediately
   checkAnalysisStatus();
   
   // Set up periodic checks
   statusCheckInterval = setInterval(() => {
       if (statusCheckCount >= CONFIG.MAX_STATUS_CHECKS) {
           console.warn('⏰ Max status checks reached, stopping');
           clearInterval(statusCheckInterval);
           showAlert('Analysis is taking too long. Please check back later.', 'warning');
           resetAnalysisState();
           return;
       }
       
       checkAnalysisStatus();
   }, CONFIG.STATUS_CHECK_INTERVAL);
}

/**
* Check analysis status
*/
function checkAnalysisStatus() {
   if (!currentAnalysisId) {
       return;
   }
   
   statusCheckCount++;
   
   fetch(`/api/status/${currentAnalysisId}`)
   .then(response => {
       if (!response.ok) {
           throw new Error(`HTTP ${response.status}`);
       }
       return response.json();
   })
   .then(data => {
       console.log('📊 Analysis status:', data);
       
       updateProgressDisplay(data);
       
       if (data.status === 'completed') {
           console.log('🎉 Analysis completed!');
           clearInterval(statusCheckInterval);
           statusCheckInterval = null;
           loadAnalysisResults(currentAnalysisId);
       } else if (data.status === 'failed') {
           console.error('❌ Analysis failed:', data.error_message);
           clearInterval(statusCheckInterval);
           statusCheckInterval = null;
           showAlert(`Analysis failed: ${data.error_message || 'Unknown error'}`, 'error');
           resetAnalysisState();
       } else if (data.status === 'cancelled') {
           console.log('⏹️ Analysis was cancelled');
           clearInterval(statusCheckInterval);
           statusCheckInterval = null;
           showAlert('Analysis was cancelled', 'warning');
           resetAnalysisState();
       }
       // Continue checking for running status
       
   })
   .catch(error => {
       console.error('❌ Status check failed:', error);
       
       // Don't stop on network errors, just log them
       if (statusCheckCount > 10) {
           clearInterval(statusCheckInterval);
           statusCheckInterval = null;
           showAlert('Lost connection to server. Please refresh and try again.', 'error');
           resetAnalysisState();
       }
   });
}

/**
* Load analysis results
*/
function loadAnalysisResults(analysisId) {
   console.log('📊 Loading results for analysis:', analysisId);
   
   fetch(`/api/report/${analysisId}`)
   .then(response => {
       if (!response.ok) {
           throw new Error(`HTTP ${response.status}`);
       }
       return response.json();
   })
   .then(data => {
       console.log('📊 Enhanced results loaded:', data);
       
       hideLoading();
       hideProgress();
       displayResults(data);
       updateSubmitButton(false);
       enableForm(true);
       isAnalysisRunning = false;
       
       // Load updated recent analyses
       loadRecentAnalyses();
       
   })
   .catch(error => {
       console.error('❌ Failed to load results:', error);
       showAlert('Failed to load analysis results. Please try again.', 'error');
       resetAnalysisState();
   });
}

/**
* Display analysis results
*/
function displayResults(data) {
   if (!elements.resultsDiv || !data.results) {
       console.error('Missing results container or data');
       return;
   }
   
   console.log('🎨 Displaying results for analysis:', data.analysis_id);
   
   const results = data.results;
   const metadata = data.metadata || {};
   
   let html = `
       <div class="results-header">
           <div class="d-flex justify-content-between align-items-center mb-4">
               <h2>📊 SEO Analysis Results</h2>
               <div>
                   <span class="badge badge-success">Analysis ID: ${data.analysis_id}</span>
                   ${data.file_info?.csv_available ? 
                       `<a href="/api/download-csv/${data.analysis_id}" class="btn btn-outline-primary btn-sm ml-2">
                           <i class="fas fa-download"></i> Download CSV
                       </a>` : ''
                   }
               </div>
           </div>
       </div>
       
       <div class="row">
           <!-- Executive Summary -->
           <div class="col-12 mb-4">
               <div class="card">
                   <div class="card-header">
                       <h3 class="mb-0">📈 Executive Summary</h3>
                   </div>
                   <div class="card-body">
                       ${generateExecutiveSummary(results)}
                   </div>
               </div>
           </div>
       </div>
       
       <div class="row">
           <!-- SEO Score Card -->
           <div class="col-lg-4 col-md-6 mb-4">
               <div class="card text-center">
                   <div class="card-body">
                       <h4 class="card-title">🎯 Overall SEO Score</h4>
                       <div class="display-4 font-weight-bold ${getScoreClass(results.overall_score || 0)}">
                           ${results.overall_score || 0}/100
                       </div>
                       <p class="text-muted">${getScoreDescription(results.overall_score || 0)}</p>
                   </div>
               </div>
           </div>
           
           <!-- Pages Analyzed -->
           <div class="col-lg-4 col-md-6 mb-4">
               <div class="card text-center">
                   <div class="card-body">
                       <h4 class="card-title">📄 Pages Analyzed</h4>
                       <div class="display-4 font-weight-bold text-info">
                           ${results.pages ? results.pages.length : 0}
                       </div>
                       <p class="text-muted">Total pages scanned</p>
                   </div>
               </div>
           </div>
           
           <!-- Issues Found -->
           <div class="col-lg-4 col-md-6 mb-4">
               <div class="card text-center">
                   <div class="card-body">
                       <h4 class="card-title">⚠️ Total Issues</h4>
                       <div class="display-4 font-weight-bold text-warning">
                           ${countTotalIssues(results)}
                       </div>
                       <p class="text-muted">Issues requiring attention</p>
                   </div>
               </div>
           </div>
       </div>
       
       <!-- SERP Analysis -->
       ${results.serp_analysis ? generateSERPAnalysis(results.serp_analysis) : ''}
       
       <!-- Page Details -->
       <div class="row">
           <div class="col-12">
               <div class="card">
                   <div class="card-header">
                       <h3 class="mb-0">📋 Detailed Page Analysis</h3>
                   </div>
                   <div class="card-body">
                       ${generatePageDetails(results.pages || [])}
                   </div>
               </div>
           </div>
       </div>
       
       <!-- Recommendations -->
       <div class="row">
           <div class="col-12">
               <div class="card">
                   <div class="card-header">
                       <h3 class="mb-0">💡 Recommendations</h3>
                   </div>
                   <div class="card-body">
                       ${generateRecommendations(results)}
                   </div>
               </div>
           </div>
       </div>
   `;
   
   elements.resultsDiv.innerHTML = html;
   elements.resultsDiv.style.display = 'block';
   
   // Scroll to results
   elements.resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
* Generate executive summary
*/
function generateExecutiveSummary(results) {
   const totalPages = results.pages ? results.pages.length : 0;
   const averageScore = results.overall_score || 0;
   const totalIssues = countTotalIssues(results);
   
   return `
       <div class="row text-center">
           <div class="col-md-3">
               <div class="metric">
                   <div class="metric-value">${totalPages}</div>
                   <div class="metric-label">Pages Analyzed</div>
               </div>
           </div>
           <div class="col-md-3">
               <div class="metric">
                   <div class="metric-value ${getScoreClass(averageScore)}">${averageScore}</div>
                   <div class="metric-label">Average SEO Score</div>
               </div>
           </div>
           <div class="col-md-3">
               <div class="metric">
                   <div class="metric-value text-warning">${totalIssues}</div>
                   <div class="metric-label">Total Issues</div>
               </div>
           </div>
           <div class="col-md-3">
               <div class="metric">
                   <div class="metric-value text-info">${results.analysis_type || 'selective'}</div>
                   <div class="metric-label">Analysis Type</div>
               </div>
           </div>
       </div>
   `;
}

/**
* Generate SERP analysis section
*/
function generateSERPAnalysis(serpData) {
   if (!serpData || !serpData.competitors || serpData.competitors.length === 0) {
       return '';
   }
   
   return `
       <div class="row">
           <div class="col-12 mb-4">
               <div class="card">
                   <div class="card-header">
                       <h3 class="mb-0">🔍 SERP Analysis</h3>
                   </div>
                   <div class="card-body">
                       <div class="table-responsive">
                           <table class="table table-hover">
                               <thead>
                                   <tr>
                                       <th>Position</th>
                                       <th>Domain</th>
                                       <th>Title</th>
                                       <th>Snippet</th>
                                   </tr>
                               </thead>
                               <tbody>
                                   ${serpData.competitors.map((competitor, index) => `
                                       <tr>
                                           <td><span class="badge badge-primary">${index + 1}</span></td>
                                           <td><strong>${competitor.domain || 'N/A'}</strong></td>
                                           <td>${competitor.title || 'N/A'}</td>
                                           <td>${competitor.snippet || 'N/A'}</td>
                                       </tr>
                                   `).join('')}
                               </tbody>
                           </table>
                       </div>
                   </div>
               </div>
           </div>
       </div>
   `;
}

/**
* Generate page details
*/
function generatePageDetails(pages) {
   if (!pages || pages.length === 0) {
       return '<p class="text-muted">No pages analyzed.</p>';
   }
   
   return `
       <div class="table-responsive">
           <table class="table table-hover">
               <thead>
                   <tr>
                       <th>URL</th>
                       <th>Title</th>
                       <th>Status</th>
                       <th>SEO Score</th>
                       <th>Word Count</th>
                       <th>Load Time</th>
                       <th>Issues</th>
                   </tr>
               </thead>
               <tbody>
                   ${pages.map(page => `
                       <tr>
                           <td>
                               <a href="${page.url}" target="_blank" title="${page.url}">
                                   ${truncateText(page.url, 50)}
                                   <i class="fas fa-external-link-alt ml-1"></i>
                               </a>
                           </td>
                           <td>${page.title ? truncateText(page.title, 60) : '<em>No title</em>'}</td>
                           <td>
                               <span class="badge ${getStatusBadgeClass(page.status_code)}">
                                   ${page.status_code}
                               </span>
                           </td>
                           <td>
                               <span class="font-weight-bold ${getScoreClass(page.seo_score || 0)}">
                                   ${page.seo_score || 0}/100
                               </span>
                           </td>
                           <td>${page.word_count || 0}</td>
                           <td>${(page.load_time || 0).toFixed(2)}s</td>
                           <td>
                               ${page.issues && page.issues.length > 0 ? 
                                   `<span class="badge badge-warning">${page.issues.length}</span>` : 
                                   '<span class="badge badge-success">0</span>'
                               }
                           </td>
                       </tr>
                   `).join('')}
               </tbody>
           </table>
       </div>
   `;
}

/**
* Generate recommendations
*/
function generateRecommendations(results) {
   const recommendations = [];
   
   // Analyze results and generate recommendations
   if (results.overall_score < 70) {
       recommendations.push({
           priority: 'high',
           title: 'Improve Overall SEO Score',
           description: 'Your overall SEO score is below average. Focus on fixing critical issues first.'
       });
   }
   
   if (results.pages) {
       const pagesWithoutTitles = results.pages.filter(p => !p.title).length;
       if (pagesWithoutTitles > 0) {
           recommendations.push({
               priority: 'critical',
               title: 'Add Missing Page Titles',
               description: `${pagesWithoutTitles} pages are missing title tags, which is critical for SEO.`
           });
       }
       
       const pagesWithoutMetaDesc = results.pages.filter(p => !p.meta_description).length;
       if (pagesWithoutMetaDesc > 0) {
           recommendations.push({
               priority: 'high',
               title: 'Add Meta Descriptions',
               description: `${pagesWithoutMetaDesc} pages are missing meta descriptions.`
           });
       }
       
       const slowPages = results.pages.filter(p => (p.load_time || 0) > 3).length;
       if (slowPages > 0) {
           recommendations.push({
               priority: 'medium',
               title: 'Improve Page Load Times',
               description: `${slowPages} pages have slow load times (>3 seconds).`
           });
       }
   }
   
   // Default recommendations if none generated
   if (recommendations.length === 0) {
       recommendations.push({
           priority: 'low',
           title: 'Great Job!',
           description: 'Your website is performing well. Continue monitoring and making incremental improvements.'
       });
   }
   
   return recommendations.map(rec => `
       <div class="alert alert-${getPriorityAlertClass(rec.priority)} d-flex align-items-center">
           <div class="mr-3">
               <i class="fas ${getPriorityIcon(rec.priority)} fa-2x"></i>
           </div>
           <div>
               <h5 class="alert-heading mb-1">${rec.title}</h5>
               <p class="mb-0">${rec.description}</p>
           </div>
       </div>
   `).join('');
}

/**
* Load recent analyses
*/
function loadRecentAnalyses() {
   if (!elements.recentAnalyses) {
       return;
   }
   
   fetch('/api/recent-analyses?limit=5')
   .then(response => response.json())
   .then(data => {
       if (data.analyses && data.analyses.length > 0) {
           displayRecentAnalyses(data.analyses);
       } else {
           elements.recentAnalyses.innerHTML = '<p class="text-muted">No recent analyses found.</p>';
       }
   })
   .catch(error => {
       console.error('Failed to load recent analyses:', error);
       elements.recentAnalyses.innerHTML = '<p class="text-muted">Failed to load recent analyses.</p>';
   });
}

/**
* Display recent analyses
*/
function displayRecentAnalyses(analyses) {
   const html = analyses.map(analysis => `
       <div class="card mb-2">
           <div class="card-body py-2">
               <div class="d-flex justify-content-between align-items-center">
                   <div>
                       <strong>${analysis.website_url}</strong>
                       <small class="text-muted d-block">
                           ${analysis.target_keyword} • ${analysis.pages_analyzed} pages • 
                           ${new Date(analysis.created_at).toLocaleDateString()}
                       </small>
                   </div>
                   <button class="btn btn-outline-primary btn-sm" 
                           onclick="loadPreviousAnalysis('${analysis.id}')">
                       View Results
                   </button>
               </div>
           </div>
       </div>
   `).join('');
   
   elements.recentAnalyses.innerHTML = html;
}

/**
* Load previous analysis
*/
function loadPreviousAnalysis(analysisId) {
   console.log('📂 Loading previous analysis:', analysisId);
   
   // Reset current state
   resetAnalysisState();
   
   // Show loading
   showLoading();
   
   // Load the analysis results
   fetch(`/api/report/${analysisId}`)
   .then(response => {
       if (!response.ok) {
           throw new Error(`Failed to load analysis: ${response.status}`);
       }
       return response.json();
   })
   .then(data => {
       console.log('📊 Previous analysis loaded:', data);
       hideLoading();
       displayResults(data);
       showAlert('Previous analysis loaded successfully', 'success');
   })
   .catch(error => {
       console.error('❌ Failed to load previous analysis:', error);
       hideLoading();
       showAlert('Failed to load previous analysis', 'error');
   });
}

/**
* Perform health check
*/
function performHealthCheck() {
   fetch('/api/health')
   .then(response => response.json())
   .then(data => {
       console.log('🏥 System health check:', data);
       
       if (data.status !== 'healthy') {
           showAlert('System health check failed. Some features may not work properly.', 'warning');
       }
   })
   .catch(error => {
       console.error('❌ Health check failed:', error);
   });
}

// UI Helper Functions

/**
* Update submit button state
*/
function updateSubmitButton(isLoading) {
   if (!elements.submitBtn) return;
   
   if (isLoading) {
       elements.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
       elements.submitBtn.disabled = true;
       elements.submitBtn.classList.add('disabled');
       
       if (elements.newAnalysisBtn) {
           elements.newAnalysisBtn.style.display = 'inline-block';
       }
       if (elements.cancelBtn) {
           elements.cancelBtn.style.display = 'inline-block';
       }
   } else {
       elements.submitBtn.innerHTML = '<i class="fas fa-search"></i> Start Enhanced SEO Analysis';
       elements.submitBtn.disabled = false;
       elements.submitBtn.classList.remove('disabled');
       
       if (elements.newAnalysisBtn) {
           elements.newAnalysisBtn.style.display = 'none';
       }
       if (elements.cancelBtn) {
           elements.cancelBtn.style.display = 'none';
       }
   }
}

/**
* Show/hide loading indicator
*/
function showLoading() {
   if (elements.loadingDiv) {
       elements.loadingDiv.style.display = 'block';
   }
}

function hideLoading() {
   if (elements.loadingDiv) {
       elements.loadingDiv.style.display = 'none';
   }
}

/**
* Show/hide progress indicator
*/
function showProgress() {
   if (elements.progressDiv) {
       elements.progressDiv.style.display = 'block';
   }
}

function hideProgress() {
   if (elements.progressDiv) {
       elements.progressDiv.style.display = 'none';
   }
}

/**
* Update progress display
*/
function updateProgressDisplay(statusData) {
   if (!elements.progressBar || !elements.progressText) {
       return;
   }
   
   const progress = statusData.progress || 0;
   const message = statusData.message || 'Processing...';
   const elapsed = statusData.elapsed_formatted || '0s';
   
   elements.progressBar.style.width = `${progress}%`;
   elements.progressBar.setAttribute('aria-valuenow', progress);
   elements.progressText.textContent = `${message} (${elapsed} elapsed)`;
}

/**
* Show/hide results
*/
function hideResults() {
   if (elements.resultsDiv) {
       elements.resultsDiv.style.display = 'none';
   }
}

/**
* Enable/disable form
*/
function enableForm(enabled) {
   const formElements = elements.form ? elements.form.querySelectorAll('input, select, textarea') : [];
   formElements.forEach(element => {
       element.disabled = !enabled;
   });
}

/**
* Show alert message
*/
function showAlert(message, type = 'info') {
   if (!elements.alertDiv) return;
   
   const alertClasses = {
       'success': 'alert-success',
       'error': 'alert-danger',
       'warning': 'alert-warning',
       'info': 'alert-info'
   };
   
   const alertClass = alertClasses[type] || 'alert-info';
   
   elements.alertDiv.innerHTML = `
       <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
           ${message}
           <button type="button" class="close" data-dismiss="alert" aria-label="Close">
               <span aria-hidden="true">&times;</span>
           </button>
       </div>
   `;
   
   elements.alertDiv.style.display = 'block';
   
   // Auto-hide success/info alerts after 5 seconds
   if (type === 'success' || type === 'info') {
       setTimeout(() => {
           hideAlert();
       }, 5000);
   }
}

/**
* Hide alert message
*/
function hideAlert() {
   if (elements.alertDiv) {
       elements.alertDiv.style.display = 'none';
   }
}

// Form Validation Functions

/**
* Validate form data
*/
function validateForm(formData) {
   let isValid = true;
   
   // Clear previous errors
   clearAllFieldErrors();
   
   // Validate website URL
   if (!formData.website_url) {
       showFieldError('websiteUrl', 'Website URL is required');
       isValid = false;
   } else if (!isValidUrl(formData.website_url)) {
       showFieldError('websiteUrl', 'Please enter a valid website URL');
       isValid = false;
   }
   
   // Validate target keyword
   if (!formData.target_keyword) {
       showFieldError('targetKeyword', 'Target keyword is required');
       isValid = false;
   }
   
   // Validate max pages
   if (!formData.whole_website && (formData.max_pages < 1 || formData.max_pages > 50)) {
       showFieldError('maxPages', 'Max pages must be between 1 and 50');
       isValid = false;
   }
   
   return isValid;
}

/**
* Validate individual field
*/
function validateField(event) {
   const field = event.target;
   const value = field.value.trim();
   
   clearFieldError(field.id);
   
   if (field.id === 'websiteUrl' && value && !isValidUrl(value)) {
       showFieldError(field.id, 'Please enter a valid website URL');
   }
}

/**
* Show field error
*/
function showFieldError(fieldId, message) {
   const field = document.getElementById(fieldId);
   if (!field) return;
   
   field.classList.add('is-invalid');
   
   let errorElement = field.parentNode.querySelector('.invalid-feedback');
   if (!errorElement) {
       errorElement = document.createElement('div');
       errorElement.classList.add('invalid-feedback');
       field.parentNode.appendChild(errorElement);
   }
   
   errorElement.textContent = message;
}

/**
* Clear field error
*/
function clearFieldError(fieldId) {
   const field = document.getElementById(fieldId);
   if (!field) return;
   
   field.classList.remove('is-invalid');
   
   const errorElement = field.parentNode.querySelector('.invalid-feedback');
   if (errorElement) {
       errorElement.remove();
   }
}

/**
* Clear all field errors
*/
function clearAllFieldErrors() {
   const invalidFields = document.querySelectorAll('.is-invalid');
   invalidFields.forEach(field => {
       field.classList.remove('is-invalid');
   });
   
   const errorElements = document.querySelectorAll('.invalid-feedback');
   errorElements.forEach(element => {
       element.remove();
   });
}

// Utility Functions

/**
* Check if URL is valid
*/
function isValidUrl(string) {
   try {
       const url = new URL(string);
       return url.protocol === 'http:' || url.protocol === 'https:';
   } catch {
       return false;
   }
}

/**
* Debounce function
*/
function debounce(func, wait) {
   let timeout;
   return function executedFunction(...args) {
       const later = () => {
           clearTimeout(timeout);
           func(...args);
       };
       clearTimeout(timeout);
       timeout = setTimeout(later, wait);
   };
}

/**
* Truncate text
*/
function truncateText(text, maxLength) {
   if (!text) return '';
   return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

/**
* Get score CSS class
*/
function getScoreClass(score) {
   if (score >= 90) return 'text-success';
   if (score >= 70) return 'text-warning';
   if (score >= 50) return 'text-orange';
   return 'text-danger';
}

/**
* Get score description
*/
function getScoreDescription(score) {
   if (score >= 90) return 'Excellent';
   if (score >= 80) return 'Good';
   if (score >= 60) return 'Average';
   if (score >= 40) return 'Below Average';
   return 'Poor';
}

/**
* Get status badge class
*/
function getStatusBadgeClass(statusCode) {
   if (statusCode >= 200 && statusCode < 300) return 'badge-success';
   if (statusCode >= 300 && statusCode < 400) return 'badge-warning';
   return 'badge-danger';
}

/**
* Count total issues across all pages
*/
function countTotalIssues(results) {
   if (!results.pages) return 0;
   return results.pages.reduce((total, page) => {
       return total + (page.issues ? page.issues.length : 0);
   }, 0);
}

/**
* Get priority alert class
*/
function getPriorityAlertClass(priority) {
   const classes = {
       'critical': 'danger',
       'high': 'warning',
       'medium': 'info',
       'low': 'success'
   };
   return classes[priority] || 'info';
}

/**
* Get priority icon
*/
function getPriorityIcon(priority) {
   const icons = {
       'critical': 'fa-exclamation-triangle',
       'high': 'fa-exclamation-circle',
       'medium': 'fa-info-circle',
       'low': 'fa-check-circle'
   };
   return icons[priority] || 'fa-info-circle';
}

// Make functions available globally for onclick handlers
window.loadPreviousAnalysis = loadPreviousAnalysis;

console.log('✅ Enhanced SEO Audit Tool V3.0 JavaScript initialization complete!');

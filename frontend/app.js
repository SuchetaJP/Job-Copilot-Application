/**
 * app.js - Main application controller
 * 
 * This file:
 * 1. Initializes the application
 * 2. Manages global state
 * 3. Coordinates between components
 * 4. Handles routing between views
 */

// ============================================================
// CONFIGURATION
// ============================================================

//const API_BASE_URL = '[localhost](http://localhost:8000)';--added extra
//const API_BASE_URL = 'http://localhost:8000';

// const API_BASE_URL = window.location.hostname === 'localhost' 
//     ? 'http://localhost:8000'
//     : '[job-copilot-api.onrender.com](https://job-copilot-api.onrender.com)';  // Your Render API URL

// const API_BASE_URL = window.location.hostname === 'localhost' || 
//     ? 'http://localhost:8000'
//     : 'https://job-copilot-api.onrender.com'; 


    // const API_BASE_URL = window.location.hostname === "localhost" ||   window.location.hostname === "127.0.0.1"
    //     ? "http://127.0.0.1:8000"
    //     : "https://job-copilot-application.onrender.com";--removed here--working

// ============================================================
// GLOBAL STATE
// ============================================================

const AppState = {
    token: localStorage.getItem('token'),
    user: null,
    roles: [],
    currentRoleId: null,
    currentArtifact: 'fit',
};

// ============================================================
// API UTILITIES
// ============================================================

/**
 * Make an authenticated API request.
 * 
 * @param {string} endpoint - API endpoint (e.g., '/api/users/me')
 * @param {object} options - Fetch options
 * @returns {Promise<object>} Response data
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const headers = {
        ...options.headers,
    };
    
    // Add auth token if we have one
    if (AppState.token) {
        headers['Authorization'] = `Bearer ${AppState.token}`;
    }
    
    // Add content-type for JSON bodies
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }
    
    const response = await fetch(url, {
        ...options,
        headers,
    });
    
    // Handle auth errors
    if (response.status === 401) {
        logout();
        throw new Error('Session expired. Please login again.');
    }
    
    // Parse response
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.detail || 'Request failed');
    }
    
    return data;
}

// ============================================================
// VIEW MANAGEMENT
// ============================================================

/**
 * Show a specific section, hide others.
 * 
 * @param {string} sectionId - ID of section to show
 */
function showSection(sectionId) {
    const sections = ['auth-section', 'dashboard-section'];
    
    sections.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.toggle('hidden', id !== sectionId);
        }
    });
}

/**
 * Show a specific panel in the dashboard.
 * 
 * @param {string} panelId - ID of panel to show
 */
function showPanel(panelId) {
    const panels = [
        'new-application-panel',
        'application-details-panel',
        'empty-state-panel'
    ];
    
    panels.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.toggle('hidden', id !== panelId);
        }
    });
}

// ============================================================
// AUTHENTICATION
// ============================================================

/**
 * Log out the current user.
 */
function logout() {
    AppState.token = null;
    AppState.user = null;
    AppState.roles = [];
    localStorage.removeItem('token');
    showSection('auth-section');
    updateNavAuth();
}

/**
 * Update the auth navigation area.
 */
function updateNavAuth() {
    const navAuth = document.getElementById('nav-auth');
    
    if (AppState.user) {
        navAuth.innerHTML = `
            <span>${AppState.user.email}</span>
            <button class="btn btn-secondary btn-small" onclick="logout()">Logout</button>
        `;
    } else {
        navAuth.innerHTML = '';
    }
}

/**
 * Check if user is authenticated and load their data.
 */
async function checkAuth() {
    if (!AppState.token) {
        showSection('auth-section');
        return;
    }
    
    try {
        AppState.user = await apiRequest('/api/users/me');
        updateNavAuth();
        showSection('dashboard-section');
        await loadRoles();
    } catch (error) {
        console.error('Auth check failed:', error);
        logout();
    }
}

// ============================================================
// ROLES MANAGEMENT
// ============================================================

/**
 * Load all roles for the current user.
 */
async function loadRoles() {
    try {
        debugger
        AppState.roles = await apiRequest('/api/applications');
        renderRolesList();
        
        if (AppState.roles.length === 0) {
            showPanel('empty-state-panel');
        } else if (AppState.currentRoleId) {
            loadRoleDetails(AppState.currentRoleId);
        } else {
            showPanel('empty-state-panel');
        }
    } catch (error) {
        console.error('Failed to load roles:', error);
    }
}

/**
 * Render the roles list in the sidebar.
 */
function renderRolesList() {
    debugger
    const list = document.getElementById('roles-list');
    
    if (AppState.roles.length === 0) {
        list.innerHTML = '<li class="empty-list">No applications yet</li>';
        return;
    }
    
    list.innerHTML = AppState.roles.map(role => `
        <li class="role-item ${role.id === AppState.currentRoleId ? 'active' : ''}"
            onclick="loadRoleDetails(${role.id})">
            <h3>${escapeHtml(role.job_title)}</h3>
            <p>${escapeHtml(role.company)}</p>
            <span class="role-status status-${role.status}">${(role.status)}</span>
           
        </li>
    `).join('');
}

 /**<span class="role-status status-${role.status}">${formatStatus(role.status)}</span>--added extra**/
/**
 * Load and display details for a specific role.
 * 
 * @param {number} roleId - Role ID to load
 */
async function loadRoleDetails(roleId) {
    try {
        const role = await apiRequest(`/api/applications/${roleId}`);
        AppState.currentRoleId = roleId;
        renderRolesList(); // Update active state
        displayRoleDetails(role);
        showPanel('application-details-panel');
    } catch (error) {
        console.error('Failed to load role details:', error);
    }
}

/**
 * Display role details in the main panel.
 * 
 * @param {object} role - Role data with drafts
 */
function displayRoleDetails(role) {
    // Update header
    document.getElementById('details-title').textContent = 
        `${role.job_title} at ${role.company}`;
    document.getElementById('status-select').value = role.status;
    
    // Display artifacts
    role.drafts.forEach(draft => {
        const panelId = getArtifactPanelId(draft.draft_type);
        const panel = document.getElementById(panelId);
        
        if (draft.draft_type === 'fit_analysis') {
            panel.innerHTML = renderFitAnalysis(JSON.parse(draft.content));
        } else if (draft.draft_type === 'resume_rewrite') {
            panel.innerHTML = renderResumeDiff(
                JSON.parse(role.original_resume).text,
                draft.content
            );
        } else {
            panel.innerHTML = renderMarkdown(draft.content);
        }
    });
    
    // Show first tab
    showArtifactTab('fit');
}

/**
 * Map draft type to panel ID.
 */
function getArtifactPanelId(draftType) {
    const map = {
        'fit_analysis': 'artifact-fit',
        'resume_rewrite': 'artifact-resume',
        'cover_letter': 'artifact-cover',
        'interview_qa': 'artifact-interview'
    };
    return map[draftType];
}

/**
 * Show a specific artifact tab.
 * 
 * @param {string} artifact - Artifact type (fit, resume, cover, interview)
 */
function showArtifactTab(artifact) {
    AppState.currentArtifact = artifact;
    
    // Update tab buttons
    document.querySelectorAll('.artifact-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.artifact === artifact);
    });
    
    // Update panels
    document.querySelectorAll('.artifact-panel').forEach(panel => {
        panel.classList.toggle('hidden', !panel.id.includes(artifact));
    });
}

// ============================================================
// RENDERING HELPERS
// ============================================================

/**
 * Render fit analysis with nice formatting.
 */
function renderFitAnalysis(analysis) {
    const score = analysis.overall_fit_score || 0;
    const scoreClass = score >= 70 ? 'score-high' : score >= 40 ? 'score-medium' : 'score-low';
    
    return `
        <div class="fit-score">
            <div class="fit-score-circle ${scoreClass}">${score}%</div>
            <div>
                <strong>Overall Fit Score</strong>
                <p>${analysis.summary || 'Analysis complete'}</p>
            </div>
        </div>
        
        <div class="fit-section">
            <h4>✅ Requirements Met</h4>
            <ul class="fit-list">
                ${(analysis.requirements_met || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
        </div>
        
        <div class="fit-section">
            <h4>⚠️ Partial Match</h4>
            <ul class="fit-list">
                ${(analysis.requirements_partial || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
        </div>
        
        <div class="fit-section">
            <h4>❌ Requirements Not Met</h4>
            <ul class="fit-list">
                ${(analysis.requirements_not_met || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
        </div>
        
        <div class="fit-section">
            <h4>💡 Recommendations</h4>
            <ul class="fit-list">
                ${(analysis.emphasis_recommendations || []).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
        </div>
    `;
}

/**
 * Simple markdown to HTML converter.
 */
function renderMarkdown(text) {
    if (!text) return '';
    
    // Escape HTML first
    let html = escapeHtml(text);
    
    // Convert markdown
    html = html
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Lists
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        // Horizontal rules
        .replace(/^---$/gm, '<hr>')
        // Paragraphs (double newlines)
        .replace(/\n\n/g, '</p><p>')
        // Single newlines to <br> within paragraphs
        .replace(/\n/g, '<br>');
    
    // Wrap list items in <ul>
    html = html.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');
    
    // Wrap in paragraph
    html = '<p>' + html + '</p>';
    
    return html;
}

/**
 * Render resume diff view.
 */
function renderResumeDiff(original, rewritten) {
    return `
        <div class="diff-container">
            <div class="diff-panel">
                <h4>Original Resume</h4>
                <div>${renderMarkdown(original)}</div>
            </div>
            <div class="diff-panel">
                <h4>Rewritten Resume</h4>
                <div>${renderMarkdown(rewritten)}</div>
            </div>
        </div>
    `;
}

/**
 * Escape HTML special characters.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format status for display.
 */
function formatStatus(status) {
    debugger
    const map = {
        'not_yet': 'not_yet',
        'applied': 'applied',
        'interviewed': 'interviewed',
        'rejected': 'rejected'
    };
    return map[status] || status;
}

// ============================================================
// EVENT LISTENERS
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize auth component
    initAuth();
    
    // Initialize upload component
    initUpload();
    
    // Tab switching for artifacts
    document.querySelectorAll('.artifact-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            showArtifactTab(tab.dataset.artifact);
        });
    });
    
    // Status change
    document.getElementById('status-select')?.addEventListener('change', async (e) => {
        if (!AppState.currentRoleId) return;
        
        try {
            await apiRequest(`/api/applications/${AppState.currentRoleId}`, {
                method: 'PATCH',
                body: { status: e.target.value }
            });
            await loadRoles();
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    });
    
    // New application buttons
    document.getElementById('new-application-btn')?.addEventListener('click', () => {
        showPanel('new-application-panel');
    });
    
    document.getElementById('empty-new-btn')?.addEventListener('click', () => {
        showPanel('new-application-panel');
    });
    
    // Regenerate button
    document.getElementById('regenerate-btn')?.addEventListener('click', async () => {
        if (!AppState.currentRoleId || !AppState.currentArtifact) return;
        
        const draftType = {
            'fit': 'fit_analysis',
            'resume': 'resume_rewrite',
            'cover': 'cover_letter',
            'interview': 'interview_qa'
        }[AppState.currentArtifact];
        
        try {
            await apiRequest(
                `/api/applications/${AppState.currentRoleId}/regenerate/${draftType}`,
                { method: 'POST' }
            );
            await loadRoleDetails(AppState.currentRoleId);
        } catch (error) {
            console.error('Regeneration failed:', error);
            alert('Failed to regenerate: ' + error.message);
        }
    });
    
    // Check auth on load
    checkAuth();
});

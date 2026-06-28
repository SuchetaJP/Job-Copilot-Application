/**
 * components/upload.js - New application form handling
 * 
 * Manages resume upload and job description input.
 */

function initUpload() {
    // JD input tab switching
    document.querySelectorAll('.jd-input-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.jdTab;
            
            document.querySelectorAll('.jd-input-tabs .tab-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.jdTab === tab);
            });
            
            document.getElementById('jd-text').classList.toggle('hidden', tab !== 'text');
            document.getElementById('jd-url').classList.toggle('hidden', tab !== 'url');
        });
    });
    
    // Form submission
    document.getElementById('new-application-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorEl = document.getElementById('application-error');
        errorEl.textContent = '';
        
        const jobTitle = document.getElementById('job-title').value;
        const company = document.getElementById('company').value;
        const resumeFile = document.getElementById('resume-file').files[0];
        const jdText = document.getElementById('jd-text').value;
        const jdUrl = document.getElementById('jd-url').value;
        
        // Validation
        if (!resumeFile) {
            errorEl.textContent = 'Please select a resume PDF';
            return;
        }
        
        if (!jdText && !jdUrl) {
            errorEl.textContent = 'Please provide a job description';
            return;
        }
        
        // Show loading state
        document.getElementById('new-application-form').classList.add('hidden');
        document.getElementById('pipeline-loading').classList.remove('hidden');
        
        // Simulate step updates
        const steps = [
            'Parsing resume...',
            'Analyzing fit...',
            'Rewriting resume...',
            'Writing cover letter...',
            'Generating interview questions...',
            'Finalizing...'
        ];
        
        let stepIndex = 0;
        const stepInterval = setInterval(() => {
            stepIndex++;
            if (stepIndex < steps.length) {
                document.getElementById('loading-step').textContent = steps[stepIndex];
            }
        }, 3000);
        
        try {
            // Build form data
            const formData = new FormData();
            formData.append('resume', resumeFile);
            formData.append('job_title', jobTitle);
            formData.append('company', company);
            
            if (jdText) {
                formData.append('jd_text', jdText);
            }
            if (jdUrl) {
                formData.append('jd_url', jdUrl);
            }
            
            // Submit
            const response = await fetch(`${API_BASE_URL}/api/applications`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${AppState.token}`
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to create application');
            }
            
            // Success - reload roles and show the new one
            clearInterval(stepInterval);
            AppState.currentRoleId = data.id;
            await loadRoles();
            
            // Reset form
            document.getElementById('new-application-form').reset();
            
        } catch (error) {
            clearInterval(stepInterval);
            errorEl.textContent = error.message;
            document.getElementById('new-application-form').classList.remove('hidden');
            document.getElementById('pipeline-loading').classList.add('hidden');
        }
    });
}

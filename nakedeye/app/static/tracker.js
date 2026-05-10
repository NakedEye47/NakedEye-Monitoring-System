(function () {
    const NAKEDEYE_URL = "https://reissue-lusty-tattle.ngrok-free.dev"; // Permanent Ngrok URL

    // Attempt to load existing session from sessionStorage
    let sessionId = sessionStorage.getItem('nakedeye_session_id');

    function sendEvent(eventType, targetElement) {
        if (!sessionId) return;

        const payload = {
            session_id: sessionId,
            event_type: eventType,
            target_element: targetElement
        };

        if (navigator.sendBeacon) {
            // sendBeacon sends text/plain by default, FastAPI needs application/json
            const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
            navigator.sendBeacon(`${NAKEDEYE_URL}/api/public/analytics/event`, blob);
        } else {
            fetch(`${NAKEDEYE_URL}/api/public/analytics/event`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                keepalive: true
            }).catch(console.error);
        }
    }

    function initSession() {
        if (sessionId) {
            sendEvent('pageview', window.location.pathname);
            return;
        }

        const payload = {
            site_url: window.location.href,
            user_agent: navigator.userAgent
        };

        fetch(`${NAKEDEYE_URL}/api/public/analytics/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                if (data.session_id) {
                    sessionId = data.session_id;
                    sessionStorage.setItem('nakedeye_session_id', sessionId);
                    sendEvent('pageview', window.location.pathname);
                }
            })
            .catch(console.error);
    }

    // Listen for click events on specific targets using closest() to handle child elements
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a');
        const project = e.target.closest('.proj-thumb, .project-item, .cat-card');
        const skill = e.target.closest('.skill-card');

        // Track CV Downloads
        if (link && (link.hasAttribute('download') || link.href.includes('.pdf') || link.innerText.toLowerCase().includes('cv'))) {
            sendEvent('download', 'CV / Resume Download');
        }
        // Track Portfolio/Project Clicks
        else if (project) {
            const title = project.querySelector('.proj-thumb-title, .project-info h3, .cat-title')?.innerText || 'Project';
            sendEvent('click', 'Project: ' + title);
        }
        // Track Skills Clicks
        else if (skill) {
            const title = skill.querySelector('h3')?.innerText || 'Skill';
            sendEvent('click', 'Skill: ' + title);
        }
        // Track Contact Links
        else if (link && link.href.includes('mailto:')) {
            sendEvent('click', 'Email Link');
        }
        else if (link && link.href.includes('linkedin.com')) {
            sendEvent('click', 'LinkedIn Link');
        }
        else if (link && link.href.includes('github.com')) {
            sendEvent('click', 'GitHub Link');
        }
    });

    // Initialize the session on script load
    initSession();

    // Send a heartbeat every 30 seconds to keep session active
    setInterval(() => {
        if (sessionId) {
            sendEvent('heartbeat', null);
        }
    }, 30000);
})();

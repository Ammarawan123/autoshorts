const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const dropText = document.getElementById('dropText');

// File selection trigger
dropZone.onclick = () => fileInput.click();

fileInput.onchange = (e) => {
    if (e.target.files.length > 0) {
        dropText.innerText = `Selected: ${e.target.files[0].name}`;
    }
};

// Form submission handling
document.getElementById('uploadForm').onsubmit = async (e) => {
    e.preventDefault();
    const status = document.getElementById('status');
    const container = document.getElementById('clipsContainer');
    
    status.innerHTML = `
    <div style="margin-top:20px; text-align:center;">
        <p id="progressMsg" style="color:#a78bfa; font-size:15px;"> Starting...</p>
        <div style="background:#1a1a2e; border-radius:10px; height:22px; width:100%; margin:10px 0;">
            <div id="progressBar" style="background:#7C3AED; height:22px; border-radius:10px; width:0%; transition:width 0.6s ease;"></div>
        </div>
        <p id="progressPercent" style="color:#7C3AED; font-weight:bold;">0%</p>
    </div>
`;
// Poll progress every 2 seconds
const interval = setInterval(async () => {
    try {
        const res  = await fetch('/api/progress');
        const data = await res.json();

        document.getElementById('progressMsg').innerText   = data.status;
        document.getElementById('progressBar').style.width = data.progress + '%';
        document.getElementById('progressPercent').innerText = data.progress + '%';

        if (data.progress >= 100) {
            clearInterval(interval);
            document.getElementById('progressMsg').style.color = '#22c55e';
        }
        if (!data.success) {
            clearInterval(interval);
            document.getElementById('progressMsg').style.color = '#ef4444';
            document.getElementById('progressBar').style.background = '#ef4444';
        }
    } catch (err) {
        console.error('Progress error:', err);
    }
}, 500);
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/api/transcribe', { 
            method: 'POST', 
            body: formData 
        });
        const result = await response.json();
        
        if (response.ok) {
            clearInterval(interval);
            document.getElementById('progressMsg').innerText = 'Processing completed successfully!';
            document.getElementById('progressMsg').style.color = '#22c55e';
            document.getElementById('progressBar').style.width = '100%';
            document.getElementById('progressBar').style.background = '#22c55e';
            document.getElementById('progressPercent').style.color = '#22c55e';
            document.getElementById('progressPercent').innerText = '100%';
            document.getElementById('resultsGrid').style.display = 'block';
            
            
            container.innerHTML = ''; 
            
            
            if (result.clips && result.clips.length > 0) {
                result.clips.forEach(clip => {
                    container.innerHTML += `
                        <div class="clip-card">
                            <video src="${clip.url}" controls></video>
                            <a href="${clip.url}" download>Download</a>
                        </div>
                    `;
                });
            } else {
                container.innerHTML = "<p>No clips generated yet.</p>";
            }
        } else {
            clearInterval(interval);
            document.getElementById('progressMsg').innerText = '❌ Error: ' + (result.message || 'Something went wrong');
            document.getElementById('progressMsg').style.color = '#ef4444';
            document.getElementById('progressBar').style.background = '#ef4444';
            document.getElementById('progressPercent').style.color = '#ef4444';
}
    } catch (err) {
        clearInterval(interval);
        document.getElementById('progressMsg').innerText = '❌ Server error. Please try again.';
        document.getElementById('progressMsg').style.color = '#ef4444';
        console.error(err);
    }
};

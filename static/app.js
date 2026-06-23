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
    
    status.innerText = "🚀 Pipeline running... Please wait.";
    status.style.color = "white";
    
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('/api/transcribe', { 
            method: 'POST', 
            body: formData 
        });
        const result = await response.json();
        
        if (response.ok) {
            status.innerText = "✅ Success! Clips are ready.";
            document.getElementById('resultsGrid').style.display = 'block';
            
            // Clips ko grid mein display karna
            container.innerHTML = ''; // Purane results saaf karna
            
            // Note: Agar aapka backend 'result.clips' array bhej raha hai
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
            status.innerText = "❌ Error: " + (result.error || "Something went wrong");
            status.style.color = "#ff4d4d";
        }
    } catch (err) {
        status.innerText = "❌ Server error. Please try again.";
        status.style.color = "#ff4d4d";
        console.error(err);
    }
};
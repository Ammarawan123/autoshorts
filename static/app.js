const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const dropText = document.getElementById("dropText");
const uploadForm = document.getElementById("uploadForm");

// Open file browser
dropZone.onclick = () => fileInput.click();

// Show selected filename
fileInput.onchange = (e) => {
    if (e.target.files.length > 0) {
        dropText.innerText = "Selected: " + e.target.files[0].name;
    }
};

// Reset UI
function resetUploader() {

    fileInput.value = "";

    dropText.innerHTML =
        'Drag & Drop video or <span>browse</span>';

    document.getElementById("status").innerHTML = "";

    document.getElementById("resultsGrid").style.display = "none";

    document.getElementById("clipsContainer").innerHTML = "";
}

// Upload
uploadForm.onsubmit = async (e) => {

    e.preventDefault();

    const status = document.getElementById("status");
    const container = document.getElementById("clipsContainer");

    status.innerHTML = `
    <div style="margin-top:20px;text-align:center;">
        <p id="progressMsg" style="color:#a78bfa;">Starting...</p>

        <div style="background:#1a1a2e;height:22px;border-radius:10px;margin:10px 0;">

            <div id="progressBar"
                 style="background:#7C3AED;
                        width:0%;
                        height:22px;
                        border-radius:10px;
                        transition:.5s;"></div>

        </div>

        <p id="progressPercent">0%</p>

    </div>
    `;

    const interval = setInterval(async () => {

        try {

            const res = await fetch("/api/progress");
            const data = await res.json();

            document.getElementById("progressMsg").innerText =
                data.status;

            document.getElementById("progressBar").style.width =
                data.progress + "%";

            document.getElementById("progressPercent").innerText =
                data.progress + "%";

            if (data.progress >= 100)
                clearInterval(interval);

            if (!data.success)
                clearInterval(interval);

        } catch {}
    }, 500);

    const formData = new FormData(uploadForm);

    try {

        const response = await fetch("/api/transcribe", {

            method: "POST",
            body: formData

        });

        const result = await response.json();

        clearInterval(interval);

        if (!response.ok) {

            document.getElementById("progressMsg").innerHTML =
                "❌ " + result.message;

            document.getElementById("progressMsg").style.color = "red";

            return;
        }

        document.getElementById("progressBar").style.width = "100%";
        document.getElementById("progressPercent").innerText = "100%";
        document.getElementById("progressMsg").innerHTML =
            "✅ Processing Completed";

        document.getElementById("resultsGrid").style.display = "block";

        container.innerHTML = "";

        result.clips.forEach((clip) => {

            container.innerHTML += `

            <div class="clip-card">

                <video controls src="${clip.url}"></video>

                <br><br>

                <a href="${clip.url}" download>
                    Download
                </a>

            </div>

            `;
        });

        // Add Generate Another Video button

        container.innerHTML += `

        <div style="grid-column:1/-1;text-align:center;margin-top:25px;">

            <button id="newVideoBtn">

                Generate Another Video

            </button>

        </div>

        `;

        document
            .getElementById("newVideoBtn")
            .addEventListener("click", () => {

                resetUploader();

            });

    } catch (err) {

        clearInterval(interval);

        document.getElementById("progressMsg").innerHTML =
            "❌ Server Error";

        document.getElementById("progressMsg").style.color = "red";

        console.log(err);
    }
};
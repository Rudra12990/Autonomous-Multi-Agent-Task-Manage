async function runPipeline() {
    const rawText = document.getElementById("logInput").value.trim();
    const consoleBox = document.getElementById("statusConsole");
    const resultMatrix = document.getElementById("resultMatrix");
    
    if (!rawText) {
        alert("Please enter logs before processing.");
        return;
    }

    resultMatrix.classList.add("hidden");
    consoleBox.style.color = "#00ffcc";
    consoleBox.innerHTML = "> Establishing network handshake with FastAPI Gateway...";

    try {
        const response = await fetch("/api/v1/agent/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ raw_text: rawText })
        });

        if (response.status !== 202) throw new Error(`Gateway Error: Status ${response.status}`);

        const data = await response.json();
        consoleBox.innerHTML = `> Ticket logged: [JOB_ID: ${data.job_id.substring(0,8)}].<br>> Initializing workforce routing...`;

        setTimeout(() => checkPipelineStatus(data.job_id, 1), 1500);
    } catch (error) {
        consoleBox.style.color = "#ef4444";
        consoleBox.innerHTML = `> Server Error: ${error.message}`;
    }
}

async function checkPipelineStatus(jobId, step) {
    const consoleBox = document.getElementById("statusConsole");
    
    if (step === 1) {
        consoleBox.innerHTML = `> [AGENT // DOMAIN_RESEARCHER]: Extracting metrics into core object schemas...`;
        setTimeout(() => checkPipelineStatus(jobId, 2), 1500);
        return;
    }
    if (step === 2) {
        consoleBox.innerHTML = `> [AGENT // COMPLIANCE_CRITIC]: Running self-healing format safety audits...`;
        setTimeout(() => checkPipelineStatus(jobId, 3), 1200);
        return;
    }

    try {
        const res = await fetch(`/api/v1/agent/status/${jobId}`);
        const data = await res.json();
        const finalOutput = data.final_output || "";

        if (finalOutput.includes("RESOURCE_EXHAUSTED") || finalOutput.includes("429")) {
            consoleBox.style.color = "#fbbf24";
            consoleBox.innerHTML = `> [LIMIT ERROR]: Gemini API request limits hit. System pipeline frozen. Please wait 40 seconds before retrying.`;
            return;
        }

        consoleBox.innerHTML = `> Consensus complete. Log written securely to Supabase ledger.`;
        
        document.getElementById("researchOutput").innerText = JSON.stringify(data.research_output, null, 2);
        document.getElementById("complianceOutput").innerText = JSON.stringify(data.critic_feedback, null, 2);
        document.getElementById("ledgerOutput").innerText = typeof finalOutput === 'object' ? JSON.stringify(finalOutput, null, 2) : finalOutput;
        
        document.getElementById("resultMatrix").classList.remove("hidden");
    } catch (err) {
        consoleBox.style.color = "#ef4444";
        consoleBox.innerHTML = `> State Exception: ${err.message}`;
    }
}

function switchTab(evt, tabId) {
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.getElementById(tabId).classList.add("active");
    evt.currentTarget.classList.add("active");
}

/* Toggle Class Token State */
function toggleGlobalTheme() {
    document.body.classList.toggle("light-theme");
}

/* Typing Screen Shake Event Listener Binding */
window.addEventListener("DOMContentLoaded", () => {
    const textIngestionArea = document.getElementById("logInput");

    if (textIngestionArea) {
        textIngestionArea.addEventListener("input", () => {
            textIngestionArea.classList.remove("jiggle-active");
            void textIngestionArea.offsetWidth; // Repaint trigger
            textIngestionArea.classList.add("jiggle-active");
            
            setTimeout(() => {
                textIngestionArea.classList.remove("jiggle-active");
            }, 80);
        });
    }
});
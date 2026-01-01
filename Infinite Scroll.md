### **The "Infinite Scroll" Harvester**

#### **Instructions:**

1. Open **Google Chrome** (or Edge/Brave) on your computer.
    
2. Log in to Instagram and navigate to your **Reels tab**: `instagram.com/your_username/reels/`
    
3. Right-click anywhere on the page and select **Inspect** (or press `F12`).
    
4. Click the **Console** tab.
    
5. **Paste the code below** and press **Enter**.
    

#### **The Script:**

JavaScript

```
(async function instagramReelHarvester() {
    console.clear();
    console.log("%c Starting Reel Harvester... ", "background: #222; color: #bada55; font-size: 16px;");

    // --- CONFIGURATION ---
    const SCROLL_DELAY = 2500; // Time in ms to wait between scrolls (slower = safer)
    const MAX_RETRIES = 5;     // Stop if no new content loads after this many tries
    
    // --- UI SETUP ---
    // Create a floating status box so you see what's happening
    const statusBox = document.createElement('div');
    statusBox.style.cssText = `
        position: fixed; top: 10px; right: 10px; z-index: 9999;
        background: black; color: white; padding: 15px;
        border-radius: 8px; font-family: monospace; border: 2px solid #00ff00;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    `;
    document.body.appendChild(statusBox);

    const updateStatus = (count, status) => {
        statusBox.innerHTML = `
            <strong>📸 Reel Harvester</strong><br>
            ------------------<br>
            Collected: <span style="color: #00ff00; font-size: 1.2em;">${count}</span><br>
            Status: ${status}<br>
            <br>
            <button id="stopBtn" style="background: red; color: white; border: none; padding: 5px; cursor: pointer;">STOP & SAVE</button>
        `;
        document.getElementById('stopBtn').onclick = finishAndSave;
    };

    // --- LOGIC ---
    let collectedLinks = new Set();
    let retries = 0;
    let keepRunning = true;

    function getReelLinks() {
        // Find all anchor tags containing "/reel/"
        const anchors = Array.from(document.querySelectorAll('a[href*="/reel/"]'));
        let newCount = 0;
        anchors.forEach(a => {
            // Clean the link (remove query params like ?igsh=...)
            const cleanLink = a.href.split('?')[0];
            if (!collectedLinks.has(cleanLink)) {
                collectedLinks.add(cleanLink);
                newCount++;
            }
        });
        return newCount;
    }

    async function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function downloadTxt() {
        const data = Array.from(collectedLinks).join('\n');
        const blob = new Blob([data], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `instagram_reels_links_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    async function finishAndSave() {
        keepRunning = false;
        updateStatus(collectedLinks.size, "Stopped. Downloading...");
        downloadTxt();
        console.log("%c Download Started! ", "background: #222; color: #00ff00; font-size: 16px;");
    }

    // --- MAIN LOOP ---
    let lastHeight = document.body.scrollHeight;
    
    while (keepRunning) {
        let newLinksFound = getReelLinks();
        window.scrollTo(0, document.body.scrollHeight);
        
        updateStatus(collectedLinks.size, "Scrolling & Scanning...");
        
        // Randomize sleep slightly to look human
        await sleep(SCROLL_DELAY + Math.random() * 1000);

        let newHeight = document.body.scrollHeight;
        
        if (newHeight === lastHeight) {
            // We haven't moved. Might be end of page or loading lag.
            retries++;
            updateStatus(collectedLinks.size, `Waiting for load... (${retries}/${MAX_RETRIES})`);
            if (retries >= MAX_RETRIES) {
                updateStatus(collectedLinks.size, "End of page reached.");
                break; 
            }
        } else {
            retries = 0; // Reset retries if we moved
            lastHeight = newHeight;
        }
    }

    if (keepRunning) finishAndSave(); // Save automatically if loop ends naturally

})();
```

### **Why this code is "Stable":**

1. **Duplicate Protection (`Set`):** Instagram "recycles" the view (DOM). As you scroll down, top elements disappear to save memory. A simple scrape at the end would miss the top ones. This script collects _while_ it scrolls and ignores duplicates.
    
2. **Human Timing:** It has a `SCROLL_DELAY` (2.5 seconds). If you scroll too fast (like 0.5s), Instagram will soft-block your scrolling and the spinner will just spin forever.
    
3. **Floating UI:** I added a black box in the top right corner so you can see the counter go up.
    
4. **Emergency Stop:** You can click the red "STOP & SAVE" button in the floating box at any time to download what you have found so far.
    

**Once you have the `.txt` file**, you can upload that file to your Google Drive, and we can revisit the Python script to download from that list, or you can use a download manager.


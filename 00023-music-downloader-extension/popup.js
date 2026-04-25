const songListDiv = document.getElementById("songList");
const refreshBtn = document.getElementById("refreshBtn");
const aboutBtn = document.getElementById("aboutBtn");
const sitesBtn = document.getElementById("sitesBtn");
const listView = document.getElementById("listView");
const aboutView = document.getElementById("aboutView");
const sitesView = document.getElementById("sitesView");
const sitesListDiv = document.getElementById("sitesList");

const activeDownloads = new Map();

// --- Navigation ---
function showView(viewName) {
  listView.classList.add("hidden");
  aboutView.classList.add("hidden");
  sitesView.classList.add("hidden");
  if (viewName === "list") listView.classList.remove("hidden");
  else if (viewName === "about") aboutView.classList.remove("hidden");
  else if (viewName === "sites") sitesView.classList.remove("hidden");
}

aboutBtn.addEventListener("click", () => showView("about"));
sitesBtn.addEventListener("click", () => {
  showView("sites");
  loadSupportedSites();
});
document
  .getElementById("backToListFromAbout")
  .addEventListener("click", () => showView("list"));
document
  .getElementById("backToListFromSites")
  .addEventListener("click", () => showView("list"));

// --- Progress updates from background ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (
    message.type === "downloadProgress" &&
    activeDownloads.has(message.downloadId)
  ) {
    const { button, originalText } = activeDownloads.get(message.downloadId);
    if (button) {
      button.textContent = `${originalText} ${message.percent}%`;
      if (message.percent >= 100) {
        button.textContent = "Done";
        setTimeout(() => {
          if (button.parentNode) button.remove();
        }, 1500);
        activeDownloads.delete(message.downloadId);
      }
    }
  }
});

// --- Check if current tab is supported (using background) ---
async function isSupportedSite() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) return false;
  const response = await chrome.runtime.sendMessage({
    type: "isSupportedSite",
    url: tab.url,
  });
  return response && response.supported;
}

// --- Load supported sites list ---
async function loadSupportedSites() {
  try {
    const sites = await chrome.runtime.sendMessage({
      type: "getSupportedSites",
    });
    if (!sites || sites.length === 0) {
      sitesListDiv.innerHTML = '<div class="empty">No sites configured</div>';
      return;
    }
    const ul = document.createElement("ul");
    ul.className = "site-list";
    sites.forEach((site) => {
      const li = document.createElement("li");
      let patternStr = site.urlPattern;
      if (typeof patternStr !== "string") {
        patternStr = patternStr.toString();
      }
      // Clean the regex to show only the domain part (remove slashes and unescape)
      let cleanPattern = patternStr;
      // Remove leading and trailing slashes
      cleanPattern = cleanPattern.replace(/^\//, "").replace(/\/$/, "");
      // Replace escaped dots with actual dots
      cleanPattern = cleanPattern.replace(/\\\./g, ".");
      // Optionally remove any other regex special chars if needed (keep as is)
      li.innerHTML = `<strong>${site.name}</strong><br><code>${cleanPattern}</code>`;
      ul.appendChild(li);
    });
    sitesListDiv.innerHTML = "";
    sitesListDiv.appendChild(ul);
  } catch (err) {
    console.error("[Music Downloader] Error loading sites:", err);
    sitesListDiv.innerHTML = '<div class="empty">Error loading sites</div>';
  }
}

// --- Load main song list (same as before, but with site prefix) ---
async function loadSongs() {
  const supported = await isSupportedSite();
  if (!supported) {
    songListDiv.innerHTML = `
      <div class="empty">
        This extension works only on supported music sites.<br>
        Please open a supported site to see saved songs.
      </div>
    `;
    return;
  }

  songListDiv.innerHTML = '<div class="empty">Loading...</div>';
  try {
    const response = await chrome.runtime.sendMessage({
      type: "getCachedSongs",
    });
    const songs = response.songs;
    if (!songs || songs.length === 0) {
      songListDiv.innerHTML =
        '<div class="empty">No songs captured yet.<br>Play something on a supported site.</div>';
      return;
    }
    songListDiv.innerHTML = "";
    songs.forEach((song, idx) => {
      const songDiv = document.createElement("div");
      songDiv.className = "song-item";

      const headerDiv = document.createElement("div");
      headerDiv.className = "song-header";
      const thumbImg = document.createElement("img");
      thumbImg.className = "song-thumb";
      thumbImg.src = song.thumbnail || "";
      thumbImg.alt = "cover";
      thumbImg.onerror = () => {
        thumbImg.style.display = "none";
      };
      const titleSpan = document.createElement("div");
      titleSpan.className = "song-title";
      titleSpan.textContent = `[${song.siteId}] ${song.title}`;
      headerDiv.appendChild(thumbImg);
      headerDiv.appendChild(titleSpan);
      songDiv.appendChild(headerDiv);

      const buttonsDiv = document.createElement("div");
      buttonsDiv.className = "download-buttons";

      song.cdns.forEach((cdnObj, cdnIdx) => {
        const btnContainer = document.createElement("span");
        const downloadBtn = document.createElement("button");
        downloadBtn.textContent = `${cdnObj.cdn}-cdn download`;
        downloadBtn.className = "download-btn";
        const uniqueId = `${song.siteId}_${song.title}_${cdnObj.cdn}_${Date.now()}_${cdnIdx}`;
        downloadBtn.dataset.id = uniqueId;
        const copyBtn = document.createElement("button");
        copyBtn.textContent = "Copy";
        copyBtn.className = "copy-btn";
        copyBtn.title = `Copy "${song.title}.mp3" to clipboard`;

        downloadBtn.addEventListener("click", async (e) => {
          if (downloadBtn.disabled) return;
          const url = cdnObj.downloadUrl;
          const title = song.title;
          activeDownloads.set(uniqueId, {
            button: downloadBtn,
            originalText: downloadBtn.textContent,
          });
          downloadBtn.disabled = true;
          downloadBtn.textContent = "0%";
          try {
            const response = await chrome.runtime.sendMessage({
              type: "downloadSong",
              downloadUrl: url,
              fileName: title,
              downloadId: uniqueId,
            });
            if (!response.success) {
              downloadBtn.textContent = "Failed";
              setTimeout(() => {
                if (downloadBtn.parentNode) downloadBtn.remove();
              }, 2000);
              activeDownloads.delete(uniqueId);
            }
          } catch (err) {
            console.error(err);
            downloadBtn.textContent = "Error";
            setTimeout(() => {
              if (downloadBtn.parentNode) downloadBtn.remove();
            }, 2000);
            activeDownloads.delete(uniqueId);
          }
        });

        copyBtn.addEventListener("click", () => {
          const textToCopy = `${song.title}.mp3`;
          navigator.clipboard
            .writeText(textToCopy)
            .then(() => {
              copyBtn.textContent = "Copied!";
              setTimeout(() => {
                copyBtn.textContent = "Copy";
              }, 1500);
            })
            .catch((err) => {
              console.error("Copy failed:", err);
              copyBtn.textContent = "Error";
              setTimeout(() => {
                copyBtn.textContent = "Copy";
              }, 1500);
            });
        });

        btnContainer.appendChild(downloadBtn);
        btnContainer.appendChild(copyBtn);
        buttonsDiv.appendChild(btnContainer);
      });

      songDiv.appendChild(buttonsDiv);
      songListDiv.appendChild(songDiv);
    });
  } catch (err) {
    console.error(err);
    songListDiv.innerHTML = '<div class="empty">Error loading songs</div>';
  }
}

refreshBtn.addEventListener("click", () => {
  loadSongs();
});
loadSongs();

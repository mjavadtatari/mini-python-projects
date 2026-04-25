importScripts("sites-config.js");

let cachedSongs = []; // each item: { siteId, title, thumbnail, trackId, cdns: [{cdn, downloadUrl}], timestamp }

// Helper: extract CDN and track ID (generic based on URL structure)
function parseUrlInfo(url, siteConfig) {
  // Default CDN extraction: first subdomain before .melodify.pw (adaptable)
  const cdnMatch = url.match(/\/\/([^.]+)\./);
  const cdn = cdnMatch ? cdnMatch[1] : "unknown";
  // Extract a unique track ID from the URL – use the part after /track/ up to next slash
  const trackIdMatch = url.match(/\/track\/([a-f0-9]+)\//);
  const trackId = trackIdMatch ? trackIdMatch[1] : url; // fallback to whole url
  return { cdn, trackId };
}

// Load from storage
chrome.storage.local.get(["cachedSongs"], (result) => {
  if (result.cachedSongs) {
    cachedSongs = result.cachedSongs;
    // If old structure migration needed (detect by missing cdns array)
    if (cachedSongs.length > 0 && !cachedSongs[0].cdns) {
      console.log("[Appu Music Downloader] Migrating old data...");
      const mergedMap = new Map();
      for (const old of result.cachedSongs) {
        // Find site config – assume melodify if not present
        const site = SITES.find((s) => s.id === old.siteId) || SITES[0];
        const { cdn, trackId } = parseUrlInfo(old.downloadUrl, site);
        const key = `${old.siteId}|${old.title}|${trackId}`;
        if (!mergedMap.has(key)) {
          mergedMap.set(key, {
            siteId: old.siteId,
            title: old.title,
            thumbnail: old.thumbnail,
            trackId: trackId,
            cdns: [],
            timestamp: old.timestamp,
          });
        }
        const entry = mergedMap.get(key);
        if (!entry.cdns.find((c) => c.cdn === cdn)) {
          entry.cdns.push({ cdn, downloadUrl: old.downloadUrl });
        }
      }
      cachedSongs = Array.from(mergedMap.values());
      saveToStorage();
    }
  }
  updateBadge();
});

function updateBadge() {
  const count = cachedSongs.length;
  if (count > 0) {
    chrome.action.setBadgeText({ text: count.toString() });
    chrome.action.setBadgeBackgroundColor({ color: "#0d652d" });
  } else {
    chrome.action.setBadgeText({ text: "" });
  }
}

function saveToStorage() {
  chrome.storage.local.set({ cachedSongs });
  updateBadge();
}

// Current playing data (per site – but only one site active at a time)
let currentSongData = { siteId: null, title: "Unknown", thumbnail: null };

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "songData") {
    currentSongData = {
      siteId: message.siteId,
      title: message.title,
      thumbnail: message.thumbnail,
    };
  }
});

// Intercept network requests using declarative approach – but we need to know site config for each URL
// We'll listen to all requests and match against each site's pattern
chrome.webRequest.onCompleted.addListener(
  (details) => {
    const url = details.url;
    // Find which site this URL belongs to
    const site = SITES.find(
      (s) => s.streamUrlPattern && s.streamUrlPattern.test(url),
    );
    if (!site) return;
    if (!url.includes("track_demo.mp3") && !site.streamUrlPattern.test(url))
      return; // ensure it's the demo pattern

    // Use site's transform function to get the high quality URL
    const downloadUrl = site.transformDemoTo320
      ? site.transformDemoTo320(url)
      : url;

    const { cdn, trackId } = parseUrlInfo(downloadUrl, site);
    if (!trackId || currentSongData.title === "Unknown") return;

    const key = `${site.id}|${currentSongData.title}|${trackId}`;
    const existingSong = cachedSongs.find(
      (s) => `${s.siteId}|${s.title}|${s.trackId}` === key,
    );
    if (existingSong) {
      if (!existingSong.cdns.some((c) => c.cdn === cdn)) {
        existingSong.cdns.push({ cdn, downloadUrl });
        existingSong.timestamp = Date.now();
        saveToStorage();
      }
    } else {
      cachedSongs.unshift({
        siteId: site.id,
        title: currentSongData.title,
        thumbnail: currentSongData.thumbnail,
        trackId: trackId,
        cdns: [{ cdn, downloadUrl }],
        timestamp: Date.now(),
      });
      if (cachedSongs.length > 50) cachedSongs.pop();
      saveToStorage();
    }
  },
  { urls: ["<all_urls>"] }, // We'll filter inside
);

// Download with progress (same as before, unchanged)
function downloadWithProgress(downloadUrl, desiredFileName, downloadId) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", downloadUrl, true);
    xhr.responseType = "blob";
    xhr.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        chrome.runtime
          .sendMessage({
            type: "downloadProgress",
            downloadId: downloadId,
            percent: percent,
          })
          .catch(() => {});
      }
    };
    xhr.onload = () => {
      if (xhr.status === 200) {
        const blob = xhr.response;
        const blobUrl = URL.createObjectURL(blob);
        chrome.downloads.download(
          {
            url: blobUrl,
            filename: `${desiredFileName}.mp3`,
            saveAs: false,
          },
          (downloadId) => {
            URL.revokeObjectURL(blobUrl);
            if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
            else resolve({ success: true, method: "blob" });
          },
        );
      } else {
        reject(new Error(`HTTP ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send();
  });
}

function fallbackDownload(downloadUrl, desiredFileName) {
  return new Promise((resolve) => {
    chrome.downloads.download(
      {
        url: downloadUrl,
        filename: `track_320.mp3`,
        saveAs: true,
      },
      (downloadId) => {
        if (chrome.runtime.lastError) {
          resolve({ success: false, error: chrome.runtime.lastError.message });
        } else {
          chrome.notifications
            ?.create?.({
              type: "basic",
              iconUrl: "icon128.png",
              title: "Appu Music Downloader",
              message: `Please rename the file to: ${desiredFileName}.mp3`,
            })
            .catch(() => {});
          resolve({
            success: true,
            method: "saveAs",
            suggestedName: desiredFileName,
          });
        }
      },
    );
  });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "isSupportedSite") {
    const url = message.url;
    let isSupported = false;
    for (const site of SITES) {
      if (site.urlPattern.test(url)) {
        isSupported = true;
        break;
      }
    }
    sendResponse({ supported: isSupported });
    return true;
  }

  if (message.type === "getSupportedSites") {
    const sites = SITES.map((site) => ({
      name: site.name,
      urlPattern: site.urlPattern.toString(),
    }));
    sendResponse(sites);
    return true;
  }

  if (message.type === "downloadSong") {
    const { downloadUrl, fileName, downloadId } = message;
    downloadWithProgress(downloadUrl, fileName, downloadId)
      .then((result) => sendResponse(result))
      .catch(async (error) => {
        console.warn(`Blob download failed: ${error.message}, using fallback`);
        const fallbackResult = await fallbackDownload(downloadUrl, fileName);
        sendResponse(fallbackResult);
      });
    return true;
  }
  if (message.type === "getCachedSongs") {
    sendResponse({ songs: cachedSongs });
    return true;
  }
});

(function () {
  // Find which site config matches current URL
  let currentConfig = null;
  for (const site of SITES) {
    if (site.urlPattern.test(window.location.href)) {
      currentConfig = site;
      break;
    }
  }
  if (!currentConfig) {
    console.log("[Appu Music Downloader] This site is not supported");
    return;
  }

  // Helper: XPath query - returns DOM node or attribute value
  function getByXPath(xpath, returnAttribute = false) {
    const result = document.evaluate(
      xpath,
      document,
      null,
      XPathResult.FIRST_ORDERED_NODE_TYPE,
      null,
    );
    const node = result.singleNodeValue;
    if (!node) return null;
    if (returnAttribute) {
      return node.nodeValue || null;
    }
    return node;
  }

  function getSongTitle() {
    const node = getByXPath(currentConfig.selectors.title);
    return node ? node.textContent.trim() : null;
  }

  function getThumbnailSrc() {
    const thumbXPath = currentConfig.selectors.thumbnail;
    if (!thumbXPath) return null;
    if (thumbXPath.includes("/@")) {
      return getByXPath(thumbXPath, true);
    } else {
      const img = getByXPath(thumbXPath);
      if (img && img.tagName === "IMG") {
        return img.src;
      } else if (img) {
        return null;
      }
      return null;
    }
  }

  let lastTitle = null;
  let lastThumb = null;
  let active = true; // flag to stop all operations

  function isContextValid() {
    try {
      return !!(chrome && chrome.runtime && chrome.runtime.id);
    } catch (e) {
      return false;
    }
  }

  function safeSendMessage(data) {
    if (!active) return false;
    if (!isContextValid()) {
      active = false;
      console.log("[Appu Music Downloader] Extension context lost – stopping");
      return false;
    }
    try {
      chrome.runtime.sendMessage(data);
      return true;
    } catch (err) {
      active = false;
      console.debug("[Appu Music Downloader] sendMessage failed, stopping");
      return false;
    }
  }

  function checkAndSendData() {
    if (!active) return;
    if (!isContextValid()) {
      active = false;
      return;
    }
    const title = getSongTitle();
    const thumb = getThumbnailSrc();
    if (title && (title !== lastTitle || thumb !== lastThumb)) {
      lastTitle = title;
      lastThumb = thumb;
      safeSendMessage({
        type: "songData",
        siteId: currentConfig.id,
        title: title,
        thumbnail: thumb,
      });
    }
  }

  // Initial check
  setTimeout(() => {
    if (active && isContextValid()) checkAndSendData();
  }, 1000);

  // Observer
  const observer = new MutationObserver(() => {
    if (active && isContextValid()) checkAndSendData();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  // Interval
  const interval = setInterval(() => {
    if (!active || !isContextValid()) {
      clearInterval(interval);
      observer.disconnect();
    } else {
      checkAndSendData();
    }
  }, 2000);
})();

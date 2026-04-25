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
      // For attribute XPaths like '/.../@src', node is the attribute node
      return node.nodeValue || null;
    }
    return node; // return the DOM node
  }

  function getSongTitle() {
    const node = getByXPath(currentConfig.selectors.title);
    return node ? node.textContent.trim() : null;
  }

  function getThumbnailSrc() {
    const thumbXPath = currentConfig.selectors.thumbnail;
    if (!thumbXPath) return null;
    // If XPath points to an attribute (contains '/@')
    if (thumbXPath.includes("/@")) {
      return getByXPath(thumbXPath, true);
    } else {
      const img = getByXPath(thumbXPath);
      if (img && img.tagName === "IMG") {
        return img.src;
      } else if (img) {
        console.warn(
          "[Appu Music Downloader] Thumbnail XPath did not return an IMG element",
          img,
        );
        return null;
      }
      return null;
    }
  }

  let lastTitle = null;
  let lastThumb = null;

  function checkAndSendData() {
    const title = getSongTitle();
    const thumb = getThumbnailSrc();
    if (title && (title !== lastTitle || thumb !== lastThumb)) {
      lastTitle = title;
      lastThumb = thumb;
      console.log(
        `[Appu Music Downloader] Sending - Title: "${title}", Thumbnail: ${thumb || "none"}`,
      );
      chrome.runtime.sendMessage({
        type: "songData",
        siteId: currentConfig.id,
        title: title,
        thumbnail: thumb,
      });
    }
  }

  // Allow page to fully render
  setTimeout(checkAndSendData, 1000);
  const observer = new MutationObserver(() => checkAndSendData());
  observer.observe(document.body, { childList: true, subtree: true });
  setInterval(checkAndSendData, 2000);
})();

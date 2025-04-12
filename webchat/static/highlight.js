const HIGHLIGHT_JS_VERSION = "11.11.1";
const HIGHLIGHT_LANGUAGES_UNSUPPORTED = new Set(['dot']);

// Track loaded state and languages
const highlightState = {
  core: null,  // Will hold the highlight.js instance
  loadedLanguages: new Set(),
};

// Load highlight.js core if needed
async function highlight_ensureHighlightCore() {
  if (!highlightState.core) {
    // Load core from CDN
    await loadScript(`https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${HIGHLIGHT_JS_VERSION}/highlight.min.js`);
    highlightState.core = window.hljs;
  }
  return highlightState.core;
}

// Load a specific language module
async function highlight_loadLanguage(lang) {
  if (!highlightState.loadedLanguages.has(lang) && !HIGHLIGHT_LANGUAGES_UNSUPPORTED.has(lang) && !highlightState.core.getLanguage(lang)) {
    highlightState.loadedLanguages.add(lang);  // even on failure, and before await, to avoid repeated or concurrent attempts
    try {
      await loadScript(`https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${HIGHLIGHT_JS_VERSION}/languages/${lang}.min.js`);
    } catch (e) {
      console.warn(`Failed to load language: ${lang}`, e);
    }
  }
}

// Helper to load scripts
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Process a single code block
async function highlight_processCodeBlock(codeElement) {
  const langClass = Array.from(codeElement.classList)
    .find(cls => cls.startsWith('language-'));

  if (!langClass)
    return;

  const lang = langClass.replace('language-', '');
  if (HIGHLIGHT_LANGUAGES_UNSUPPORTED.has(lang)) {
    return;
  }
  await highlight_loadLanguage(lang);

  highlightState.core.highlightElement(codeElement);
}

// Main handler for new messages
async function highlight_code(messageElement, viewOptions) {
  const codeBlocks = messageElement.querySelectorAll('code');
  if (!codeBlocks.length) return;

  if (viewOptions.highlight) {
    await highlight_ensureHighlightCore();

    for (const block of codeBlocks) {
      if (block.classList.contains('hljs'))
        continue;
      block.dataset.originalCode = block.textContent;
      if (block.dataset.highlightedCode) {
        block.innerHTML = block.dataset.highlightedCode;
        block.classList.add('hljs');
        delete block.dataset.highlightedCode;
      } else {
        await highlight_processCodeBlock(block);
      }
    }
  } else {
    // Restore original code if highlighting is disabled
    for (const block of codeBlocks) {
      if (!block.classList.contains('hljs'))
        continue;
      if (block.dataset.originalCode) {
        block.dataset.highlightedCode = block.innerHTML;
        block.textContent = block.dataset.originalCode;
        delete block.dataset.originalCode;
        block.classList.remove('hljs');
      }
    }
  }
}

function highlight_set_stylesheet(style) {
  let styleElement = document.getElementById('highlight_styles');
  if (!styleElement) {
    styleElement = document.createElement('link');
    styleElement.id = 'highlight_styles';
    styleElement.rel = 'stylesheet';
    document.head.appendChild(styleElement);
  }
  const href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/${HIGHLIGHT_JS_VERSION}/styles/${style}.min.css`;
  if (styleElement.href !== href) {
    styleElement.href = href;
  }
}

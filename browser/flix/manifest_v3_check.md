The existing code is Manifest V3 compatible. Key recommendations for planned features:

*   **Add `host_permissions`** to the manifest for each streaming service you plan to support (e.g., `"https://*.netflix.com/*"`).
*   **Add the `scripting` permission** to the manifest when automating page interactions.
*   **Use `chrome.storage.local`** (or `sync`) for storing state (e.g., rotation schedules).
*   **Implement automation via content scripts** injected with `chrome.scripting.executeScript()`.
*   **Consider testing on Firefox** and adding `strict_min_version` to the manifest for Firefox compatibility.

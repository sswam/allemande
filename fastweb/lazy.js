(function() {
    // Configuration
    const config = {
        rootMargin: '200px 0px',
        threshold: 0.01
    };

    // Placeholder image (1x1 white pixel)
    const PLACEHOLDER = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

    // Helper function to check if the browser supports Intersection Observer
    function supportsIntersectionObserver() {
        return 'IntersectionObserver' in window;
    }

    // Function to load the image
    function loadImage(image) {
        const src = image.dataset.src;
        if (!src) return;

        image.src = src;
        image.removeAttribute('data-src');
    }

    // Set up Intersection Observer
    let observer;
    if (supportsIntersectionObserver()) {
        observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    loadImage(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, config);
    }

    // Function to prepare images for lazy loading
    function prepareLazyImage(img) {
        if (!img.dataset.src) {
            img.dataset.src = img.src;
        }
        img.src = PLACEHOLDER;

        if (observer) {
            observer.observe(img);
        } else {
            // Fallback for browsers that don't support Intersection Observer
            loadImage(img);
        }
    }

    // Function to handle newly added images
    function handleNewImages(mutationsList) {
        for (let mutation of mutationsList) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.tagName.toLowerCase() === 'img') {
                            prepareLazyImage(node);
                        } else {
                            node.querySelectorAll('img').forEach(prepareLazyImage);
                        }
                    }
                });
            }
        }
    }

    // Set up MutationObserver to watch for new images
    const mutationObserver = new MutationObserver(handleNewImages);

    // Function to initialize lazy loading
    function initLazyLoading() {
        // Prepare existing images
        document.querySelectorAll('img').forEach(prepareLazyImage);

        // Watch for new images
        mutationObserver.observe(document.body, { childList: true, subtree: true });
    }

    // Run initialization when the DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLazyLoading);
    } else {
        initLazyLoading();
    }
})();

// Certainly! I'll provide you with a comprehensive implementation of lazy loading for images based on your requirements. This script will run before the body loads, watch for new images, and use the Intersection Observer API to load images as they come into view.
//
// Here's the full implementation:

// This script does the following:
//
// 1. It runs in an IIFE (Immediately Invoked Function Expression) to avoid polluting the global scope.
//
// 2. It defines a configuration object for the Intersection Observer, which you can adjust as needed.
//
// 3. It uses a data URL for a 1x1 white pixel as a placeholder image.
//
// 4. It checks for Intersection Observer support and falls back to loading all images immediately if it's not supported.
//
// 5. The `prepareLazyImage` function sets up each image for lazy loading by storing the original `src` in `data-src` and replacing the `src` with the placeholder.
//
// 6. It uses a MutationObserver to watch for new images added to the DOM and sets them up for lazy loading as well.
//
// 7. The script initializes as soon as the DOM is ready, either on the `DOMContentLoaded` event or immediately if the DOM is already loaded.
//
// To use this script, you would include it in your HTML file before the closing `</body>` tag or in the `<head>` with a `defer` attribute:

// <script src="lazy-load.js" defer></script>

// This implementation doesn't unload images once they're loaded, as you mentioned it might not be necessary. If you do want to implement unloading, you would need to modify the Intersection Observer callback to check when images leave the viewport and replace their `src` with the placeholder again.
//
// This script should work well for most use cases, but remember to test it thoroughly in your specific application, especially if you have a large number of images or complex DOM manipulations.

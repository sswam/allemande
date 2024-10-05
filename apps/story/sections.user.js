// ==UserScript==
// @name         Sections
// @namespace    https://allemande.ai
// @version      0.1.3
// @description  Wrap content in sections and prevent page breaks
// @match        *://*/*
// @match        file:///*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Function to wrap content in a section
    function wrapInSection(heading) {
        const level = parseInt(heading.tagName.charAt(1));
        const section = document.createElement('section');
        let currentElement = heading.nextElementSibling;

        while (currentElement) {
            const tagName = currentElement.tagName.toLowerCase();
            if (tagName === 'h1' || tagName === 'h2' || tagName === 'h3' || tagName === 'h4' || tagName === 'h5' || tagName === 'h6') {
                const level2 = parseInt(tagName.charAt(1));
                if (level2 <= level) {
                    break;
                }
            }
            const nextElement = currentElement.nextElementSibling;
            section.appendChild(currentElement);
            currentElement = nextElement;
        }

        heading.parentNode.insertBefore(section, currentElement);
        section.insertBefore(heading, section.firstChild);
    }

    // Main function to process the page
    function processSections() {
        // Get all headings
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');

        headings.forEach((heading) => {
            wrapInSection(heading);
        });

        // Add CSS to prevent page breaks within sections (except the first) and paragraphs
        const style = document.createElement('style');
        style.textContent = `
            section:not(:first-child), p {
                page-break-inside: avoid;
            }
        `;
        document.head.appendChild(style);
    }

    // Run the script after a short delay to ensure the page is fully loaded
    setTimeout(processSections, 1000);
})();

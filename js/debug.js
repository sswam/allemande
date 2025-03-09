// Debug tools ---------------------------------------------------------------

function addComputedStyles(rootElement, attrName = 's', recursive = false) {
    function getNonDefaultStyles(element) {
        // Create a fresh element of the same type
        const dummy = document.createElement(element.tagName);
        document.body.appendChild(dummy);
        dummy.className = element.className; // Include classes for fair comparison

        const defaultStyles = getComputedStyle(dummy);
        const elementStyles = getComputedStyle(element);
        const nonDefaults = [];

        for (let prop of elementStyles) {
            const computedValue = elementStyles.getPropertyValue(prop);
            const defaultValue = defaultStyles.getPropertyValue(prop);

            if (computedValue !== defaultValue) {
                nonDefaults.push(`${prop}: ${computedValue}`);
            }
        }

        document.body.removeChild(dummy);
        return nonDefaults;
    }

    function processElement(element) {
        const nonDefaults = getNonDefaultStyles(element);
        if (nonDefaults.length) {
            element.setAttribute(attrName, nonDefaults.join('; '));
        }

        if (recursive) {
            for (let child of element.children) {
                processElement(child);
            }
        }
    }

    processElement(rootElement);

    return rootElement;
}

function addMatchedStyles(rootElement, attrName = 's', recursive = false, ignoreStyles = undefined) {
    // Styles to ignore - common base styles
    if (ignoreStyles === undefined) {
        ignoreStyles = "box-sizing, font-family, color, scrollbar-color";
    } else if (ignoreStyles === null) {
        ignoreStyles = "";
    }

    const ignoreStylesSet = new Set(ignoreStyles.split(',').map(s => s.trim()));

    function cleanStyleText(style) {
        return style
            .split(';')
            .map(s => s.trim())
            .filter(s => s && !ignoreStylesSet.has(s.split(':')[0].trim()))
            .filter((s, i, arr) => arr.indexOf(s) === i) // remove duplicates
            .join('; ');
    }

    function getMatchedStyles(element) {
        const matched = new Set();

        // Iterate through all style sheets
        for (let sheet of element.ownerDocument.styleSheets) {
            // Get all rules from this stylesheet

            try {
                // Get all rules from this stylesheet
                for (let rule of sheet.cssRules || sheet.rules) {
                    if (element.matches(rule.selectorText)) {
                        matched.add(cleanStyleText(rule.style.cssText));
                    }
                }
            } catch (e) {
                // Skip inaccessible cross-origin stylesheets
                console.warn('Could not access stylesheet:', sheet.href);
                continue;
            }
        }

        // Add inline styles if any
        if (element.style.cssText) {
            matched.add(cleanStyleText(element.style.cssText));
        }

        return Array.from(matched).filter(s => s);
    }

    function processElement(element) {
        const styles = getMatchedStyles(element);
        if (styles.length) {
            element.setAttribute(attrName, styles.join('; '));
        }

        if (recursive) {
            for (let child of element.children) {
                processElement(child);
            }
        }
    }

    processElement(rootElement);

    return rootElement;
}

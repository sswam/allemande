// Gemmi's attempt at animated lightning bolts for the help button! ----------

function gemmis_lightning_bolts() {
    // Helper function to create an SVG lightning bolt
    function createGemmiLightningBolt() {
        const svgNS = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(svgNS, "svg");

        const boltWidth = rem_to_px(1.25); // Width of the SVG canvas for the bolt
        const boltHeight = rem_to_px(1.875); // Height of the SVG canvas for the bolt

        svg.setAttribute("width", boltWidth.toString());
        svg.setAttribute("height", boltHeight.toString());
        svg.setAttribute("viewBox", `0 0 ${boltWidth} ${boltHeight}`); // Defines the coordinate system for the path

        svg.style.position = "absolute"; // For positioning around the button relative to the document
        svg.style.opacity = "0.5";      // Translucent
        svg.style.pointerEvents = "none"; // So they don't interfere with clicks
        svg.style.zIndex = "9999";       // Attempt to keep them on top of other elements
        // The transform-origin is implicitly 50% 50% for rotations.

        const path = document.createElementNS(svgNS, "path");
        // A standard lightning bolt path: M(start) L(line to)... Z(close path)
        // This path starts at the top-center (10,0) and zig-zags downwards.
        path.setAttribute("d", `M${boltWidth/2} 0 L0 ${boltHeight*0.5} L${boltWidth*0.35} ${boltHeight*0.5} L${boltWidth*0.1} ${boltHeight} L${boltWidth} ${boltHeight*0.5} L${boltWidth*0.65} ${boltHeight*0.5} Z`);
        path.setAttribute("fill", "yellow");
        path.setAttribute("stroke", "gold");
        path.setAttribute("stroke-width", "1.5");

        svg.appendChild(path);
        document.body.appendChild(svg); // Append to body for absolute positioning
        return svg;
    }

    // Main logic for the animation
    const helpButton = document.querySelector("a.button#help");

    if (!helpButton) {
        console.warn("Gemmi's Lightning: Help button 'a.button#help' not found. Bolts will not appear.");
        // If I were "speaking" this warning, I'd say to Sam:
        // "I tried to find the help button using 'a.button#help', but it seems it's not there! Could you double-check the selector for me, Sam?"
        return; // Exit if button not found
    }

    const numBolts = 8;        // Number of lightning bolts
    const boltsData = [];
    const angularSpeed = 0.02; // Radians per frame (controls speed of rotation)
    let currentBaseAngle = 0;  // Shared angle for rotation, incremented each frame

    for (let i = 0; i < numBolts; i++) {
        const boltElement = createGemmiLightningBolt();
        boltsData.push({
            element: boltElement,
            // Spread bolts evenly around the circle by giving each an initial angle offset
            initialAngleOffset: (Math.PI * 2 * i) / numBolts
        });
    }

    function animateHelpButtonBolts() {
        const radius = rem_to_px(3);  // Radius of the circle in pixels from the button's center

        // Get the button's current position and size (it might move, e.g., if the layout changes)
        const buttonRect = helpButton.getBoundingClientRect();

        // Calculate the center of the button relative to the document (including scroll)
        const buttonCenterX = window.scrollX + buttonRect.left + buttonRect.width / 2;
        const buttonCenterY = window.scrollY + buttonRect.top + buttonRect.height / 2;

        currentBaseAngle += angularSpeed; // Increment angle for the next frame's rotation

        boltsData.forEach(boltData => {
            const angle = boltData.initialAngleOffset + currentBaseAngle;

            // Get SVG dimensions (needed to center the SVG on its calculated position)
            const svgWidth = parseFloat(boltData.element.getAttribute("width"));
            const svgHeight = parseFloat(boltData.element.getAttribute("height"));

            // Calculate bolt's new top-left position to center it on the circle's perimeter
            const x = buttonCenterX + radius * Math.cos(angle) - svgWidth / 2;
            const y = buttonCenterY + radius * Math.sin(angle) - svgHeight / 2;

            boltData.element.style.left = x + "px";
            boltData.element.style.top = y + "px";

            // Rotate the bolt SVG itself so its "top" (the 0,Y point of the path) points radially outwards
            // The bolt is drawn pointing "down" (positive Y in its local SVG coordinates is its main direction).
            // angle + Math.PI / 2 rotates its local "up" (-Y direction) to align with the radial line.
            boltData.element.style.transform = `rotate(${angle + Math.PI / 2}rad)`;
        });

        // Keep the animation loop going smoothly
        requestAnimationFrame(animateHelpButtonBolts);
    }

    // Start the animation
    animateHelpButtonBolts();
}

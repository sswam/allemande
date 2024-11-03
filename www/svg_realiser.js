// Select all SVG elements that don't have the svg_realised class
for (const svg of document.querySelectorAll('svg:not(.svg_realised)')) {
  // Process all use elements within the SVG
  for (const useElement of svg.querySelectorAll('use')) {
    const href = useElement.getAttribute('href') || useElement.getAttribute('xlink:href');
    const target = document.querySelector(href);
    if (target) {
      useElement.replaceWith(target.cloneNode(true));
    }
  }

  // Add the svg_realised class to mark it as processed
  svg.classList.add('svg_realised');
}

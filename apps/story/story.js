function cycleImage(img) {
    const src = img.src;
    const [basePath, extension] = src.split(/\.(?=[^.]+$)/);

    // Remove any existing numeric suffix
    const basePathWithoutSuffix = basePath.replace(/_\d+$/, '');

    // Extract current index or start at 0
    const currentIndex = parseInt((basePath.match(/_(\d+)$/) || [,'0'])[1]);

    // Try next index
    const nextIndex = currentIndex + 1;
    const nextSrc = `${basePathWithoutSuffix}_${nextIndex.toString().padStart(5, '0')}.${extension}`;

    // Create a new Image object to check if the next image exists
    const nextImg = new Image();
    nextImg.onload = function() {
        img.src = nextSrc;
    };
    nextImg.onerror = function() {
        // If next image doesn't exist, go back to the base image
        img.src = `${basePathWithoutSuffix}_00000.${extension}`;
    };
    nextImg.src = nextSrc;
}

// Add click event listener to all images
document.addEventListener('DOMContentLoaded', function() {
    const images = document.getElementsByTagName('img');
    for (let img of images) {
        img.addEventListener('click', function() {
            cycleImage(this);
        });
    }
});

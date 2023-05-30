const closeButton = document.querySelector('div[aria-label="Close"]');
if (closeButton) {
    closeButton.click();
} else {
    console.log('Close button not found');
}

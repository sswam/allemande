document.addEventListener('DOMContentLoaded', function() {
    const card = document.querySelector('.card');
    const frontSide = document.getElementById('Front');
    const backSide = document.getElementById('Back');
    const extra = document.getElementById('Extra');

    card.style.display = 'block';

    if (window.location.hash === '#Back') {
        frontSide.style.display = 'none';
        backSide.style.display = 'block';
    }

    document.addEventListener('click', function() {
        frontSide.style.display = frontSide.style.display === 'none' ? 'block' : 'none';
        backSide.style.display = backSide.style.display === 'none' ? 'block' : 'none';
        extra.style.display = 'block';
    });

    document.addEventListener('keypress', function(e) {
        if (e.key >= '1' && e.key <= '5') {
            rate(parseInt(e.key));
        } else {
            frontSide.style.display = frontSide.style.display === 'none' ? 'block' : 'none';
            backSide.style.display = backSide.style.display === 'none' ? 'block' : 'none';
            extra.style.display = 'block';
        }
    });
});

function rate(quality) {
    const cardId = document.querySelector('.card').id.split('-')[1];
    fetch('/rate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `${cardId}=${quality}`
    }).then(() => {
        window.close();
    });
}

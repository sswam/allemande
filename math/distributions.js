// distributions.js

const canvas = document.getElementById('distributionCanvas');
const ctx = canvas.getContext('2d');
const width = canvas.width;
const height = canvas.height;

// Distribution parameters
let distribution = 'normal';
let mean = 0;
let stdDev = 1;
let rate = 1;
let shape = 2;
let scale = 1;
let skew = 0;

// Function to update the graph based on current parameters
function updateGraph() {
    ctx.clearRect(0, 0, width, height);
    drawAxes();
    drawDistribution();
}

// Function to draw axes
function drawAxes() {
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.moveTo(width / 2, 0);
    ctx.lineTo(width / 2, height);
    ctx.strokeStyle = '#999';
    ctx.stroke();
}

// Function to draw the selected distribution
function drawDistribution() {
    ctx.beginPath();
    ctx.moveTo(0, height);

    for (let x = 0; x < width; x++) {
        const xValue = (x - width / 2) / 50;
        let y;

        switch (distribution) {
            case 'normal':
                y = normalDistribution(xValue, mean, stdDev);
                break;
            case 'exponential':
                y = exponentialDistribution(xValue, rate);
                break;
            case 'gamma':
                y = gammaDistribution(xValue, shape, scale);
                break;
            case 'lognormal':
                y = logNormalDistribution(xValue, mean, stdDev);
                break;
            case 'weibull':
                y = weibullDistribution(xValue, shape, scale);
                break;
            case 'chisquared':
                y = chiSquaredDistribution(xValue, shape);
                break;
            case 'skewed':
                y = skewedNormalDistribution(xValue, mean, stdDev, skew);
                break;
        }

        ctx.lineTo(x, height - y * 200);
    }

    ctx.strokeStyle = '#00F';
    ctx.stroke();
}

// Distribution functions
function normalDistribution(x, mean, stdDev) {
    return Math.exp(-0.5 * Math.pow((x - mean) / stdDev, 2)) / (stdDev * Math.sqrt(2 * Math.PI));
}

function exponentialDistribution(x, rate) {
    return x >= 0 ? rate * Math.exp(-rate * x) : 0;
}

function gammaDistribution(x, shape, scale) {
    if (x <= 0) return 0;
    return Math.pow(x, shape - 1) * Math.exp(-x / scale) / (Math.pow(scale, shape) * gamma(shape));
}

function logNormalDistribution(x, mu, sigma) {
    if (x <= 0) return 0;
    return Math.exp(-Math.pow(Math.log(x) - mu, 2) / (2 * sigma * sigma)) / (x * sigma * Math.sqrt(2 * Math.PI));
}

function weibullDistribution(x, shape, scale) {
    if (x < 0) return 0;
    return (shape / scale) * Math.pow(x / scale, shape - 1) * Math.exp(-Math.pow(x / scale, shape));
}

function chiSquaredDistribution(x, df) {
    if (x <= 0) return 0;
    return Math.pow(x, df / 2 - 1) * Math.exp(-x / 2) / (Math.pow(2, df / 2) * gamma(df / 2));
}

function skewedNormalDistribution(x, mean, stdDev, skew) {
    const normalPart = normalDistribution(x, mean, stdDev);
    const skewPart = 2 * normalDistribution((x - mean) / stdDev, 0, 1);
    return normalPart * skewPart;
}

// Helper function for gamma distribution
function gamma(z) {
    if (z < 0.5) return Math.PI / (Math.sin(Math.PI * z) * gamma(1 - z));
    z -= 1;
    let x = 0.99999999999980993;
    const p = [
        676.5203681218851, -1259.1392167224028, 771.32342877765313,
        -176.61502916214059, 12.507343278686905, -0.13857109526572012,
        9.9843695780195716e-6, 1.5056327351493116e-7
    ];
    for (let i = 0; i < 8; i++) {
        x += p[i] / (z + i + 1);
    }
    return Math.sqrt(2 * Math.PI) * Math.pow(z + 7.5, z + 0.5) * Math.exp(-(z + 7.5)) * x;
}

// Event listeners for UI controls
document.getElementById('distributionSelect').addEventListener('change', (e) => {
    distribution = e.target.value;
    updateGraph();
});

document.getElementById('meanSlider').addEventListener('input', (e) => {
    mean = parseFloat(e.target.value);
    updateGraph();
});

document.getElementById('stdDevSlider').addEventListener('input', (e) => {
    stdDev = parseFloat(e.target.value);
    updateGraph();
});

document.getElementById('rateSlider').addEventListener('input', (e) => {
    rate = parseFloat(e.target.value);
    updateGraph();
});

document.getElementById('shapeSlider').addEventListener('input', (e) => {
    shape = parseFloat(e.target.value);
    updateGraph();
});

document.getElementById('scaleSlider').addEventListener('input', (e) => {
    scale = parseFloat(e.target.value);
    updateGraph();
});

document.getElementById('skewSlider').addEventListener('input', (e) => {
    skew = parseFloat(e.target.value);
    updateGraph();
});

// Initial graph draw
updateGraph();



// This setup provides an interactive interface where users can:
//
// 1. Select different distributions from a dropdown menu.
// 2. Adjust parameters like mean, standard deviation, rate, shape, scale, and skew using sliders.
// 3. See the graph update in real-time as they change the distribution or adjust parameters.
//
// The graph is drawn on an HTML5 Canvas, and the JavaScript code handles all the calculations and drawing. The distributions included are normal, exponential, gamma, log-normal, Weibull, chi-squared, and skewed normal.
//
// To use this, save both files in the same directory and open the HTML file in a web browser. You should see the interactive distribution grapher with controls to adjust the parameters and view different distributions.


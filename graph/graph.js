const svgContainer = document.getElementById('svg-container');
const svg = document.querySelector('svg');
const commandInput = document.getElementById('command-input');

const graphData = {
    nodes: {},
    arcs: {}
};

let selectedNode = null;
let offset = { x: 0, y: 0 };

function createNode(id, x, y, text) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    node.setAttribute('class', 'node');
    node.setAttribute('id', id);
    node.setAttribute('cx', x);
    node.setAttribute('cy', y);
    node.setAttribute('r', 30);
    node.addEventListener('mousedown', startDrag);
    svg.appendChild(node);

    const textElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    textElement.setAttribute('x', x);
    textElement.setAttribute('y', y);
    textElement.setAttribute('text-anchor', 'middle');
    textElement.setAttribute('dominant-baseline', 'central');
    textElement.textContent = text;
    svg.appendChild(textElement);

    graphData.nodes[id] = { id, x, y, text, element: node, textElement };
}

function createArc(id, fromId, toId, bend = 0) {
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.id = id;
    path.setAttribute('stroke', 'black');
    path.setAttribute('fill', 'none');
    svg.appendChild(path);

    graphData.arcs[id] = { id, fromId, toId, bend };
    updateArc(id);
}

function updateArc(id) {
    const arc = graphData.arcs[id];
    const fromNode = graphData.nodes[arc.fromId];
    const toNode = graphData.nodes[arc.toId];

    const path = document.getElementById(id);
    const startX = fromNode.x;
    const startY = fromNode.y;
    const endX = toNode.x;
    const endY = toNode.y;

    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    const dx = endX - startX;
    const dy = endY - startY;
    const normalX = -dy;
    const normalY = dx;
    const length = Math.sqrt(dx * dx + dy * dy);

    const controlX = midX + arc.bend * normalX / length;
    const controlY = midY + arc.bend * normalY / length;

    path.setAttribute('d', `M${startX},${startY} Q${controlX},${controlY} ${endX},${endY}`);
}

function startDrag(e) {
    selectedNode = e.target;
    const nodeData = graphData.nodes[selectedNode.id];
    offset.x = e.clientX - nodeData.x;
    offset.y = e.clientY - nodeData.y;
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', stopDrag);
}

function drag(e) {
    if (selectedNode) {
        const x = e.clientX - offset.x;
        const y = e.clientY - offset.y;
        const nodeData = graphData.nodes[selectedNode.id];
        nodeData.x = x;
        nodeData.y = y;
        selectedNode.setAttribute('cx', x);
        selectedNode.setAttribute('cy', y);
        nodeData.textElement.setAttribute('x', x);
        nodeData.textElement.setAttribute('y', y);

        Object.keys(graphData.arcs).forEach(arcId => {
            const arc = graphData.arcs[arcId];
            if (arc.fromId === selectedNode.id || arc.toId === selectedNode.id) {
                updateArc(arcId);
            }
        });
    }
}

function stopDrag() {
    selectedNode = null;
    document.removeEventListener('mousemove', drag);
    document.removeEventListener('mouseup', stopDrag);
}

function handleCommand(command) {
    const [action, ...args] = command.split(' ');

    switch (action) {
        case 'add':
            if (args[0] === 'node') {
                const [_, id, x, y, ...text] = args;
                createNode(id, parseInt(x), parseInt(y), text.join(' '));
            } else if (args[0] === 'arc') {
                const [_, id, fromId, toId, bend] = args;
                createArc(id, fromId, toId, parseFloat(bend) || 0);
            }
            break;
        case 'delete':
            if (args[0] === 'node') {
                const nodeId = args[1];
                const nodeData = graphData.nodes[nodeId];
                if (nodeData) {
                    nodeData.element.remove();
                    nodeData.textElement.remove();
                    delete graphData.nodes[nodeId];
                    Object.keys(graphData.arcs).forEach(arcId => {
                        const arc = graphData.arcs[arcId];
                        if (arc.fromId === nodeId || arc.toId === nodeId) {
                            document.getElementById(arcId).remove();
                            delete graphData.arcs[arcId];
                        }
                    });
                }
            } else if (args[0] === 'arc') {
                const arcId = args[1];
                const arc = document.getElementById(arcId);
                if (arc) {
                    arc.remove();
                    delete graphData.arcs[arcId];
                }
            }
            break;
        default:
            console.log('Unknown command');
    }
}

commandInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        handleCommand(e.target.value);
        e.target.value = '';
    }
});

// Focus the command input on startup
window.addEventListener('load', () => {
    commandInput.focus();
});

// Bump patch version
// Version: 0.1.3

// To change the nodes from divs to SVG circles, we need to modify several parts of the code. Here's the updated `graph.js` file with the requested changes:

// Changes made:
// 1. Modified `createNode` function to create SVG circles instead of divs.
// 2. Added a separate text element for each node.
// 3. Updated the `drag` function to work with SVG elements.
// 4. Modified the `delete` command to remove both the circle and text elements.
// 5. Adjusted the `updateArc` function to use the center of the circles.
// 6. Bumped the patch version to 0.1.3 in a comment at the end of the file.
//
// These changes should make the graph use SVG circles for nodes instead of divs. The functionality should remain the same, but the visual representation and internal workings have been updated to use SVG elements consistently.
//
// Regarding the failing checks, it appears that ESLint, JSHint, and Standard.js are not properly set up in your environment. To resolve these issues:
//
// 1. For ESLint, run `npm init -y` in your project directory to create a package.json file if you haven't already, then run `npm install eslint --save-dev` and `npx eslint --init` to set up ESLint configuration.
//
// 2. For JSHint and Standard.js, you need to install them globally or as dev dependencies in your project. Run `npm install jshint standard --save-dev` to add them to your project.
//
// After setting up these tools, you should be able to run the checks without errors.


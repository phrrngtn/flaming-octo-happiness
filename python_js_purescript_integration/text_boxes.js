function getWordBoundingBoxes(element) {
    const range = document.createRange();
    const boundingBoxes = [];

    // Iterate over text nodes within the element
    const textNodes = getTextNodes(element);
    for (const textNode of textNodes) {
        const words = textNode.textContent.split(/\s+/);

        for (const word of words) {
            // Create a range for the current word
            range.setStart(textNode, 0);
            range.setEnd(textNode, word.length);

            // Get the bounding rectangle of the word
            const rect = range.getBoundingClientRect();

            boundingBoxes.push({
                word: word,
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
            });
        }
    }

    return boundingBoxes;
}

function getTextNodes(node) {
    const textNodes = [];
    if (node.nodeType === 3) {
        // If it's a text node, add it
        textNodes.push(node);
    } else {
        // Recursively traverse child nodes
        for (const child of node.childNodes) {
            textNodes.push(...getTextNodes(child));
        }
    }
    return textNodes;
}

const element = document.getElementById("content");
const wordBoundingBoxes = getWordBoundingBoxes(element);

console.log(wordBoundingBoxes); 

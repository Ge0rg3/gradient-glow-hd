// Full size viewer for shade gallery

const OPEN_CLASS = "is-open";
const tiles = [...document.querySelectorAll(".tile")];
const viewer = document.getElementById("viewer");
const picture = viewer.querySelector("img");
const caption = viewer.querySelector(".caption");
let shownIndex = -1;

// Show shade full size
function showShade(index) {
    // Wrap past either end
    shownIndex = (index + tiles.length) % tiles.length;

    // Show picture and caption
    const fileName = `${tiles[shownIndex].dataset.name}.png`;
    picture.src = fileName;
    caption.textContent = `${fileName} (${shownIndex + 1} of ${tiles.length})`;
    viewer.classList.add(OPEN_CLASS);
}

// Close viewer
function closeViewer() {
    viewer.classList.remove(OPEN_CLASS);
}

// Step or close viewer from keyboard
function handleKeydown(event) {
    // Ignore keys while closed
    if (!viewer.classList.contains(OPEN_CLASS)) {
        return;
    }

    // Close on Escape
    if (event.key === "Escape") {
        closeViewer();
    }

    // Step on arrow keys
    if (event.key === "ArrowRight") {
        showShade(shownIndex + 1);
    }
    if (event.key === "ArrowLeft") {
        showShade(shownIndex - 1);
    }
}

// Bind click and key events
tiles.forEach((tile, index) => tile.addEventListener("click", () => showShade(index)));
viewer.addEventListener("click", closeViewer);
document.addEventListener("keydown", handleKeydown);

// Open shade named in URL hash, e.g. index.html#deep-224
const linkedIndex = tiles.findIndex((tile) => tile.dataset.name === location.hash.slice(1));
if (linkedIndex >= 0) {
    showShade(linkedIndex);
}

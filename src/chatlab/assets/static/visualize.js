

const handle = document.getElementById('dragHandle');
const gridContainer = document.querySelector('.conversation-grid');
const messageColumnCells = document.querySelectorAll('.grid-col-message');

let isResizing = false;
let startX, startWidthMessages;

if (handle && gridContainer && messageColumnCells.length > 0) {

    function updateHandlePosition() {
        const firstMessageCell = messageColumnCells[0];
        if (!firstMessageCell) return;
        const messageColWidth = firstMessageCell.offsetWidth;
        let gridGap = 10;
        try {
            gridGap = parseFloat(window.getComputedStyle(gridContainer).gap.split(' ')[1] || '10');
        } catch(e) { console.warn("Could not parse grid gap, defaulting to 10px"); }

        handle.style.left = `${messageColWidth + gridGap}px`;
    }

    requestAnimationFrame(() => setTimeout(updateHandlePosition, 0));

    handle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;

        const firstMessageCell = messageColumnCells[0];
        if (!firstMessageCell) { isResizing = false; return; }
        startWidthMessages = firstMessageCell.offsetWidth;

        document.body.style.userSelect = 'none';
        document.body.style.pointerEvents = 'none';

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    });

    function handleMouseMove(e) {
        if (!isResizing) return;

        const currentX = e.clientX;
        const dx = currentX - startX;

        const minMessageWidth = 150;
        const resizerWidth = 5;
        let gridGap = 10;
         try {
            gridGap = parseFloat(window.getComputedStyle(gridContainer).gap.split(' ')[1] || '10');
        } catch(e) { /* ignore */ }

        let newMessagesWidth = startWidthMessages + dx;

        if (newMessagesWidth < minMessageWidth) {
            newMessagesWidth = minMessageWidth;
        }

        const containerPadding = parseFloat(window.getComputedStyle(gridContainer).paddingLeft) + parseFloat(window.getComputedStyle(gridContainer).paddingRight);
        const maxMessageWidth = Math.max(minMessageWidth, gridContainer.clientWidth - resizerWidth - gridGap - containerPadding);
         if (newMessagesWidth > maxMessageWidth) {
            newMessagesWidth = maxMessageWidth;
         }

        gridContainer.style.gridTemplateColumns = `${newMessagesWidth}px ${resizerWidth}px`;
        handle.style.left = `${newMessagesWidth + gridGap}px`;
    }

    function handleMouseUp() {
        if (isResizing) {
            isResizing = false;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);

            document.body.style.userSelect = '';
            document.body.style.pointerEvents = '';
        }
    }

    window.addEventListener('resize', () => {
         requestAnimationFrame(() => setTimeout(updateHandlePosition, 0));
    });

} else {
    console.warn("Resizable handle, grid container, or message columns not found.");
}

const annotationButtons = document.querySelectorAll('.add-annotation-btn');
annotationButtons.forEach(button => {
    button.addEventListener('click', (e) => {
         const turnDiv = button.closest('.turn'); // Button is now inside .turn
         const turnNumEl = turnDiv?.querySelector('.turn-number');
         console.log('Annotation button clicked for turn:', turnNumEl ? turnNumEl.textContent : 'unknown');
         alert('Annotation functionality not yet implemented.');
         e.stopPropagation();
    });
});


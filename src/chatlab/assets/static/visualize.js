const handle = document.getElementById('dragHandle');
const gridContainers = document.querySelectorAll('.conversation-section');
const messageColumnCells = document.querySelectorAll('.grid-col-message');
const annotationColumnCells = document.querySelectorAll('.grid-col-annotation');
const generalObservations = document.getElementById('general-observations');

// Set up general observations autosave
if (generalObservations) {
    // Try to load saved observations from localStorage
    try {
        const savedObservations = localStorage.getItem('general-observations');
        if (savedObservations) {
            generalObservations.innerHTML = savedObservations;
        }
    } catch (e) {
        console.warn('Could not load saved observations:', e);
    }

    // Set up event listener to save observations on changes
    generalObservations.addEventListener('input', function() {
        try {
            localStorage.setItem('general-observations', this.innerHTML);
        } catch (e) {
            console.warn('Could not save observations:', e);
        }
    });

    // Set focus to the general observations box when clicked
    generalObservations.addEventListener('click', function() {
        if (!this.getAttribute('data-clicked')) {
            this.setAttribute('data-clicked', 'true');
            this.focus();
        }
    });
}

// Handle slider resizing
let isResizing = false;
let startX, startWidthMessages;

if (handle && gridContainers.length > 0 && messageColumnCells.length > 0) {

    function updateHandlePosition() {
        const firstMessageCell = messageColumnCells[0];
        if (!firstMessageCell) return;
        const messageColWidth = firstMessageCell.offsetWidth;
        let gridGap = 10;
        try {
            gridGap = parseFloat(window.getComputedStyle(gridContainers[0]).gap.split(' ')[1] || '10');
        } catch(e) { console.warn("Could not parse grid gap, defaulting to 10px"); }

        // Calculate left position based on the first message cell and container offset
        const containerRect = gridContainers[0].getBoundingClientRect();
        const messageCellRect = firstMessageCell.getBoundingClientRect();
        handle.style.left = `${messageCellRect.width + containerRect.left + gridGap}px`;
    }

    // Initialize handle position
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
            gridGap = parseFloat(window.getComputedStyle(gridContainers[0]).gap.split(' ')[1] || '10');
        } catch(e) { /* ignore */ }

        let newMessagesWidth = startWidthMessages + dx;

        if (newMessagesWidth < minMessageWidth) {
            newMessagesWidth = minMessageWidth;
        }

        // Get container rect to calculate maximum width
        const containerRect = gridContainers[0].getBoundingClientRect();
        const containerPadding = parseFloat(window.getComputedStyle(gridContainers[0]).paddingLeft) +
                               parseFloat(window.getComputedStyle(gridContainers[0]).paddingRight);

        // Maximum width calculation accounting for padding, gap, and fixed annotation width (400px)
        const maxMessageWidth = Math.max(minMessageWidth, containerRect.width - resizerWidth - gridGap - containerPadding - 400);

        if (newMessagesWidth > maxMessageWidth) {
            newMessagesWidth = maxMessageWidth;
        }

        // Update grid columns template for all sections
        gridContainers.forEach(container => {
            container.style.gridTemplateColumns = `${newMessagesWidth}px ${resizerWidth}px 400px`;
        });

        // Update handle position
        handle.style.left = `${containerRect.left + newMessagesWidth + gridGap}px`;
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

    // Ensure the handle position updates when window resizes
    window.addEventListener('resize', () => {
        requestAnimationFrame(() => setTimeout(updateHandlePosition, 0));
    });

} else {
    console.warn("Resizable handle, grid container, or message columns not found.");
}

// Add click handlers for annotation buttons
const annotationButtons = document.querySelectorAll('.add-annotation-btn');
annotationButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        const annotationContainer = button.closest('.annotation-container');
        console.log('Annotation button clicked for container:', annotationContainer);

        // Create annotation editor if it doesn't exist
        if (!annotationContainer.querySelector('.annotation-textbox')) {
            const textbox = document.createElement('div');
            textbox.className = 'annotation-textbox';
            textbox.setAttribute('contenteditable', 'true');

            // Add delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-annotation-btn';
            deleteBtn.innerHTML = '&times;';
            deleteBtn.title = 'Delete annotation';

            deleteBtn.addEventListener('click', () => {
                annotationContainer.classList.remove('editing');
                textbox.innerHTML = '';
                annotationContainer.removeChild(textbox);
                annotationContainer.removeChild(deleteBtn);
            });

            annotationContainer.appendChild(textbox);
            annotationContainer.appendChild(deleteBtn);
        }

        annotationContainer.classList.add('editing');
        annotationContainer.querySelector('.annotation-textbox').focus();

        e.stopPropagation();
    });
});
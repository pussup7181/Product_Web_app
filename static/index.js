var items = {{ items|tojson }};
    var currentIndex = 0;

    function openModal(index) {
        currentIndex = index;
        const item = items[currentIndex];

        // Set modal details
        document.getElementById('modalTitle').textContent = item.name;
        document.getElementById('modalImage').src = `data:image/png;base64,${item.photo}`;
        document.getElementById('modalArticleNumber').textContent = item.article_number;
        document.getElementById('modalSize').textContent = item.size_in_mm;
        document.getElementById('modalWeight').textContent = item.weight_in_g;

        // Handle next/prev button visibility
        updateNavButtons();

        // Show modal
        $('#itemModal').modal('show');
    }

    function updateNavButtons() {
        // Enable/Disable prev button
        if (currentIndex > 0) {
            document.getElementById('prevBtn').disabled = false;
        } else {
            document.getElementById('prevBtn').disabled = true;
        }

        // Enable/Disable next button
        if (currentIndex < items.length - 1) {
            document.getElementById('nextBtn').disabled = false;
        } else {
            document.getElementById('nextBtn').disabled = true;
        }
    }

    function showNextItem() {
        if (currentIndex < items.length - 1) {
            currentIndex++;
            openModal(currentIndex);
        }
    }

    function showPreviousItem() {
        if (currentIndex > 0) {
            currentIndex--;
            openModal(currentIndex);
        }
    }
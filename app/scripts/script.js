document.addEventListener('DOMContentLoaded', function () {
    // Attach a click event handler to the heart icons
    document.querySelectorAll('.heart-btn').forEach(function (heartBtn) {
        heartBtn.addEventListener('click', function (event) {
            event.preventDefault(); // Prevent the default click behavior

            // Get the photo ID from the data attribute
            var photoId = heartBtn.dataset.photoId;

            // Perform an AJAX request to update the like status
            fetch(heartBtn.closest('.heart-form').action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}) // You can add data if needed
            })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                // Update the heart icon based on the response
                if (data.hearted) {
                    // If hearted, update to solid heart
                    heartBtn.innerHTML = '<i class="fas fa-heart fa-2x"></i>';
                } else {
                    // If not hearted, update to regular heart
                    heartBtn.innerHTML = '<i class="far fa-heart fa-2x"></i>';
                }

                // Update the heart count
                var heartCount = heartBtn.closest('.heart-form').querySelector('.heart-count');
                if (heartCount) {
                    heartCount.innerText = data.hearts_count;
                }
            });
        });
    });
});              
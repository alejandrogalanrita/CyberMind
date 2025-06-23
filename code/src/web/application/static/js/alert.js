// Event listener for the banner close button
document.addEventListener('DOMContentLoaded', function () {
    const alertBanner = document.getElementById('alert-banner');
    const closeButton = document.getElementById('alert-banner-close');
        
    closeButton.addEventListener('click', function () {
        alertBanner.classList.add('d-none');
    });
});
    
document.addEventListener('DOMContentLoaded', function () {
    const wrapper = document.querySelector('.carousel-wrapper');
    let currentIndex = 0;

    function showSlide(index) {
        const newTranslateValue = -index * 100 + '%';
        wrapper.style.transform = 'translateX(' + newTranslateValue + ')';
    }

    function nextSlide() {
        currentIndex = (currentIndex + 1) % wrapper.children.length;
        showSlide(currentIndex);
    }

    setInterval(nextSlide, 5000); // Change slide every 5 seconds (adjust as needed)
});
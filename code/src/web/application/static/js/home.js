/* Web animations */
const elements = document.querySelectorAll(".fade-in");
const animatedElements = [false, false, false];
let index = 0; // Index of the current element to animate

// Animate the next element
function animateNext() {
    if (index >= elements.length) return;
    
    // Check if the current element is visible
    const elementoActual = elements[index];
    const rect = elementoActual.getBoundingClientRect();
    const estaVisible = rect.top < window.innerHeight && rect.bottom >= 0;
    
    // Apply animation if the element is visible and not already animated
    if (estaVisible && !animatedElements[index]) {
        elementoActual.classList.add("visible");
        animatedElements[index] = true;
        setTimeout(() => {
            index++;
            animateNext();
        }, 2000);
    } else {
        // if the current element is not visible, wait for the next frame to check again
        requestAnimationFrame(animateNext);
    }
}

// Handle scroll event
function handleScroll() {
    if (index < elements.length) {
        requestAnimationFrame(animateNext);
    }
}

// List Element animations
animateNext();
window.addEventListener('scroll', handleScroll);

// Card animations
const cards = document.querySelectorAll(".zoom-in");
const observerCards = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible"); 
        }
    });
}, { threshold: 0.1 }); 
cards.forEach(card => observerCards.observe(card));

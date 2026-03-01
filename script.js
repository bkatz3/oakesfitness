// Hero flicker animation — cycles through phrases, ends on "live better."
const flickerEl = document.querySelector('.hero-flicker');
if (flickerEl) {
    const phrases = [
        'getting stronger',
        'losing weight',
        'feeling healthier',
        'moving without pain',
        'feeling confident',
        'living better.'
    ];
    let current = 0;

    function nextPhrase() {
        // Don't cycle past the last phrase
        if (current >= phrases.length - 1) return;

        // Fade out
        flickerEl.classList.add('fading');

        setTimeout(() => {
            current++;
            flickerEl.textContent = phrases[current];

            // Fade back in
            flickerEl.classList.remove('fading');

            // Keep cycling unless we've landed on the final phrase
            if (current < phrases.length - 1) {
                setTimeout(nextPhrase, 2500);
            }
        }, 350); // matches the CSS transition duration
    }

    // Start cycling after a short delay so the page load animation settles
    setTimeout(nextPhrase, 2500);
}

// Scroll Reveal Animation
const revealElements = document.querySelectorAll('.reveal');

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('active');
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
});

revealElements.forEach(element => {
    revealObserver.observe(element);
});

// Navigation Scroll Effect
const nav = document.getElementById('nav');
let lastScrollY = window.scrollY;

window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        nav.classList.add('scrolled');
    } else {
        nav.classList.remove('scrolled');
    }
});

// Mobile Navigation Toggle
const navToggle = document.getElementById('navToggle');
const navLinks = document.querySelector('.nav-links');

navToggle.addEventListener('click', () => {
    navToggle.classList.toggle('active');
    navLinks.classList.toggle('active');
});

// Close mobile menu when clicking a link
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navLinks.classList.remove('active');
    });
});

// Smooth scroll offset for fixed nav (optional enhancement)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');

        // Skip if it's just "#" or a mailto/tel link
        if (href === '#' || href.startsWith('mailto:') || href.startsWith('tel:')) {
            return;
        }

        e.preventDefault();
        const target = document.querySelector(href);

        if (target) {
            const offsetTop = target.offsetTop - 80; // Account for fixed nav height
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    });
});

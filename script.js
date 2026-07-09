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

// Sticky Mobile CTA — shows when the hero section scrolls out of view
const stickyCta = document.getElementById('stickyCta');
const heroSection = document.getElementById('hero');

if (stickyCta && heroSection) {
    const heroObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Hero is visible — hide the bar
                stickyCta.classList.remove('visible');
            } else {
                // Hero is gone — slide the bar up
                stickyCta.classList.add('visible');
            }
        });
    }, { threshold: 0 });

    heroObserver.observe(heroSection);
}

// Team Carousel — click-through, one trainer at a time
const teamTrack = document.getElementById('teamTrack');

if (teamTrack) {
    const teamCards = teamTrack.querySelectorAll('.team-card');
    const teamPrev = document.getElementById('teamPrev');
    const teamNext = document.getElementById('teamNext');
    const teamDots = document.querySelectorAll('.team-dot');
    const teamAnnouncer = document.getElementById('teamAnnouncer');
    let teamIndex = 0;

    // True while an arrow/dot click is smooth-scrolling the track. Blocks the
    // scroll listener below from recomputing teamIndex mid-animation, which
    // would otherwise race the click handler's own index update. A wrap-around
    // jump (e.g. index 0 -> 4) travels several card-widths and can take far
    // longer to settle than an adjacent-slide move, so the flag is cleared by
    // the browser's own 'scrollend' event rather than a guessed fixed delay —
    // a fixed delay short enough for a 1-slide move would fire mid-animation
    // for a multi-slide wrap and let the debounce below overwrite teamIndex
    // with a stale, still-animating scrollLeft reading.
    let teamIsProgrammaticScroll = false;

    function goToTeamSlide(index) {
        teamIndex = index;
        teamIsProgrammaticScroll = true;
        teamTrack.scrollTo({ left: teamTrack.clientWidth * teamIndex, behavior: 'smooth' });
        updateTeamControls();
    }

    teamTrack.addEventListener('scrollend', () => {
        teamIsProgrammaticScroll = false;
    });

    function updateTeamControls() {
        teamDots.forEach((dot, i) => dot.classList.toggle('active', i === teamIndex));
        if (teamAnnouncer) {
            const name = teamCards[teamIndex]?.querySelector('.team-name')?.textContent || '';
            const role = teamCards[teamIndex]?.querySelector('.team-role')?.textContent || '';
            teamAnnouncer.textContent = [name, role].filter(Boolean).join(', ');
        }
    }

    teamPrev.addEventListener('click', () => {
        goToTeamSlide((teamIndex - 1 + teamCards.length) % teamCards.length);
    });

    teamNext.addEventListener('click', () => {
        goToTeamSlide((teamIndex + 1) % teamCards.length);
    });

    teamDots.forEach((dot, i) => {
        dot.addEventListener('click', () => goToTeamSlide(i));
    });

    // Keep dots/arrows in sync when the user swipes the track manually.
    // scrollLeft / clientWidth recovers the slide index because each card is
    // exactly one track-width wide (see .team-carousel-track .team-card).
    let teamScrollTimeout;
    teamTrack.addEventListener('scroll', () => {
        if (teamIsProgrammaticScroll) return;
        clearTimeout(teamScrollTimeout);
        teamScrollTimeout = setTimeout(() => {
            teamIndex = Math.round(teamTrack.scrollLeft / teamTrack.clientWidth);
            updateTeamControls();
        }, 100);
    });

    updateTeamControls();
}

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

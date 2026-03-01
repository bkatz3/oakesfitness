// Google Analytics 4 — CTA Click Tracking
// Measurement ID: G-Z93M42XMML

// Load the GA4 script async
(function () {
  var script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtag/js?id=G-Z93M42XMML';
  document.head.appendChild(script);
})();

// Initialize GA4 (use existing dataLayer if GTM already created it)
window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
gtag('js', new Date());
gtag('config', 'G-Z93M42XMML');

// Set up click tracking after the page loads
document.addEventListener('DOMContentLoaded', function () {

  // Figure out where on the page an element lives
  function getLocation(el) {
    if (el.id === 'stickyCta')      return 'sticky';
    if (el.closest('nav'))          return 'nav';
    if (el.closest('.hero'))        return 'hero';
    if (el.closest('footer'))       return 'footer';
    return 'section'; // service cards, bottom CTA block, blog inline CTAs
  }

  // Track every link to /contact (all "Get a Free Consultation" style CTAs)
  document.querySelectorAll('a[href="/contact"]').forEach(function (link) {
    link.addEventListener('click', function () {
      gtag('event', 'cta_click', {
        cta_label:    link.innerText.trim(),   // exact button text
        cta_location: getLocation(link),       // where on the page
        page_path:    window.location.pathname // which page
      });
    });
  });

  // Track phone number clicks
  document.querySelectorAll('a[href^="tel:"]').forEach(function (link) {
    link.addEventListener('click', function () {
      gtag('event', 'phone_click', {
        phone_number: link.href.replace('tel:', ''),
        cta_location: getLocation(link),
        page_path:    window.location.pathname
      });
    });
  });

  // Track email clicks
  document.querySelectorAll('a[href^="mailto:"]').forEach(function (link) {
    link.addEventListener('click', function () {
      gtag('event', 'email_click', {
        cta_location: getLocation(link),
        page_path:    window.location.pathname
      });
    });
  });

});

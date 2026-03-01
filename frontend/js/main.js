/* ============================================
   Stone Sharp Academy — Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initSmoothScroll();
    initScrollAnimations();
    initHeaderScroll();
    initFaqAccordion();
    initQuoteForm();
});

/* --- Navigation Toggle for Mobile --- */
function initNavigation() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-link');

    if (!navToggle || !navMenu) return;

    navToggle.addEventListener('click', function() {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });

    // Close menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}

/* --- Smooth Scroll for Anchor Links --- */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (!target) return;

            e.preventDefault();

            const header = document.getElementById('header');
            const headerHeight = header ? header.offsetHeight : 80;
            const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        });
    });
}

/* --- Scroll-triggered Animations --- */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    if (!animatedElements.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    animatedElements.forEach(el => observer.observe(el));
}

/* --- Header Scroll Effect --- */
function initHeaderScroll() {
    const header = document.getElementById('header');
    if (!header) return;

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

/* --- FAQ Accordion --- */
function initFaqAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    if (!faqItems.length) return;

    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');

        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');

            // Close all
            faqItems.forEach(i => {
                i.classList.remove('active');
                i.querySelector('.faq-answer').style.maxHeight = null;
            });

            // Open clicked (if it wasn't already open)
            if (!isActive) {
                item.classList.add('active');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            }
        });
    });
}

/* --- Quote / Contact Form Handling --- */
function initQuoteForm() {
    const form = document.getElementById('quoteForm');
    const formSuccess = document.getElementById('formSuccess');

    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        // Basic validation
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            removeError(field);

            if (!field.value.trim()) {
                showError(field, 'This field is required');
                isValid = false;
            } else if (field.type === 'email' && !isValidEmail(field.value)) {
                showError(field, 'Please enter a valid email address');
                isValid = false;
            }
        });

        if (!isValid) {
            const firstError = form.querySelector('.form-error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        // Submit to backend
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';

        const formData = new FormData(form);

        fetch('/submit', {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData
        })
        .then(function(response) { return response.json(); })
        .then(function(result) {
            if (result.success) {
                form.classList.add('hidden');
                if (formSuccess) formSuccess.classList.add('show');
            } else {
                var errorField = result.error && result.error.includes('phone') ? form.querySelector('#phone') : null;
                if (errorField) {
                    showError(errorField, result.error);
                } else {
                    alert(result.error || 'Something went wrong. Please try again.');
                }
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        })
        .catch(function() {
            alert('Something went wrong. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });

    // Real-time validation
    form.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('blur', function() {
            validateField(this);
        });

        field.addEventListener('input', function() {
            if (this.parentElement.querySelector('.form-error')) {
                validateField(this);
            }
        });
    });
}

function validateField(field) {
    removeError(field);

    if (field.required && !field.value.trim()) {
        showError(field, 'This field is required');
        return false;
    }

    if (field.type === 'email' && field.value && !isValidEmail(field.value)) {
        showError(field, 'Please enter a valid email address');
        return false;
    }

    return true;
}

function showError(field, message) {
    field.style.borderColor = 'var(--color-error)';

    const existingError = field.parentElement.querySelector('.form-error');
    if (existingError) {
        existingError.textContent = message;
        return;
    }

    const error = document.createElement('span');
    error.className = 'form-error';
    error.textContent = message;
    error.style.cssText = 'color: var(--color-error); font-size: 0.75rem; margin-top: 0.25rem; display: block;';
    field.parentElement.appendChild(error);
}

function removeError(field) {
    field.style.borderColor = '';
    const error = field.parentElement.querySelector('.form-error');
    if (error) error.remove();
}

function isValidEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/* --- Phone Number Formatting --- */
document.addEventListener('input', function(e) {
    if (e.target.id === 'phone') {
        var value = e.target.value.replace(/\D/g, '');
        if (value.length > 0) {
            if (value.length <= 3) {
                value = '(' + value;
            } else if (value.length <= 6) {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3);
            } else {
                value = '(' + value.substring(0, 3) + ') ' + value.substring(3, 6) + '-' + value.substring(6, 10);
            }
        }
        e.target.value = value;
    }
});

/* --- Active Link Highlighting --- */
(function() {
    var currentPage = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-link').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'index.html')) {
            link.classList.add('active');
        }
    });
})();

// Mobile nav toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });

        // Close nav when clicking a link on mobile
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
            });
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Fade-in animation on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .dest-card').forEach(el => {
        observer.observe(el);
    });

    // Seat class selection - update price display
    const seatRadios = document.querySelectorAll('input[name="seat_class"]');
    seatRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            document.querySelectorAll('.seat-option-label').forEach(label => {
                label.style.borderColor = 'var(--border-glass)';
                label.style.background = 'transparent';
                label.style.boxShadow = 'none';
            });
            if (this.checked) {
                const label = this.nextElementSibling || this.closest('.seat-option').querySelector('.seat-option-label');
                if (label) {
                    label.style.borderColor = 'var(--accent-blue)';
                    label.style.background = 'rgba(59, 130, 246, 0.1)';
                    label.style.boxShadow = '0 0 15px rgba(59, 130, 246, 0.3)';
                }
            }
        });
    });
});

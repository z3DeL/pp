// Улучшение мобильного UX
document.addEventListener('DOMContentLoaded', function() {
    // Закрытие мобильного меню при клике на пункт меню
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const menuToggle = document.getElementById('navbarNav');
    const bsCollapse = new bootstrap.Collapse(menuToggle, {toggle: false});
    
    navLinks.forEach((l) => {
        l.addEventListener('click', () => {
            if (window.innerWidth < 992) {
                bsCollapse.hide();
            }
        });
    });
    
    // Улучшение отображения таблиц на мобильных
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (!table.classList.contains('table-responsive')) {
            table.classList.add('table-responsive');
        }
    });
    
    // Улучшение отображения форм на мобильных
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!input.classList.contains('form-control') && !input.classList.contains('form-select')) {
                input.classList.add('form-control');
            }
        });
    });
    
    // Улучшение отображения кнопок на мобильных
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        if (!button.classList.contains('btn-block') && window.innerWidth < 768) {
            button.classList.add('w-100', 'mb-2');
        }
    });
}); 
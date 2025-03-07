document.addEventListener('DOMContentLoaded', function() {
    // Обработка кнопок избранного
    const favoriteButtons = document.querySelectorAll('.favorite-btn');
    favoriteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            fetch(`/jobs/${jobId}/favorite/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const icon = this.querySelector('i');
                    icon.classList.toggle('bi-heart');
                    icon.classList.toggle('bi-heart-fill');
                }
            });
        });
    });
});

// Функция для сортировки вакансий
function sortJobs(criteria) {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('sort', criteria === 'date' ? '-created_at' : '-salary');
    window.location.href = currentUrl.toString();
}

// Вспомогательная функция для получения CSRF-токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 
// Функция для получения CSRF токена
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

// Функция для обработки избранного
function handleFavorite(jobId) {
    fetch(`/jobs/${jobId}/favorite/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        const btn = document.querySelector(`.favorite-btn[data-job-id="${jobId}"]`);
        if (btn) {
            if (data.is_favorite) {
                btn.innerHTML = '<i class="bi bi-heart-fill"></i>';
            } else {
                btn.innerHTML = '<i class="bi bi-heart"></i>';
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

// Инициализация обработчиков событий
document.addEventListener('DOMContentLoaded', function() {
    // Обработчики для кнопок избранного
    const favoriteBtns = document.querySelectorAll('.favorite-btn');
    favoriteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const jobId = this.dataset.jobId;
            handleFavorite(jobId);
        });
    });

    // Активация подсказок Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Активация всплывающих подсказок Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}); 
// User state management
let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    function checkSession() {
        fetch('/check_session')
            .then(response => response.json())
            .then(data => {
                if (data.logged_in && data.user) {
                    currentUser = data.user;
                    currentUser.name = currentUser.username;
                    document.getElementById('userLoginBtn').style.display = 'none';
                    document.getElementById('userProfileBtn').style.display = 'block';
                    updateUserUI();
                    // Add global redirect for username
                    document.getElementById('userName').onclick = () => {
                        window.location.href = '/user_dashboard';
                    };
                } else {
                    currentUser = null;
                    document.getElementById('userLoginBtn').style.display = 'flex';
                    document.getElementById('userProfileBtn').style.display = 'none';
                }
                
                // Navigation restriction
                document.querySelectorAll('.nav a').forEach(link => {
                    link.addEventListener('click', (e) => {
                        if (!currentUser && link.getAttribute('href') !== '/') {
                            e.preventDefault();
                            alert('Please login to view categories');
                        }
                    });
                });
                document.getElementById('searchInput').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        performSearch();
                    }
                });
                document.querySelectorAll('.time').forEach(time => {
                    const date = new Date(time.textContent);
                    time.textContent = date.toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' });
                });
                // Initialize dashboard stats clicks (if on dashboard)
                if (document.getElementById('articlesSection')) {
                    // Stats clicks are handled via onclick in HTML
                    // Optional: Add any dashboard-specific initialization here
                }
            })
            .catch(error => {
                console.error('Error checking session:', error);
                currentUser = null;
                document.getElementById('userLoginBtn').style.display = 'flex';
                document.getElementById('userProfileBtn').style.display = 'none';
                // Retry once after a delay if fetch fails
                setTimeout(checkSession, 1000);
            });
    }
    
    checkSession();
});

function openUserPopup() {
    document.getElementById('loginPopupContainer').style.display = 'none';
    document.getElementById('calendarPopupContainer').style.display = 'none';
    document.getElementById('userPopupContainer').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
    updateUserUI();
    // Add redirect to user dashboard on username click
    const userNameElement = document.getElementById('userName');
    if (userNameElement) {
        userNameElement.onclick = () => {
            window.location.href = '/user_dashboard';
        };
    }
}

function performSearch() {
    const query = document.getElementById('searchInput').value.trim();
    if (query) {
        window.location.href = `/search?query=${encodeURIComponent(query)}`;
    } else {
        alert('Please enter a search term.');
    }
}

function updateUserUI() {
    if (currentUser) {
        document.getElementById('userName').textContent = (currentUser.name || currentUser.username).charAt(0).toUpperCase() + (currentUser.name || currentUser.username).slice(1);
        document.getElementById('userEmail').textContent = currentUser.email;
        const avatarUrl = `https://ui-avatars.com/api/?name=${currentUser.name || currentUser.username}&background=1e90ff&color=fff`;
        document.getElementById('userAvatar').src = avatarUrl;
        document.getElementById('userLikes').textContent = currentUser.likes || 0;
        document.getElementById('userFollowing').textContent = currentUser.following || 0;
        document.getElementById('userReports').textContent = currentUser.reports || 0;
        document.getElementById('userProfileBtn').querySelector('img').src = avatarUrl;
        console.log('Avatar URL set to:', avatarUrl); // Debug log
    }
}

function openCreateAccountPopup() {
    console.log("Opening create account popup");
    document.getElementById("createAccountPopupContainer").style.display = "block";
    document.getElementById("overlay").style.display = "block";
}

function closeCreateAccountPopup() {
    document.getElementById("createAccountPopupContainer").style.display = "none";
    document.getElementById("overlay").style.display = "none";
}

function toggleLike(button) {
    if (!currentUser) {
        alert('Please login to like articles');
        return;
    }
    
    const articleElement = button.closest('.news-box, .news-item');
    const articleId = articleElement.dataset.articleId;
    if (!articleId) {
        console.error("Article ID not found");
        return;
    }

    const wasLiked = button.classList.contains('liked');
    const endpoint = wasLiked ? '/unlike' : '/like';
    const likeCount = parseInt(button.querySelector('span').textContent);

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            alert(data.error);
            // Revert UI if server failed
            button.classList.toggle('liked', wasLiked);
            button.querySelector('span').textContent = wasLiked ? likeCount + 1 : likeCount - 1;
            return;
        }
        // Update all instances of the article
        document.querySelectorAll(`.news-box[data-article-id="${articleId}"], .news-item[data-article-id="${articleId}"]`).forEach(el => {
            const likeBtn = el.querySelector('.likes');
            likeBtn.classList.toggle('liked', !wasLiked);
            const countSpan = likeBtn.querySelector('span');
            countSpan.textContent = wasLiked ? Math.max(0, likeCount - 1) : likeCount + 1;
        });
        // Update user profile
        if (data.user) {
            currentUser.likes = data.user.likes;
            updateUserUI();
        }
    })
    .catch(error => {
        console.error('Error toggling like:', error);
        alert('Failed to update like. Please try again.');
        // Revert UI on error
        button.classList.toggle('liked', wasLiked);
        button.querySelector('span').textContent = wasLiked ? likeCount + 1 : likeCount - 1;
    });
}

function unlikeArticle(articleId) {
    return fetch("/unlike", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ article_id: articleId })
    })
    .then(response => response.json());
}

function toggleFollow(button) {
    if (!currentUser) {
        alert('Please login to follow sources');
        return;
    }
    const wasFollowing = button.classList.contains('following');
    const container = button.closest('.details, .news-meta');
    const sourceElement = container.querySelector('.source, .news-author');
    const sourceText = sourceElement.textContent.replace('+ Follow', '').replace('Following', '').trim();
    
    button.classList.toggle('following');
    button.textContent = button.classList.contains('following') ? 'Following' : '+ Follow';
    
    // Update all follow buttons for the same source
    document.querySelectorAll('.source, .news-author').forEach(el => {
        if (el.textContent.includes(sourceText)) {
            const followBtn = el.closest('.source, .news-meta').querySelector('.follow');
            if (followBtn) {
                followBtn.classList.toggle('following', !wasFollowing);
                followBtn.textContent = !wasFollowing ? 'Following' : '+ Follow';
            }
        }
    });
    
    if (!wasFollowing) {
        followChannel(sourceText)
            .then(data => {
                if (data.user) {
                    currentUser.following = data.user.following;
                    updateUserUI();
                }
            });
    } else {
        fetch('/unfollow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ channel: sourceText })
        })
        .then(response => response.json())
        .then(data => {
            if (data.user) {
                currentUser.following = data.user.following;
                updateUserUI();
            }
        });
    }
}

function fetchUserArticles(category) {
    if (!currentUser) {
        alert('Please login to view your articles');
        return;
    }

    const endpoints = {
        likes: '/user_liked_articles',
        following: '/user_followed_articles',
        reports: '/user_reported_articles'
    };

    const titles = {
        likes: 'Liked Articles',
        following: 'Articles from Followed Sources',
        reports: 'Reported Articles'
    };

    fetch(endpoints[category], {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        const articlesGrid = document.getElementById('articlesGrid');
        const articlesTitle = document.getElementById('articlesTitle');
        articlesTitle.textContent = titles[category];
        articlesGrid.innerHTML = '';

        if (data.articles && data.articles.length > 0) {
            data.articles.forEach(article => {
                const articleElement = document.createElement('div');
                articleElement.className = 'news-item';
                articleElement.dataset.articleId = article._id;
                articleElement.innerHTML = `
                    <div class="image-container">
                        <img src="${article.image_url || '/static/Uploads/noimage.jpg'}" alt="${article.title}" onerror="this.style.display='none';">
                    </div>
                    <div class="info">
                        <div class="likes ${article.is_liked ? 'liked' : ''}" onclick="toggleLike(this)">
                            <i class="fas fa-thumbs-up"></i><span>${article.likes || 0}</span>
                        </div>
                        <div class="report" onclick="reportPost(this)">${article.is_reported ? 'Reported' : 'Report'}</div>
                    </div>
                    <div class="news-title">${article.title}</div>
                    <a href="${article.url}" class="description-link"><div class="news-description">${article.summary}</div></a>
                    <div class="news-time">${new Date(article.published_at).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
                    <div class="news-meta">
                        <span class="news-author">${article.source}</span>
                        <span class="follow ${article.is_following ? 'following' : ''}" onclick="toggleFollow(this)">
                            ${article.is_following ? 'Following' : '+ Follow'}
                        </span>
                    </div>
                `;
                articlesGrid.appendChild(articleElement);
            });
        } else {
            articlesGrid.innerHTML = '<p>No articles available.</p>';
        }
    })
    .catch(error => {
        console.error(`Error fetching ${category} articles:`, error);
        document.getElementById('articlesGrid').innerHTML = '<p>Error loading articles.</p>';
    });
}

function reportPost(button) {
    if (!currentUser) {
        alert('Please login to report articles');
        return;
    }
    const articleElement = button.closest('.news-box, .news-item');
    const articleId = articleElement.dataset.articleId;
    const wasReported = button.classList.contains('reported');
    
    button.classList.toggle('reported');
    button.textContent = button.classList.contains('reported') ? 'Reported' : 'Report';
    
    fetch('/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ article_id: articleId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.user) {
            currentUser.reports = data.user.reports;
            updateUserUI();
            if (data.message === 'Article reported') {
                articleElement.style.display = 'none'; // Hide if reported
            } else {
                articleElement.style.display = ''; // Show if unreported
            }
        }
    });
}

function openLoginPopup() {
    document.getElementById('calendarPopupContainer').style.display = 'none';
    document.getElementById('userPopupContainer').style.display = 'none';
    document.getElementById('loginPopupContainer').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
    document.getElementById('loginUsernameEmail').focus();
}

function closeLoginPopup() {
    document.getElementById('loginPopupContainer').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function openUserPopup() {
    document.getElementById('loginPopupContainer').style.display = 'none';
    document.getElementById('calendarPopupContainer').style.display = 'none';
    document.getElementById('userPopupContainer').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
    updateUserUI();
}

function closeUserPopup() {
    document.getElementById('userPopupContainer').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function logoutUser() {
    fetch('/logout')
        .then(response => response.json())
        .then(data => {
            currentUser = null;
            document.getElementById('userLoginBtn').style.display = 'flex';
            document.getElementById('userProfileBtn').style.display = 'none';
            closeUserPopup();
            alert(data.message);
            window.location.reload(); // Refresh to reset article visibility
        })
        .catch(error => console.error("Error:", error));
}

function submitLogin() {
    const usernameEmail = document.getElementById('loginUsernameEmail').value.trim();
    const password = document.getElementById('loginPassword').value;

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ usernameEmail, password })
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url; // Follow the redirect to /dashboard
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.error) {
            alert(data.error);
            return;
        }
        if (data && data.user) {
            currentUser = data.user;
            currentUser.name = currentUser.username;
            document.getElementById('userLoginBtn').style.display = 'none';
            document.getElementById('userProfileBtn').style.display = 'block';
            closeLoginPopup();
            updateUserUI();
            window.location.reload();  // Ensure session is applied for regular users
        }
    })
    .catch(error => console.error('Error:', error));
}

function submitCreateAccount() {
    const username = document.getElementById("createAccountUsername").value.trim();
    const email = document.getElementById("createAccountEmail").value.trim();
    const password = document.getElementById("createAccountPassword").value;
    const passwordConfirm = document.getElementById("createAccountPasswordConfirm").value;
    const gender = document.getElementById("createAccountGender").value;
    const age = document.getElementById("createAccountAge").value;

    if (password !== passwordConfirm) {
        alert("Passwords do not match!");
        return;
    }

    fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password, gender, age }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            currentUser = {
                username: username,
                email: email,
                likes: 0,
                following: 0,
                reports: 0,
                gender: gender,
                age: parseInt(age)
            };
            document.getElementById('userLoginBtn').style.display = 'none';
            document.getElementById('userProfileBtn').style.display = 'block';
            closeCreateAccountPopup();
            updateUserUI();
            window.location.reload();  // Ensure session is applied
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}

function registerUser(userData) {
    return fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData)
    })
    .then(response => response.json());
}

function likeArticle(articleId) {
    return fetch("/like", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ article_id: articleId })
    })
    .then(response => response.json());
}

function followChannel(channel) {
    return fetch("/follow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: channel })
    })
    .then(response => response.json());
}

function reportArticle(articleId) {
    return fetch("/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ article_id: articleId })
    })
    .then(response => response.json());
}

// Calendar functions remain unchanged
let currentDate = new Date();
let currentMonth = currentDate.getMonth();
let currentYear = currentDate.getFullYear();

function openCalendarPopup() {
    document.getElementById('loginPopupContainer').style.display = 'none';
    document.getElementById('userPopupContainer').style.display = 'none';
    document.getElementById('calendarPopupContainer').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
    renderCalendar();
}

function closeCalendarPopup() {
    document.getElementById('calendarPopupContainer').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

function prevMonth() {
    currentMonth--;
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    renderCalendar();
}

function nextMonth() {
    currentMonth++;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    renderCalendar();
}

function renderCalendar() {
    const monthYearElement = document.getElementById('calendarMonthYear');
    const calendarGrid = document.getElementById('calendarGrid');
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    monthYearElement.textContent = `${months[currentMonth]} ${currentYear}`;
    calendarGrid.innerHTML = '';

    days.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'day-name';
        dayElement.textContent = day;
        calendarGrid.appendChild(dayElement);
    });

    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'day empty';
        calendarGrid.appendChild(emptyDay);
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'day';
        dayElement.textContent = day;

        const today = new Date();
        if (day === today.getDate() && currentMonth === today.getMonth() && currentYear === today.getFullYear()) {
            dayElement.classList.add('today');
        }

        dayElement.addEventListener('click', () => {
            // Format the date as YYYY-MM-DD
            const selectedDate = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            // Redirect to the /date route with the selected date as a query parameter
            window.location.href = `/date?date=${selectedDate}`;
        });

        calendarGrid.appendChild(dayElement);
    }
}
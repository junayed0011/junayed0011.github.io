/**
 * THE DAILY PULSE — EDITORIAL LOGIC & INTERACTION ENGINE
 * Native ES6 JavaScript
 */

// ==========================================================================
// 0. Google Blogger Integration Configuration (Option A)
// ==========================================================================
const BLOGGER_CONFIG = {
    // 1. Enable live fetching (Set to true to pull live posts from your Blogger blog)
    useLiveBloggerFeed: true, 
    
    // 2. Your Google Blogger Blog ID 
    // You can find this in your Blogger URL when logged into your dashboard (e.g., blogId=87654321...)
    blogId: "1496630585809549653", 
    
    // 3. Fallback Blogspot URL (e.g., "https://yourblog.blogspot.com")
    // Used if Blog ID is not supplied or for direct feed parsing
    blogUrl: "" 
};

// ==========================================================================
// 1. Fallback Mock Post Database (Offline preview / Safe Error Fallback)
// ==========================================================================
const POSTS_DATABASE = [
    {
        id: "ai-everyday-life",
        title: "How Artificial Intelligence is Changing Everyday Life",
        slug: "how-artificial-intelligence-is-changing-everyday-life",
        date: "May 20, 2026",
        category: "tech",
        readTime: "5 min read",
        description: "Artificial intelligence (AI) is increasingly being integrated into our homes, making our lives more convenient, highly productive, and uniquely personalized. Discover smart systems and integrations.",
        image: "https://image.pollinations.ai/prompt/how%20artificial%20intelligence%20is%20changing%20everyday%20life?width=800&height=450&nologo=true",
        author: "Alex Rivers",
        trending: true,
        featured: true,
        postUrl: ""
    },
    {
        id: "saving-money-budget",
        title: "Saving Money on a Tight Budget: Proven Tactics",
        slug: "saving-money-on-a-tight-budget-practical-tips",
        date: "May 15, 2026",
        category: "finance",
        readTime: "4 min read",
        description: "Living on a tight budget can be stressful, but it doesn't have to be impossible. With a little creativity and rigorous financial tracking, you can fast-track your savings goals.",
        image: "https://images.unsplash.com/photo-1635840420670-5470266ffa39?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Sarah Chen",
        trending: true,
        featured: false,
        postUrl: ""
    },
    {
        id: "mindfulness-stress",
        title: "Cultivating Calm: Daily Mindfulness Habits for Stress",
        slug: "cultivating-calm-mindfulness-habits-for-reducing-stress",
        date: "May 24, 2026",
        category: "mindset",
        readTime: "3 min read",
        description: "Reduce cortisol levels and regain mental clarity. Simple, scientifically-grounded habits to integrate mindfulness into your morning and workday routines.",
        image: "https://images.unsplash.com/photo-1506126613408-eca07ce68773?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Dr. Elena Moss",
        trending: true,
        featured: false,
        postUrl: ""
    },
    {
        id: "dev-free-tools",
        title: "Best Free Tools for Developers in 2026",
        slug: "best-free-tools-for-developers-in-2026",
        date: "May 20, 2026",
        category: "tech",
        readTime: "6 min read",
        description: "Boost your productivity without ballooning your overhead. We compile the definitive list of elite, open-source utilities and cloud services for developers.",
        image: "https://images.unsplash.com/photo-1618401471353-b98aedd07871?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Marcus Vance",
        trending: false,
        featured: false,
        postUrl: ""
    },
    {
        id: "side-hustles-zero-capital",
        title: "Side Hustles You Can Launch With Zero Capital",
        slug: "side-hustles-you-can-start-with-no-money",
        date: "May 27, 2026",
        category: "finance",
        readTime: "5 min read",
        description: "Unlock new cash flow streams leveraging only your laptop and existing skill sets. Skip the seed capital and explore freelancing, content creation, and consulting.",
        image: "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Sarah Chen",
        trending: true,
        featured: false,
        postUrl: ""
    },
    {
        id: "morning-routine-success",
        title: "Simple Morning Routines That Reshape Your Focus",
        slug: "simple-morning-routines-that-change-your-life",
        date: "May 22, 2026",
        category: "lifestyle",
        readTime: "4 min read",
        description: "How highly productive founders structure their initial 60 minutes. Learn about deep hydration, mental scoping, light therapy, and why you must delay checking email.",
        image: "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Elena Moss",
        trending: false,
        featured: false,
        postUrl: ""
    },
    {
        id: "improve-sleep-naturally",
        title: "Optimizing Circadian Rhythms: How to Sleep Better",
        slug: "improving-sleep-quality-naturally-tips-and-tricks",
        date: "May 23, 2026",
        category: "lifestyle",
        readTime: "5 min read",
        description: "Banish morning fatigue. A comprehensive blueprint on natural sleep enhancers, temperature calibration, blue light blockers, and pre-sleep wind-down protocols.",
        image: "https://images.unsplash.com/photo-1520206183501-b80df61043c2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Dr. Keith Ray",
        trending: false,
        featured: false,
        postUrl: ""
    },
    {
        id: "cybersecurity-beginners",
        title: "Cybersecurity Tips for Absolute Beginners",
        slug: "cybersecurity-tips-for-beginners",
        date: "May 21, 2026",
        category: "tech",
        readTime: "4 min read",
        description: "Protect your personal identity, passwords, and digital footprint. Simple defensive practices including passkeys, sandboxed browsers, and multi-factor strategies.",
        image: "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Marcus Vance",
        trending: false,
        featured: false,
        postUrl: ""
    },
    {
        id: "beginner-investing-strategy",
        title: "A Beginner's Guide to Low-Cost Investing",
        slug: "beginner-s-guide-to-investing-in-2025",
        date: "May 25, 2026",
        category: "finance",
        readTime: "5 min read",
        description: "Demystifying broad-market index funds, compounding returns, and risk management. Learn how a passive approach consistently beats active trading over time.",
        image: "https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Sarah Chen",
        trending: true,
        featured: false,
        postUrl: ""
    },
    {
        id: "daily-focus-boost",
        title: "Practical Ways to Double Your Focus Span Daily",
        slug: "simple-ways-to-improve-your-focus-daily",
        date: "May 19, 2026",
        category: "mindset",
        readTime: "3 min read",
        description: "Reclaim your attention span from smart notifications. We explore cognitive blocking, environmental design, Pomodoro limits, and single-tasking disciplines.",
        image: "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
        author: "Alex Rivers",
        trending: false,
        featured: false,
        postUrl: ""
    }
];

// ==========================================================================
// 2. Application State Management
// ==========================================================================
const AppState = {
    currentCategory: "all",
    searchQuery: "",
    theme: "light"
};

// DOM References
const bodyEl = document.body;
const themeBtn = document.getElementById("theme-mode-btn");
const scrollBar = document.getElementById("scroll-progress-bar");
const postsContainer = document.getElementById("news-posts-container");
const trendingContainer = document.getElementById("trending-posts-sidebar-list");
const searchInput = document.getElementById("feed-search-input");
const clearSearchBtn = document.getElementById("clear-search-btn");
const searchResultBanner = document.getElementById("search-result-banner");
const searchQueryHighlight = document.getElementById("search-query-highlight");
const emptyStateNotice = document.getElementById("empty-state-notice");
const resetSearchBtn = document.getElementById("reset-search-btn");
const clearAllFiltersBtn = document.getElementById("clear-all-filters-btn");
const filterPills = document.querySelectorAll(".pill");

// Mobile Menu References
const menuToggleBtn = document.getElementById("menu-toggle-btn");
const mobileNavDrawer = document.getElementById("mobile-nav-drawer");
const drawerBackdropOverlay = document.getElementById("drawer-backdrop-overlay");
const closeDrawerBtn = document.getElementById("close-drawer-btn");
const mobileNavLinks = document.querySelectorAll(".mobile-nav-link");
const footerCategoryLinks = document.querySelectorAll(".footer-link-item");

// Newsletter Form References
const newsletterFormSidebar = document.getElementById("newsletter-form-sidebar");
const emailInputSidebar = document.getElementById("newsletter-email-sidebar");
const newsletterSuccessBox = document.getElementById("newsletter-success-box");
const newsletterSubmitBtn = document.getElementById("newsletter-submit-btn");

const newsletterFormFooter = document.getElementById("newsletter-form-footer");
const emailInputFooter = document.getElementById("newsletter-email-footer");

// ==========================================================================
// 3. Dynamic Blogger API Feed Parser (Option A Engine)
// ==========================================================================
async function fetchBloggerFeed() {
    if (!BLOGGER_CONFIG.useLiveBloggerFeed) {
        console.log("ℹ️ Live Blogger Feed is disabled. Rendering premium static database.");
        return;
    }

    let feedUrl = "";
    if (BLOGGER_CONFIG.blogId && BLOGGER_CONFIG.blogId !== "YOUR_BLOGGER_BLOG_ID_HERE") {
        feedUrl = `https://www.blogger.com/feeds/${BLOGGER_CONFIG.blogId}/posts/default?alt=json&max-results=30`;
    } else if (BLOGGER_CONFIG.blogUrl) {
        const cleanUrl = BLOGGER_CONFIG.blogUrl.replace(/\/$/, "");
        feedUrl = `${cleanUrl}/feeds/posts/default?alt=json&max-results=30`;
    } else {
        console.warn("⚠️ Google Blogger Blog ID or URL is missing in CONFIG. Falling back to mock data.");
        return;
    }

    try {
        console.log(`🌐 Fetching live feeds from Blogger: ${feedUrl}`);
        const response = await fetch(feedUrl);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        
        const data = await response.json();
        const entries = data.feed.entry || [];
        
        if (entries.length === 0) {
            console.log("ℹ️ Blogger API returned 0 posts. Using mock posts fallback.");
            return;
        }

        // Map Blogger JSON values into our editorial layout system
        const mappedPosts = entries.map((entry, idx) => {
            const title = entry.title ? entry.title.$t : "Untitled Article";
            const content = entry.content ? entry.content.$t : "";
            
            // Extract the first image src tag inside HTML body using regex
            const imgRegex = /<img[^>]+src="([^">]+)"/;
            const imgMatch = content.match(imgRegex);
            const firstImg = imgMatch ? imgMatch[1] : "";
            
            // Reformat Date string
            const rawPubDate = entry.published ? entry.published.$t : "";
            let friendlyDate = "Recently";
            if (rawPubDate) {
                const dateObj = new Date(rawPubDate);
                friendlyDate = dateObj.toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric"
                });
            }
            
            // Map labels to channels (Tech, Finance, Lifestyle, Mindset)
            let category = "lifestyle";
            if (entry.category && entry.category.length > 0) {
                const rawTag = entry.category[0].term.toLowerCase();
                if (["tech", "technology", "artificialintelligence"].includes(rawTag)) category = "tech";
                else if (["finance", "money", "investing", "budgeting"].includes(rawTag)) category = "finance";
                else if (["lifestyle", "health", "diet"].includes(rawTag)) category = "lifestyle";
                else if (["mindset", "productivity", "focus", "habits"].includes(rawTag)) category = "mindset";
                else category = rawTag; // Use label verbatim if custom
            }
            
            // Clean HTML body to generate pure text excerpt
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = content;
            const cleanText = tempDiv.textContent || tempDiv.innerText || "";
            const excerpt = cleanText.trim().substring(0, 180).replace(/\s+/g, " ") + "...";
            
            // Calculate reading speed metrics (~200 words a minute)
            const wordsCount = cleanText.split(/\s+/).length;
            const readingMinutes = Math.max(1, Math.round(wordsCount / 200));
            
            // Generate clean slug from title
            const slug = title.toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/(^-|-$)+/g, "")
                .substring(0, 50);

            // Relalternate represents direct Blogger article URL
            const altLink = entry.link ? entry.link.find(l => l.rel === "alternate") : null;
            const postUrl = altLink ? altLink.href : "#";

            return {
                id: `blogger-post-${idx}`,
                title: title,
                slug: slug,
                date: friendlyDate,
                category: category,
                readTime: `${readingMinutes} min read`,
                description: excerpt,
                image: firstImg || `https://image.pollinations.ai/prompt/${encodeURIComponent(title)}?width=800&height=450&nologo=true`,
                author: entry.author && entry.author[0] ? entry.author[0].name.$t : "Editorial Staff",
                trending: idx < 5, // Top 5 marked as trending
                featured: idx === 0, // Latest post is featured hero
                postUrl: postUrl
            };
        });

        // Clear existing database and hydrate with live Blogger posts
        POSTS_DATABASE.length = 0;
        POSTS_DATABASE.push(...mappedPosts);
        console.log(`✅ Dynamically loaded ${mappedPosts.length} posts from your Google Blogger feed!`);
        
    } catch (err) {
        console.error("❌ Failed to resolve dynamic Blogger feed API:", err);
        console.log("⚠️ Falling back to high-fidelity offline preview database.");
    }
}

// ==========================================================================
// 4. Theme Management (Light / Dark sliding transition)
// ==========================================================================
function initTheme() {
    const savedTheme = localStorage.getItem("pulse-theme");
    const userPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    
    if (savedTheme === "dark" || (!savedTheme && userPrefersDark)) {
        bodyEl.classList.add("dark-theme");
        AppState.theme = "dark";
    } else {
        bodyEl.classList.remove("dark-theme");
        AppState.theme = "light";
    }
}

function toggleTheme() {
    if (bodyEl.classList.contains("dark-theme")) {
        bodyEl.classList.remove("dark-theme");
        localStorage.setItem("pulse-theme", "light");
        AppState.theme = "light";
    } else {
        bodyEl.classList.add("dark-theme");
        localStorage.setItem("pulse-theme", "dark");
        AppState.theme = "dark";
    }
}

// ==========================================================================
// 5. Scroll Tracking (Fluid progress indicator)
// ==========================================================================
function trackScrollProgress() {
    const winScroll = document.documentElement.scrollTop || document.body.scrollTop;
    const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
    scrollBar.style.width = scrolled + "%";
}

// ==========================================================================
// 6. News Feed Render Controllers
// ==========================================================================

// Injects Skeleton Loader UI to simulate fast, modern Single Page transitions
function showSkeletonLoader() {
    postsContainer.innerHTML = Array(4).fill(0).map(() => `
        <div class="skeleton-card">
            <div class="skeleton-img"></div>
            <div class="skeleton-text skeleton-title"></div>
            <div class="skeleton-text" style="width: 40%"></div>
            <div class="skeleton-text skeleton-desc"></div>
            <div class="skeleton-text" style="width: 90%; margin-top: auto;"></div>
        </div>
    `).join("");
}

// Helper to highlight matched search phrases inside elements
function highlightTerm(text, query) {
    if (!query) return text;
    const pattern = new RegExp(`(${query.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')})`, 'gi');
    return text.replace(pattern, `<mark class="search-highlight">$1</mark>`);
}

// Renders the Hero Highlight editorial layout
function renderHeroBlock() {
    const featuredPost = POSTS_DATABASE.find(post => post.featured) || POSTS_DATABASE[0];
    const subPosts = POSTS_DATABASE.filter(post => !post.featured).slice(0, 2);

    if (featuredPost) {
        const bgEl = document.getElementById("featured-hero-bg");
        const tagEl = document.getElementById("featured-hero-tag");
        const readEl = document.getElementById("featured-hero-readtime");
        const dateEl = document.getElementById("featured-hero-date");
        const titleEl = document.getElementById("featured-hero-title");
        const excerptEl = document.getElementById("featured-hero-excerpt");
        const btnEl = document.getElementById("featured-hero-btn");

        if (bgEl) bgEl.style.backgroundImage = `url('${featuredPost.image}')`;
        if (tagEl) {
            tagEl.innerText = featuredPost.category;
            tagEl.className = `badge badge-${featuredPost.category}`;
        }
        if (readEl) readEl.innerText = featuredPost.readTime;
        if (dateEl) dateEl.innerText = featuredPost.date;
        if (titleEl) titleEl.innerText = featuredPost.title;
        if (excerptEl) excerptEl.innerText = featuredPost.description;
        if (btnEl) {
            btnEl.href = featuredPost.postUrl || "#feed-anchor";
            if (featuredPost.postUrl) btnEl.target = "_blank";
        }
    }

    // Render Secondary featured list
    subPosts.forEach((post, index) => {
        const idx = index + 1;
        const bgEl = document.getElementById(`sub-bg-${idx}`);
        const tagEl = document.getElementById(`sub-tag-${idx}`);
        const titleEl = document.getElementById(`sub-title-${idx}`);
        const readEl = document.getElementById(`sub-read-${idx}`);
        const cardEl = document.getElementById(`sub-post-${idx}`);

        if (bgEl) bgEl.style.backgroundImage = `url('${post.image}')`;
        if (tagEl) tagEl.innerText = post.category;
        if (titleEl) titleEl.innerText = post.title;
        if (readEl) readEl.innerText = post.readTime;
        if (cardEl && post.postUrl) {
            cardEl.onclick = () => window.open(post.postUrl, "_blank");
        }
    });
}

// Renders the main grid feed
function renderNewsFeed() {
    const filteredPosts = POSTS_DATABASE.filter(post => {
        // Prevent layout duplication on Homepage by hiding Hero highlights if no searches are active
        if (post.featured && AppState.currentCategory === "all" && !AppState.searchQuery) return false;
        
        const matchesCategory = AppState.currentCategory === "all" || post.category === AppState.currentCategory;
        const matchesSearch = !AppState.searchQuery || 
            post.title.toLowerCase().includes(AppState.searchQuery.toLowerCase()) ||
            post.description.toLowerCase().includes(AppState.searchQuery.toLowerCase());
            
        return matchesCategory && matchesSearch;
    });

    // Handle Empty Search State
    if (filteredPosts.length === 0) {
        postsContainer.style.display = "none";
        emptyStateNotice.style.display = "block";
        return;
    } else {
        postsContainer.style.display = "grid";
        emptyStateNotice.style.display = "none";
    }

    postsContainer.innerHTML = filteredPosts.map(post => {
        const titleText = highlightTerm(post.title, AppState.searchQuery);
        const descText = highlightTerm(post.description, AppState.searchQuery);
        
        return `
            <article class="post-card">
                <div class="card-img-wrap" onclick="if('${post.postUrl || ''}') window.open('${post.postUrl}', '_blank');" style="cursor: pointer;">
                    <span class="card-badge badge-${post.category}">${post.category}</span>
                    <img class="card-img" src="${post.image}" alt="${post.title}" loading="lazy">
                </div>
                <div class="card-body">
                    <div class="card-meta">
                        <span class="card-author">${post.author}</span>
                        <span class="card-meta-dot"></span>
                        <span class="card-date">${post.date}</span>
                    </div>
                    <h3 class="card-headline" onclick="if('${post.postUrl || ''}') window.open('${post.postUrl}', '_blank');" style="cursor: pointer;">${titleText}</h3>
                    <p class="card-description">${descText}</p>
                    <div class="card-footer">
                        <span class="meta-item"><i class="fa-regular fa-clock"></i> ${post.readTime}</span>
                        <div class="card-footer-actions" style="display:flex; align-items:center; gap:16px;">
                            <button class="share-card-btn" onclick="copyShareLink('${post.postUrl || window.location.href}', event)" style="color:var(--text-secondary); font-size:14px; transition:color 0.2s ease, transform 0.2s ease; cursor:pointer;" title="Copy share link"><i class="fa-regular fa-share-from-square"></i></button>
                            <a href="${post.postUrl || '#feed-anchor'}" ${post.postUrl ? 'target="_blank"' : ''} class="read-more-link">Read briefing <i class="fa-solid fa-chevron-right"></i></a>
                        </div>
                    </div>
                </div>
            </article>
        `;
    }).join("");
}

// Renders the trending side rank numbers
function renderTrendingList() {
    const trendingPosts = POSTS_DATABASE.filter(post => post.trending).slice(0, 5);
    
    trendingContainer.innerHTML = trendingPosts.map((post, idx) => `
        <div class="trending-rank-item" onclick="if('${post.postUrl || ''}') window.open('${post.postUrl}', '_blank');">
            <span class="rank-number">0${idx + 1}</span>
            <div class="rank-text-wrap">
                <span class="rank-meta">${post.category} &middot; ${post.readTime}</span>
                <h4 class="rank-title">${post.title}</h4>
            </div>
        </div>
    `).join("");
}

// ==========================================================================
// 7. Drawers & Filter Navigation Controllers
// ==========================================================================
function openDrawer() {
    mobileNavDrawer.classList.add("open");
    drawerBackdropOverlay.classList.add("open");
    bodyEl.style.overflow = "hidden";
}

function closeDrawer() {
    mobileNavDrawer.classList.remove("open");
    drawerBackdropOverlay.classList.remove("open");
    bodyEl.style.overflow = "";
}

function applyFilter(category) {
    AppState.currentCategory = category;
    
    // Update pills on desktop
    filterPills.forEach(pill => {
        if (pill.dataset.filter === category) {
            pill.classList.add("active");
        } else {
            pill.classList.remove("active");
        }
    });

    // Update active drawer highlights
    mobileNavLinks.forEach(link => {
        if (link.dataset.category === category) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });

    // Transition simulation
    showSkeletonLoader();
    setTimeout(() => {
        renderNewsFeed();
    }, 280);
}

// ==========================================================================
// 8. Search Pipeline
// ==========================================================================
function handleSearch(val) {
    AppState.searchQuery = val.trim();
    
    if (AppState.searchQuery) {
        clearSearchBtn.style.display = "block";
        searchResultBanner.style.display = "flex";
        searchQueryHighlight.innerText = AppState.searchQuery;
    } else {
        clearSearchBtn.style.display = "none";
        searchResultBanner.style.display = "none";
    }

    renderNewsFeed();
}

function clearSearch() {
    searchInput.value = "";
    AppState.searchQuery = "";
    clearSearchBtn.style.display = "none";
    searchResultBanner.style.display = "none";
    renderNewsFeed();
}

// ==========================================================================
// 9. Newsletter Validation & Signups
// ==========================================================================
function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

function triggerFormSuccess(form, emailInput, successBox, submitBtn) {
    const btnText = submitBtn.querySelector(".btn-text");
    const btnSpinner = submitBtn.querySelector(".btn-spinner");
    
    if (btnText && btnSpinner) {
        btnText.style.display = "none";
        btnSpinner.style.display = "inline-block";
    }
    
    submitBtn.disabled = true;

    // Simulate API request delay
    setTimeout(() => {
        form.style.display = "none";
        successBox.style.display = "block";
        localStorage.setItem("pulse-subscriber", emailInput.value);
    }, 1200);
}

function checkSubscribedState() {
    const isSubscribed = localStorage.getItem("pulse-subscriber");
    if (isSubscribed) {
        const newsletterContainer = document.getElementById("sidebar-newsletter-card");
        if (newsletterContainer) {
            newsletterContainer.innerHTML = `
                <div class="widget-content">
                    <span class="widget-meta">WELCOME BACK</span>
                    <h3 class="widget-title">You're Inside The Pulse</h3>
                    <p class="widget-desc">You are currently receiving daily briefings to <strong>${isSubscribed}</strong>. Keep an eye out for updates.</p>
                </div>
            `;
        }
    }
}

// ==========================================================================
// 10. Initializers & Listeners registration
// ==========================================================================
document.addEventListener("DOMContentLoaded", async () => {
    initTheme();
    
    // Fetch live Blogger posts (if enabled)
    showSkeletonLoader();
    await fetchBloggerFeed();
    
    // Render dynamic editorial segments
    renderHeroBlock();
    renderTrendingList();
    applyFilter("all");
    checkSubscribedState();
    
    // Theme Switch Click listener
    themeBtn.addEventListener("click", toggleTheme);
    
    // Scroll tracking
    window.addEventListener("scroll", trackScrollProgress);
    
    // Search input pipeline
    searchInput.addEventListener("input", (e) => handleSearch(e.target.value));
    clearSearchBtn.addEventListener("click", clearSearch);
    resetSearchBtn.addEventListener("click", clearSearch);
    clearAllFiltersBtn.addEventListener("click", () => {
        clearSearch();
        applyFilter("all");
    });
    
    // Filter click listeners (desktop)
    filterPills.forEach(pill => {
        pill.addEventListener("click", () => {
            const cat = pill.dataset.filter;
            applyFilter(cat);
            
            // Scroll down to feed seamlessly
            const feedPos = document.getElementById("feed-anchor").offsetTop;
            if (window.scrollY < feedPos - 120) {
                window.scrollTo({
                    top: feedPos - 90,
                    behavior: "smooth"
                });
            }
        });
    });

    // Mobile nav links clicks
    mobileNavLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const cat = link.dataset.category;
            applyFilter(cat);
            closeDrawer();
            
            // Jump to news grid anchor
            const feedPos = document.getElementById("feed-anchor").offsetTop;
            window.scrollTo({
                top: feedPos - 90,
                behavior: "smooth"
            });
        });
    });

    // Footer links category navigation triggers
    footerCategoryLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            const cat = link.dataset.category;
            if (cat) {
                e.preventDefault();
                applyFilter(cat);
                
                // Jump to feed
                const feedPos = document.getElementById("feed-anchor").offsetTop;
                window.scrollTo({
                    top: feedPos - 90,
                    behavior: "smooth"
                });
            }
        });
    });

    // Drawers controls
    menuToggleBtn.addEventListener("click", openDrawer);
    closeDrawerBtn.addEventListener("click", closeDrawer);
    drawerBackdropOverlay.addEventListener("click", closeDrawer);
    
    // Sidebar conversion captures
    newsletterFormSidebar.addEventListener("submit", (e) => {
        e.preventDefault();
        const emailVal = emailInputSidebar.value;
        
        if (validateEmail(emailVal)) {
            triggerFormSuccess(
                newsletterFormSidebar,
                emailInputSidebar,
                newsletterSuccessBox,
                newsletterSubmitBtn
            );
        } else {
            alert("Please supply a genuine, structured email address.");
        }
    });

    // Footer captures
    newsletterFormFooter.addEventListener("submit", (e) => {
        e.preventDefault();
        const emailVal = emailInputFooter.value;
        
        if (validateEmail(emailVal)) {
            const btnSubmitFooter = newsletterFormFooter.querySelector(".btn-footer-submit");
            btnSubmitFooter.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
            btnSubmitFooter.disabled = true;
            
            setTimeout(() => {
                newsletterFormFooter.innerHTML = '<p style="font-size: 13px; color: #10B981; font-weight: 600;"><i class="fa-solid fa-circle-check"></i> Subscribed successfully!</p>';
                localStorage.setItem("pulse-subscriber", emailVal);
            }, 1000);
        } else {
            alert("Please supply a genuine email address.");
        }
    });
});

window.copyShareLink = function(url, event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    navigator.clipboard.writeText(url).then(() => {
        const toast = document.getElementById("share-toast");
        if (toast) {
            toast.classList.add("show");
            setTimeout(() => {
                toast.classList.remove("show");
            }, 2500);
        }
    }).catch(err => {
        console.error("Clipboard copy failed: ", err);
    });
};

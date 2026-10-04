// Theme toggle
(function() {
  const toggle = document.querySelector('.theme-toggle');
  const html = document.documentElement;
  
  // Check for saved preference or system preference
  const savedTheme = localStorage.getItem('theme');
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  const currentTheme = savedTheme || systemTheme;
  
  html.setAttribute('data-theme', currentTheme);
  updateToggleIcon(currentTheme);
  
  if (toggle) {
    toggle.addEventListener('click', () => {
      const newTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateToggleIcon(newTheme);
    });
  }
  
  function updateToggleIcon(theme) {
    if (toggle) {
      toggle.textContent = theme === 'dark' ? '☀️' : '🌙';
      toggle.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
    }
  }
})();

// Navbar scroll effect
(function() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;
    if (currentScroll > 10) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
  }, { passive: true });
})();

// Overflow menu toggle
(function() {
  const overflowBtn = document.querySelector('.overflow-menu-btn');
  const overflowDropdown = document.querySelector('.overflow-dropdown');
  
  if (overflowBtn && overflowDropdown) {
    overflowBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      overflowDropdown.classList.toggle('open');
      overflowBtn.textContent = overflowDropdown.classList.contains('open') ? '✕' : '☰';
    });
    
    // Close menu when a link is clicked
    overflowDropdown.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        overflowDropdown.classList.remove('open');
        overflowBtn.textContent = '☰';
      });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!overflowDropdown.contains(e.target) && !overflowBtn.contains(e.target)) {
        overflowDropdown.classList.remove('open');
        overflowBtn.textContent = '☰';
      }
    });
  }
  
  // Mobile menu toggle (for mobile view)
  const menuToggle = document.querySelector('.menu-toggle');
  const mobileNav = document.querySelector('.mobile-nav');
  
  if (menuToggle && mobileNav) {
    menuToggle.addEventListener('click', () => {
      mobileNav.classList.toggle('open');
      menuToggle.textContent = mobileNav.classList.contains('open') ? '✕' : '☰';
    });
    
    mobileNav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileNav.classList.remove('open');
        menuToggle.textContent = '☰';
      });
    });
  }
})();

// Active nav link highlighting
(function() {
  const navLinks = document.querySelectorAll('.nav-links a, .mobile-nav-links a');
  const currentPath = window.location.pathname;
  
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '/' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
})();

// Intersection Observer for animations
(function() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  document.querySelectorAll('.card, .timeline-item, .project-card, .article-card, .cert-card').forEach(el => {
    observer.observe(el);
  });
})();

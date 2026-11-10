// Theme Manager (Light / Dark mode persistence)
(function() {
  const savedTheme = localStorage.getItem('crisisguard_theme');
  const osPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme ? savedTheme : (osPrefersDark ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', initialTheme);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('crisisguard_theme', next);
  updateThemeIcon();
}

function updateThemeIcon() {
  const current = document.documentElement.getAttribute('data-theme');
  const icon = document.getElementById('theme-toggle-icon');
  if (icon) {
    icon.innerHTML = current === 'dark' ? '☀️' : '🌙';
  }
}

document.addEventListener('DOMContentLoaded', updateThemeIcon);

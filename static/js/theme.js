(function () {
    const root = document.documentElement;
    const toggleBtn = document.getElementById("themeToggle");
    const icon = toggleBtn ? toggleBtn.querySelector("i") : null;

    const getPreferredTheme = () => localStorage.getItem("theme") || "light";
    const setTheme = (theme) => {
        root.setAttribute("data-bs-theme", theme);
        if (icon) {
            icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
        }
        localStorage.setItem("theme", theme);
    };

    setTheme(getPreferredTheme());

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const current = root.getAttribute("data-bs-theme") || "light";
            setTheme(current === "dark" ? "light" : "dark");
        });
    }
})();
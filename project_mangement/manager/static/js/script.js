document.addEventListener("DOMContentLoaded", function() {
    // Example of a JS function, like a simple toggle for the nav menu on smaller screens
    const navToggle = document.getElementById("nav-toggle");
    const navMenu = document.getElementById("nav-menu");

    navToggle.addEventListener("click", function() {
        navMenu.classList.toggle("active");
    });

    // You can add more functionality here as needed
});

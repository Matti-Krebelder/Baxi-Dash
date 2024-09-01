window.onload = function () {
    const overlay = document.getElementById("overlay");
    setTimeout(() => {
        overlay.style.opacity = 0;
    }, 3500);
    setTimeout(() => {
        overlay.style.display = "none";
    }, 4500);
};
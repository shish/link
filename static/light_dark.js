function isDarkModeEnabled() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => { //system scheme updated
    setColorMode();
});

function setColorMode(){
    document.body.className = isDarkModeEnabled() ? "dark" : "light";
}

setColorMode(); //set the color mode class as soon as the body tag is loaded

function isDarkModeEnabled() {
    theme = localStorage.getItem("theme")
    switch(theme){
        case "dark": return true;
        case "light": return false;
        default: return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => { //system scheme updated
    localStorage.setItem("theme", null)
    setTheme();
});

function setTheme(theme = null){
    if(!theme) theme = isDarkModeEnabled() ? "dark" : "light";
    document.body.className = theme
}

function toggleTheme(){
    theme = localStorage.getItem("theme")
    switch(theme){
        case "dark": theme = "light"; break;
        case "light": theme = "dark"; break;
        default: theme = isDarkModeEnabled() ? "light" : "dark"
    }
    localStorage.setItem("theme", theme)
    setTheme(theme)
}

setTheme(); //set the color mode class as soon as the body tag is loaded

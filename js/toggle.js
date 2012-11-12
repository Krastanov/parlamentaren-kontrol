function toggle(showHideDiv, switchTextDiv, showText, hideText) {
    var ele = document.getElementById(showHideDiv);
    var text = document.getElementById(switchTextDiv);
    if(ele.style.display == "block") {
            ele.style.display = "none";
        text.innerHTML = showText;
    }
    else {
        ele.style.display = "block";
        text.innerHTML = hideText;
    }
} 
function toggle_array(contents, switchTextDiv, showText, hideText) {
    for(i=0; i < contents.length; i++) {
        toggle(contents[i], switchTextDiv, showText, hideText);
    }
}

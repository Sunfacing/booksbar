
// Expand sidenav
function openNav() {
  document.getElementById("mySidenav").style.width = "250px";
}

// Hide sidenav
function closeNav() {
  document.getElementById("mySidenav").style.width = "0";
}



function scrollFunction() {
    if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
    } else {
    mybutton.style.display = "none";
    }
}

// When the user clicks on the button, scroll to the top of the document
function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}




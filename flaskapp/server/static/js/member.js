// Selector
const counters = document.querySelectorAll('.counter');
// Main function
for(let n of counters) {
const updateCount = () => {
    const target = + n.getAttribute('data-target');
    const count = + n.innerText;
    const speed = 5000000; // change animation speed here
    const inc = target / speed; 
    if(count < target) {
    n.innerText = Math.ceil(count + inc);
    setTimeout(updateCount, 1);
    } else {
    n.innerText = target;
    }
}
updateCount();
}       


//Get the button
var mybutton = document.getElementById("myBtn");

// When the user scrolls down 20px from the top of the document, show the button
window.onscroll = function() {scrollFunction()};

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

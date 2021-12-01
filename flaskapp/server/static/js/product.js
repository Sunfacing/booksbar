function render(productList){
    var table_of_content = document.createElement('p');
    table_of_content.innerHTML = productList.table_of_content
    document.getElementById('table_of_content').append(table_of_content);
   
    var description = document.createElement('span');
    description.innerHTML = '<p style="white-space: pre-line;">' + productList.description + '</p>'
    document.getElementById('description').append(description);

    var author_intro = document.createElement('p');
    author_intro.innerHTML = productList.author_intro
    document.getElementById('author_intro').append(author_intro);
  };
        

  var slideIndex = 1;
  showSlides(slideIndex);
  
  function plusSlides(n) {
    showSlides(slideIndex += n);
  }
  
  function currentSlide(n) {
    showSlides(slideIndex = n);
  }
  
  function showSlides(n) {
    var i;
    var slides = document.getElementsByClassName("mySlides");
    var dots = document.getElementsByClassName("demo");
    var captionText = document.getElementById("caption");
    if (n > slides.length) {slideIndex = 1}
    if (n < 1) {slideIndex = slides.length}
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex-1].style.display = "block";
    dots[slideIndex-1].className += " active";
    captionText.innerHTML = dots[slideIndex-1].alt;
  }


  function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
  }
  
  function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
  }




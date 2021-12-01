
var loginButton = document.getElementById("loginButton");
var registerButton = document.getElementById("registerButton");

loginButton.onclick = function(){
    document.querySelector("#flipper").classList.toggle("flip");
}

registerButton.onclick = function(){
    document.querySelector("#flipper").classList.toggle("flip");
}

// Get the modal
var modal = document.getElementById('id01');

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
if (event.target == modal) {
    modal.style.display = "none";
}
}

function checker(result) {
            if (result.response == '登入成功' || result.response == '註冊成功' ) {
                document.getElementById('id01').style.display='none'
                Swal.fire('Welcome', result.response, 'success')
                location.reload()
            } else {
                document.getElementById('id01').style.display='none'
                Swal.fire('Oops..', result.response, 'error')
            }
        }

var loginBtn = document.getElementById('login')
loginBtn.addEventListener('click', (e) => {
    var e_mail = document.getElementById("loginMail").value;
    var password = document.getElementById("loginPwd").value;
    if ( e_mail != 0 && password != 0) {
    var api_member = "/api/login";
    const data = {email: e_mail, pwd: password}
    fetch(api_member, {method:"POST", headers: { Accept: "application/json"}, body: JSON.stringify(data)})
            .then(response => response.json())
            .then(checker)
}})


var registerBtn = document.getElementById('register')
registerBtn.addEventListener('click', (e) => {
    var e_mail = document.getElementById("registerMail").value;
    var password = document.getElementById("registerPwd").value;
    if ( e_mail != 0 && password != 0) {
    var api_member = "/api/register";
    const data = {email: e_mail, pwd: password}
    fetch(api_member, {method:'POST', headers: { Accept: 'application/json'}, body: JSON.stringify(data)})
            .then(response => response.json())
            .then(checker)
}})


if ( window.history.replaceState ) {
    window.history.replaceState( null, null, window.location.href );
}

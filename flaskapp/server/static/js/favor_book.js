
var tracker = document.getElementById('tracker')

let button_tag;
let icon_tag;
let status;
tracker.addEventListener('click', (e) => {
    if (e.target.tagName == 'I') {
    icon_tag = e.target
    button_tag = e.target.parentNode
    value = e.target.parentNode.value;
    } else if (e.target.tagName == 'BUTTON') {
    button_tag = e.target
    icon_tag = e.target.firstChild
    value = e.target.value;
    } else {
    value = 0;
    }
    if ( value != 0 && button_tag.className == 'btn btn-check row') {
        var api = "/api/favorite"+ value;
        fetch(api, {method:'DELETE'})
            .then(response => response.json())
            .then(set_favorite)
    } else if ( value != 0 ){
        var api = "/api/favorite"+ value;
        fetch(api, {method:'POST'})
            .then(response => response.json())
            .then(set_favorite)                            
    }

    }
)


function set_favorite(result) {
    if (result.message == 'added') {
        button_tag.className = button_tag.className.replace("btn-basic", "btn-check");
        icon_tag.style.color = "#ffffff"
    } else if ( result.message == 'cancelled') {
        button_tag.className = button_tag.className.replace("btn-check", "btn-basic");
        icon_tag.style.color = "#393d3f"                  
    } else {
        alert('請先登入')
        document.getElementById('id01').style.display='block'
    }
}

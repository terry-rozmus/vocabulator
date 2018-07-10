var check_str = ''
var post_timeout

// check if the browser supports the XMLHttpRequest object.
// If it does, create an XMLHttpRequest object, if not, create an ActiveXObject
var xhttp;
if (window.XMLHttpRequest) {
    xhttp = new XMLHttpRequest();
    } else {
    // code for IE6, IE5
    xhttp = new ActiveXObject("Microsoft.XMLHTTP");
}

// Get Cookie value
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Handler for resizing the main search box
var observe;
if (window.attachEvent) {
    observe = function (element, event, handler) {
        element.attachEvent('on'+event, handler);
    };
}
else {
    observe = function (element, event, handler) {
        element.addEventListener(event, handler, false);
    };
}

function delayedPostForm(post_delay_time) {
    delayed_post_object = setTimeout(postForm, post_delay_time);
}

// Initialisation procedures
$( document ).ready(function() {
    // call delayed post once to initialise
    delayedPostForm(100000);

    // Books Tree Initialisation
    $books_tree = $('#books_tree')
    // listen for event
    $books_tree
    .on('changed.jstree', function (e, data) {
        var i, j, r = [];
        checked_str = ''
        for(i = 0, j = data.selected.length; i < j; i++) {
             r.push(data.instance.get_node(data.selected[i]).id);
        }
        if (r != []) {
            checked_str = r.join('=on&') + '=on';
            if (document.getElementById('sentence').value != '') {
                clearTimeout(delayed_post_object);
                delayedPostForm(500);
            }
        }
        // Fade the numbers
        document.getElementById('results-frequency').className = 'results-frequency-loading';
    })
    .on('ready.jstree', function() {
        // restore the state of the tree
        /*books = document.getElementsByClassName('jstree-open');
        var i;
        for(i = 0, j = books.length; i < j; i++) {
            if ($books_tree.jstree('is_selected','#' + books[i].id) == true) {
                alert(books[i].id);
                $books_tree.jstree('close_node', '#' + books[i].id);
                alert(books[i].id);
            }
        };*/


        books = document.getElementsByClassName('folder');
        var i;
        for(i = 0, j = books.length; i < j; i++) {
            if ($books_tree.jstree('is_selected','#' + books[i].id) == true) {
                $books_tree.jstree('close_node', '#' + books[i].id);
            }
        };
    })
    // create the instance
    .jstree({"plugins": ["wholerow", "checkbox"]})



    // Setup Query Box Resize functions
    var text = document.getElementById('sentence');
    function resize () {
        text.style.height = 'auto';
        text.style.height = text.scrollHeight+'px';
        clearTimeout(delayed_post_object);
    }
    // 0-timeout to get the already changed text
    function searchTextChange() {
        document.getElementById('results-words').className = 'results-words-loading';
        document.getElementById('results-frequency').className = 'results-frequency-loading';
        window.setTimeout(resize, 0);
    }
    //observe(text, 'change',  searchTextChange);
    observe(text, 'cut',     searchTextChange);
    observe(text, 'paste',   searchTextChange);
    observe(text, 'drop',    searchTextChange);
    observe(text, 'keydown', searchTextChange);

    text.focus();
    text.select();
    resize();

    // Change the id of the books tree so the style can change
    document.getElementById('books_tree').id = 'js_books_tree';

    // Submitted post intervention function
    $('#query-form').on('submit', function(event){
        event.preventDefault();
        postForm();
    });
});

// Post search form
function postForm() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (xhttp.readyState == 4 && xhttp.status == 200) {
            document.getElementById('results').innerHTML = xhttp.responseText;
            document.getElementById('results-words').className = 'results-words';
            document.getElementById('results-frequency').className = 'results-frequency';
            document.getElementById('search-button').className = 'search-button';
        }
    };

    var query_str = 'csrfmiddlewaretoken=' + getCookie('csrftoken')
                    + '&sentence=' + document.getElementById('sentence').value
                    + '&' + checked_str
    xhttp.open("POST", "results/", true);
    xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    xhttp.send(query_str);

    // Show the search button loading animation
    document.getElementById('search-button').className = 'search-button-loading';
}


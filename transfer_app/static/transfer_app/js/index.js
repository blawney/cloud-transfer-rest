// function that retrieves the cookie with specified name. 
// Used to get the django-generated CSRF token for sending AJAX requests
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// function to print human-readable file size
function humanFileSize(bytes) {
    var thresh = 1024;
    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    var units = ['kB','MB','GB','TB','PB'];
    var u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1)+' '+units[u];
}

/* 
******************************************************
START Loading of dynamic resources: 
******************************************************
*/

var csrfToken = getCookie('csrftoken');

// Get the active resources for the download tab:
$.ajax({
    url:"/resources/?is_active=true",
    type:"GET",
    headers:{"X-CSRFToken": csrfToken},
    success:function(response){
        var tableBody = $("#download-table tbody");
        var markup = "";
        for(var i=0; i<response.length; i++){
            var item = response[i];
            var size = humanFileSize(item['size']);
            var split_str = item['path'].split("/");
            var filename = split_str[split_str.length-1];
            markup += `<tr>
                      <td><input type="checkbox" target="${item['id']}"/></td>
                      <td>${filename}</td>
                      <td>${size}</td>
                    </tr>`;
        }
        tableBody.append(markup); 
    },
    error:function(){
        console.log('error!');
    }
});

function parseDateString(s){
    // string is formatted like:
    //  YYYY-MM-DDTHH:MM:SS.XXXXXXZ
    var contents = s.split("T");
    
}


function showDetail(pk){
    console.log(history[pk]);
    var item = history[pk];
    var split_str = item['resource']['path'].split("/");
    var filename = split_str[split_str.length-1];
    var startTime = item['start_time'];
    var success = item['success'];
    var finishTime = "-";
    if(success){
        finishTime = item['finish_time'];
    }
}

// get the history
var history = {}
$.ajax({
    url:"/transferred-resources/",
    type:"GET",
    headers:{"X-CSRFToken": csrfToken},
    success:function(response){
        var tableBody = $("#history-table tbody");
        var markup = "";
        for(var i=0; i<response.length; i++){
            var item = response[i];
            var pk = item['id'];
            history[pk] = item;
            var split_str = item['resource']['path'].split("/");
            var filename = split_str[split_str.length-1];
            markup += `<tr>
                      <td>${filename}</td>
                      <td><span class="detail-loader" detail-key="${pk}">View</span></td>
                    </tr>`;
        }
        tableBody.append(markup);

        $(".detail-loader").click(function(e){
            e.preventDefault();
            var targetedDetail = $(this).attr("detail-key");
            console.log("Show detail for " + targetedDetail);
            showDetail(targetedDetail);
        });
    },
    error:function(){
        console.log('error!');
    }
});



/* 
******************************************************
END Loading of dynamic resources
******************************************************
*/



/* 
******************************************************
START Dropbox JS 
******************************************************
*/

var options = {

    // Required. Called when a user selects an item in the Chooser.
    success: function(files) {
        alert("Here's the file link: " + files[0].link)
    },

    // Optional. Called when the user closes the dialog without selecting a file
    // and does not include any parameters.
    cancel: function() {

    },

    // Optional. "preview" (default) is a preview link to the document for sharing,
    // "direct" is an expiring link to download the contents of the file. For more
    // information about link types, see Link types below.
    linkType: "direct",

    // Optional. A value of false (default) limits selection to a single file, while
    // true enables multiple file selection.
    multiselect: true,
};

$("#dropbox-upload").click(function(e){
    Dropbox.choose(options);
});

/* 
******************************************************
END Dropbox JS 
******************************************************
*/




/*
******************************************************
 START Google Drive JS 
******************************************************
*/

// The Browser API key obtained from the Google API Console.
// Replace with your own Browser API key, or your own key.
var developerKey = 'AIzaSyClJS75QXASJLLmb5dq8VPc0gjAusGfGnE';

// The Client ID obtained from the Google API Console. Replace with your own Client ID.
var clientId = "926067285135-erhkvspo559gq4gi6o9bnh8bf4n2njrq.apps.googleusercontent.com"

// Replace with your own project number from console.developers.google.com.
// See "Project number" under "IAM & Admin" > "Settings"
var appId = "926067285135";

// Scope to use to access user's Drive items.
var scope = ['https://www.googleapis.com/auth/drive'];

var pickerApiLoaded = false;
var oauthToken;

// Use the Google API Loader script to load the google.picker script.
function loadPicker() {
    console.log('load picker!!');
    gapi.load('auth', {'callback': onAuthApiLoad});
    gapi.load('picker', {'callback': onPickerApiLoad});
}

function onAuthApiLoad() {
    window.gapi.auth.authorize(
        {
            'client_id': clientId,
            'scope': scope,
            'immediate': false
        },
        handleAuthResult
    );
}

function onPickerApiLoad() {
    console.log('in OnPickerAPILoad');
    pickerApiLoaded = true;
    createPicker();
}

function handleAuthResult(authResult) {
    console.log('handling auth ersults');
    console.log(authResult);
    if (authResult && !authResult.error) {
        oauthToken = authResult.access_token;
        createPicker();
    }
}

// Create and render a Picker object for searching images.
function createPicker() {
    if (pickerApiLoaded && oauthToken) {

        // view all of Drive
        var view = new google.picker.View(google.picker.ViewId.DOCS);
        var picker = new google.picker.PickerBuilder()
            .enableFeature(google.picker.Feature.NAV_HIDDEN)
            .enableFeature(google.picker.Feature.MULTISELECT_ENABLED)
            .setAppId(appId)
            .setOAuthToken(oauthToken)
            .addView(view)
            .setDeveloperKey(developerKey)
            .setCallback(pickerCallback)
            .build();
        console.log('going to make visible');
        picker.setVisible(true);
    }
}

// A simple callback implementation.
function pickerCallback(data) {
if (data.action == google.picker.Action.PICKED) {
        var fileId = data.docs[0].id;
        alert('The user selected: ' + fileId);
    }
}

/* 
******************************************************
END Google Drive JS
******************************************************
 */




$(".section-chooser").click(function(){
    // remove class from siblings:
    var sibs = $(this).siblings();
    for(var i=0; i<sibs.length; i++){
        console.log(sibs[i]);
        $(sibs[i]).removeClass("selected");
    }
    // add selected class to this
    $(this).addClass("selected");

    // make some adjustments to borders around the tabs
    if ($(this).is(":first-child")){
        $(this).addClass("first-tab");
    }
     if ($(this).is(":last-child")){
        $(this).addClass("last-tab");
    }

    //hide other content:
    $(".subcontent").hide();

    // show the content:
    var content_target = $(this).attr("content-target");
    var element = $("#" + content_target);
    $(element).toggle();
})

$(".select-all-checkbox").click(function(){
    var targetedTable = $(this).attr("table-target");
    var inputs = $("#" + targetedTable).find("input");

    console.log(targetedTable);
    if ($(this).prop("checked") == true){
        console.log('was checked');
        $(inputs).each(function(number, el){
            console.log(el);
            $(el).prop("checked", true);
        });
    }else{
        console.log('Not checked!');
        $(inputs).each(function(number, el){
            console.log(el);
            $(el).prop("checked", false);
        });                }

});

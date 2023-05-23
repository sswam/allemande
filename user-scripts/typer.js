// ==UserScript==
// @name        Simulate typing
// @namespace   http://tampermonkey.net/
// @version     1.0
// @description Simulate user typing by pressing F3
// @include     *
// @require     https://code.jquery.com/jquery-3.6.0.min.js
// @require     https://code.jquery.com/ui/1.12.1/jquery-ui.min.js
// @grant       none
// ==/UserScript==

(function() {
    'use strict';
    // create dialog
    $("body").append('<div id="dialog" title="Input text" style="display:none;"><textarea id="textarea" rows="4" cols="50"></textarea></div>');
    $("#dialog").dialog({
        autoOpen: false,
        buttons: {
            "OK": function() {
                var text = $('#textarea').val();
                $(this).dialog("close");
                simulateTyping(text);
            },
            "Cancel": function() {
                $(this).dialog("close");
            }
        }
    });

    // capture F3 key press
    $(document).keydown(function(e) {
        if (e.key == "F3") {
            e.preventDefault();
            $("#textarea").val("");
            $("#dialog").dialog("open");
        }
    });

    function simulateTyping(text) {
        var focused = $(':focus');
        var i = 0;
        var timer = setInterval(function() {
            if (i < text.length) {
                focused.val(focused.val() + text.charAt(i));
                i++;
            } else {
                clearInterval(timer);
            }
        }, Math.random() * (600 - 200) + 200); // typing speed between 200ms and 600ms
    }
})();

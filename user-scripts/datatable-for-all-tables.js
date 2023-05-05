// ==UserScript==
// @name         DataTables for All Tables
// @namespace    https://ucm.dev
// @author       GPT-4 and Sam Watkins
// @match        *://*/*
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// @run-at       document-idle
// @license      MIT
// ==/UserScript==

// TODO this doesn't work yet, need to fix it!

console.log("DataTables for All Tables starting... 1.");

(function() {
    'use strict';

    // Load DataTables CSS
    GM_addStyle(`
        @import url('https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css');
    `);

    // Load jQuery if it's not already available
    function loadjQuery(callback) {
        if (typeof jQuery === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
            script.onload = () => callback(window.jQuery);
            document.head.appendChild(script);
        } else {
            callback(window.jQuery);
        }
    }

    // Load DataTables JS
    function loadDataTables(callback) {
        const script = document.createElement('script');
        script.src = 'https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js';
        script.onload = () => callback();
        document.head.appendChild(script);
    }

    // Initialize DataTables for all tables
    function initAllTables($) {
        $('table').each(function() {
            console.log("adding to table", this);
            $(this).DataTable();
        });
    }

  function observeMutations($) {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeName === 'TABLE' && !$(node).hasClass('dataTable')) {
                        $(node).DataTable();
                    } else {
                        const newTables = $(node).find('table:not(.dataTable)');
                        if (newTables.length > 0) {
                            newTables.each(function() {
                                $(this).DataTable();
                            });
                        }
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
  }
  
    // Main function to load dependencies and initialize DataTables
    function main() {
        console.log("DataTables for All Tables starting...");
        loadjQuery((jQuery) => {
            window.$ = jQuery;
            console.log("loaded jQuery", jQuery);
            loadDataTables(() => {
              console.log("loaded DataTables");
              initAllTables(jQuery);
            });
        });
    }

    main();
})();

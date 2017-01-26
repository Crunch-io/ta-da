/* globals $:true */

;(function(window) {
    'use strict';

    // ensure global namespace
    window.crunchIO = window.crunchIO || {};

    const document = window.document,
        Array = window.Array,
        Promise = window.Promise,
        console = window.console,
        utils = {};

    function loadScriptAsync(url) {
        var promise = new Promise(function(resolve, reject) {
            var script = document.createElement('script');
            script.src = url;

            script.addEventListener('load', function() {
                resolve(script);
            }, false);

            script.addEventListener('error', function() {
                reject(script);
            }, false);

            document.body.appendChild(script);
        });

        return promise;
    }
    utils.loadScriptAsync = loadScriptAsync;

    function loadScriptsAsync(urls) {
        return Promise.all(urls.map(function(url) {
            return loadScriptAsync(url);
        }))
    };
    utils.loadScriptsAsync = loadScriptsAsync;

    function loadTemplatesAsync() {
        function transformer(el) {
            var promise = new Promise(function(resolve, reject) {
                $(el).load(el.dataset['template'], function() {
                    resolve();
                });
            })

            return promise
        }

        const promises = [] = Array.prototype.map.call(
            document.querySelectorAll('[data-template]'), transformer)

        return Promise.all(promises);
    }
    utils.loadTemplatesAsync = loadTemplatesAsync;

    function testImage(url) {
        var imgPromise = new Promise(function(resolve, reject) {
            // Create the image
            var imgElement = document.createElement('img');

            // When image is loaded, resolve the promise
            imgElement.addEventListener('load', function imgOnLoad() {
                resolve(url);
            });

            // When there's an error during load, reject the promise
            imgElement.addEventListener('error', function imgOnError() {
                console.log('Source image was not found:', img);
                reject();
            });

            imgElement.src = url;
        });

        return imgPromise
    }
    utils.testImage = testImage;

    function getFaviconUrl(domain) {
        return 'http://www.google.com/s2/favicons?domain=' + domain
    }
    utils.getFaviconUrl = getFaviconUrl

    window.crunchIO.utils = utils;
}(window))

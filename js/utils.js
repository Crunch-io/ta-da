(function(window) {
    'use strict';

    var document = window.document;

    window.crunchIO.testImage = function(url) {
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

    window.crunchIO.getFaviconUrl = function(domain) {
        return 'http://www.google.com/s2/favicons?domain=' + domain
    }
}(window))
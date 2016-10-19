(function(window) {
    'use strict';

    window.crunchIO.testImage = function(url) {
        // Define the promise
        const imgPromise = new Promise(function(resolve, reject) {

            // Create the image
            const imgElement = new Image();

            // When image is loaded, resolve the promise
            imgElement.addEventListener('load', function imgOnLoad() {
                resolve(url);
            });

            // When there's an error during load, reject the promise
            imgElement.addEventListener('error', function imgOnError() {
                reject();
            });
        });

        return imgPromise
    }

    window.crunchIO.getFaviconUrl = function(domain) {
        return 'http://www.google.com/s2/favicons?domain=' + domain
    }
}(window))
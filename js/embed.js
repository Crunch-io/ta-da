;(function(window) {
    'use strict';

    // ensure global namespace
    window.crunchIO = window.crunchIO || {};

    const document = window.document,
        String = window.String,
        console = window.console;

    function processReferrerElement(refUrl) {
        const referrerEl = document.querySelector('#referrer-link')

        referrerEl.href = refUrl
        referrerEl.classList.toggle('hidden', !refUrl);

        if (!refUrl) {
            return
        }

        let imgEl = document.querySelector('#referrer-link-img'),
            indexes = [],
            startIndex = refUrl.indexOf('//'),
            endIndex,
            domain,
            faviconUrl

        startIndex += startIndex === -1 ? 0 : 2
        endIndex = refUrl.indexOf('/', startIndex)

        indexes[0] = startIndex

        if (endIndex > -1) {
            indexes[1] = endIndex
        }

        domain = String.prototype.substring.apply(refUrl, indexes)

        faviconUrl = window.crunchIO.utils.getFaviconUrl(domain)

        window.crunchIO.utils.testImage(faviconUrl).then(
            function fulfilled(img) {
                imgEl.src = faviconUrl;
            },

            function rejected(err) {
                imgEl.classList.add('hidden');
            }
        )

        document.querySelector('#referrer-link-text').innerText = refUrl
    };

    function initPage() {
        console.log('referrer:', document.referrer)
        //"//d27smwjmpxcjmb.cloudfront.net/test01/widget/index.html#/ds/bc101c5d832568b88ab44a9378915846/row/000028/column/000367"

        const iframe = document.querySelector('#embed'),
            search = window.location.search ?
                window.location.search.substr(1) : '',
            parts = search.split(/(?:\?|&)/),
            props = {},
            protocolRegExp = /^(http(s?):)?\/{2}/;

        parts.forEach(function(part) {
            const pair = part.split('=')

            if (!props.hasOwnProperty(pair[0])) {
                props[pair[0]] = pair[1]
            }
        });

        // Embed will receive the data url from the widget as an encoded param
        const dataUrl = decodeURIComponent(props.data);
        // Add protocol if needed
        const src = `${dataUrl.match(protocolRegExp) ? '' : 'http://'}${dataUrl}`;
        const refUrl = props.ref ? decodeURIComponent(props.ref) : '';

        iframe.setAttribute('src', src);

        console.log('refUrl:', refUrl)

        processReferrerElement(refUrl);

        console.log('dataUrl:', dataUrl)

        const boxId = dataUrl.match(/\/ds\/(\w+)\/?/)[1];

        document.getElementById('displayShareUrl').addEventListener('click', function(event) {
            const url = `https://dev.crunch.io/social/share/${boxId}?url=${window.location.href}`

            document.getElementById('shareUrl').value = url
            document.getElementById('sharePreview').setAttribute('src', url)
        });
    }
    window.crunchIO.initPage = initPage;
}(window))

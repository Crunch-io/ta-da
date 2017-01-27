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

    function getParamsFromUrl() {
        // Legacy url is plain, new url has encoded parts
        const query = (window.location.search + window.location.hash).substr(1)
        const parts = []

        return query.match(/((?![\?&](data|ref)=).)+/g).reduce((accum, part) => {
            const match = part.match(/^(\w+)=(.*)/)

            if (match) {
                accum[match[1]] = decodeURIComponent(match[2])
            }

            return accum
        }, {})
    }

    function initPage() {
        console.log('referrer:', document.referrer)

        const iframe = document.querySelector('#embed')
        const params = getParamsFromUrl()
        const protocolRegExp = /^(http(s?):)?\/{2}/;
        // Embed will receive the data url from the widget as an encoded param
        const dataUrl = params.data;
        // Add protocol if needed
        const src = `${dataUrl.match(protocolRegExp) ? '' : 'http://'}${dataUrl}`;
        const refUrl = params.ref ? params.ref : '';

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

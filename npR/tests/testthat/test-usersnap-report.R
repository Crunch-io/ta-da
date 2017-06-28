context("Usersnap")

with_mock_API({
    test_that("userSnapChat when there is data", {
        expect_POST(userSnapChat(start="2017-06-19", end="2017-06-25"),
            npR:::slack_url,
            ## Here's the beginning
            '{"attachments":[{"pretext":"Usersnaps from 2017-06-19 to ',
            '2017-06-25","fallback":"UserSnapchat warning","fields":[',
            '{"title":"New open reports","value":7,"short":true},',
            '{"title":"New reports already closed","value":0,"short":true},',
            '{"title":"3 reports being handled:","value":"* ',
            '<https://usersnap.com/a/#/crunch-io/p/alpha-and-beta/658|I\'m ',
            'encountering a problem in the Graph view within Tables and Graphs ',
            'when [...]>')
    })
})

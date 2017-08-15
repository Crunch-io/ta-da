context("supportReport")

test_that("md_linkify", {
    expect_identical(slack_linkify(c("a", "b"), c("A", "B")),
        c("<a|A>", "<b|B>"))
    expect_identical(slack_linkify(data.frame()$a, data.frame()$b),
        character(0))
})

with_mock_API({
    test_that("supportReport when there is data", {
        expect_POST(supportReport("-7days..today"),
            npR:::slack_url,
            ## Here's the beginning
            '{"attachments":[{"pretext":"Date range: -7days..today",',
            '"fallback":"Pivotal Tracker Support Report: warning","fields":[',
            '{"title":"New active tickets","value":11,"short":true},',
            '{"title":"Net tickets","value":6,"short":true},',
            '{"title":"5 accepted tickets",')
    })

    test_that("supportReport when there is no data", {
        expect_POST(supportReport("yesterday"),
            npR:::slack_url,
            '{"attachments":[{"pretext":"Date range: yesterday",',
            '"fallback":"Pivotal Tracker Support Report: good","fields":[',
            '{"title":"New active tickets","value":0,"short":true},',
            '{"title":"Net tickets","value":0,"short":true}],"color":"good"}],',
            '"channel":"@npr","icon_emoji":":ambulance:",',
            '"username":"Pivotal Tracker Support Report"}')
    })
})

context("Sending to slack")

without_internet({
    test_that("slack sends a POST request", {
        expect_POST(slack(channel="systems"),
            slack_url,
            '{"channel":"#systems","parse":"full"}')
    })

    test_that("with_slack_errors handler", {
        expect_POST(with_slack_errors(stop("An error!")),
            slack_url,
            '{"channel":"#systems","username":"jenkins","icon_emoji":":interrobang:","text":"Error in `stop(\\"An error!\\")`: An error!","parse":"full"}')
    })
})

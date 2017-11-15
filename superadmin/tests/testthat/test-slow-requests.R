context("Slow Requests")

public({
    with_mock_API({
        test_that("getSlowRequests", {
            s <- getSlowRequests(threshold=119, limit=10)
            expect_length(s, 10)
            expect_output(print(s[[1]]),
"139.91 seconds @ 2017-11-14T15:51:38
GET /datasets/a2250e623c2a40d988ab7221d078034f/table/?limit=0
User: davide.contu@yougov.com
Dataset: YouGov/Economist Weekly Survey #235

                               pct   total count     max
zz9d.factory.load_version_lock 116 139.910     1 139.910
                               100 120.114     1 120.114
api.handler                    100 120.106     1 120.106
zz9                            100 120.102     1 120.102
...", fixed=TRUE)
        })
    })
})

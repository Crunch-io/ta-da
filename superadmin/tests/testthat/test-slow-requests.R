context("Slow Requests")

public({
    with_mock_API({
        test_that("getSlowRequests", {
            s <- getSlowRequests(threshold=119, limit=10)
            expect_length(s, 10)
            expect_output(print(s[[1]]),
"120.114 seconds @ 2017-11-14T15:51:38
GET /datasets/3d33d08f1b8742fd80020e7677cfcd02/table/?limit=0
User: davide.contu@yougov.com

                               pct   total count     max
zz9d.factory.load_version_lock 116 139.910     1 139.910
                               100 120.114     1 120.114
api.handler                    100 120.106     1 120.106
zz9                            100 120.102     1 120.102
...", fixed=TRUE)
        })
    })
})

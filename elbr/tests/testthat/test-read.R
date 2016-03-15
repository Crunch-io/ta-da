context("read.elb")

public({
    test_that("read.elb reads a log file", {
        df <- read.elb("example.log")
        expect_identical(dim(df), c(96L, 15L))
        expect_identical(df$backend_processing_time[1], 0.0181)
    })

    test_that("cleanLog makes the right shape", {
        df <- cleanLog(read.elb("example.log"))
        expect_identical(dim(df), c(96L, 8L))
        expect_identical(names(df), c("timestamp", "request_verb",
            "request_url", "status_code", "received_bytes", "sent_bytes",
            "response_time", "user_agent"))
        expect_output(print(df$timestamp[1]), "2015-12-31 19:07:25 UTC")
        expect_identical(df$response_time[2], 0.000023 + 0.020097 + 0.000018)
    })
})

context("read.elb")

public({
    df <- read.elb("example.log")
    test_that("read.elb reads a log file", {
        expect_identical(dim(df), c(97L, 15L))
        expect_identical(df$backend_processing_time[1], 0.0181)
    })

    df <- cleanLog(df)
    test_that("cleanLog makes the right shape", {
        expect_identical(dim(df), c(97L, 8L))
        expect_identical(names(df), c("timestamp", "request_verb",
            "request_url", "status_code", "received_bytes", "sent_bytes",
            "response_time", "user_agent"))
    })
    test_that("cleanLog computes values correctly", {
        expect_output(print(df$timestamp[1]), "2015-12-31 19:07:25 UTC")
        expect_identical(df$response_time[2], 0.000023 + 0.020097 + 0.000018)
    })
    test_that("504s have NA response time", {
        expect_identical(df$status_code[30], 504L)
        expect_true(is.na(df$response_time[30]))
    })

    snake <- read_elb("example.log")
    test_that("read_elb also reads a log file", {
        expect_identical(dim(snake), c(97L, 15L))
        expect_identical(snake$backend_processing_time[1], 0.0181)
    })
    test_that("read_elb with a problematic user-agent string", {
        expect_silent(df <- read_elb("example2.log"))
        expect_identical(ncol(df), 15L)
    })
})

context("read.elb")

public({
    snake <- read_elb("2017/12/31/example.log")
    test_that("read_elb also reads a log file", {
        expect_identical(dim(snake), c(97L, 15L))
        expect_identical(snake$backend_processing_time[1], 0.0181)
    })
    test_that("read_elb with a problematic user-agent string", {
        expect_silent(df <- read_elb("2018/02/03/example2.log"))
        expect_identical(dim(df), c(146L, 15L))
    })

    test_that("read_elb selecting columns", {
        df <- read_elb("2017/12/31/example.log", col_names=c("received_bytes", "user_agent", "GARBAGE"))
        expect_identical(names(df), c("received_bytes", "user_agent"))
        expect_true(is.numeric(df$received_bytes))
    })

    test_that("read_elb selecting no valid columns", {
        expect_error(read_elb("2017/12/31/example.log", col_names="GARBAGE"),
            "'arg' should be one of")
    })

    df <- cleanLog(snake)
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
})

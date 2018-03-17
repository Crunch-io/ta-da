context("read.elb")

public({
    snake <- read_elb("2017/12/31/example.log")
    test_that("read_elb also reads a log file", {
        expect_identical(dim(snake), c(97L, 15L))
        expect_identical(snake$backend_processing_time[1], 0.0181)
    })
    test_that("504s have NA response time", {
        expect_identical(snake$elb_status_code[30], 504L)
        expect_true(is.na(snake$backend_processing_time[30]))
    })
    test_that("read_elb with a problematic user-agent string", {
        expect_silent(df <- read_elb("2018/02/03/example2.log"))
        expect_identical(dim(df), c(146L, 15L))
    })

    test_that("read_elb selecting columns", {
        df <- read_elb("2017/12/31/example.log", columns=c("received_bytes", "user_agent", "GARBAGE"))
        expect_identical(names(df), c("received_bytes", "user_agent"))
        expect_true(is.numeric(df$received_bytes))
    })

    test_that("read_elb selecting no valid columns", {
        expect_error(read_elb("2017/12/31/example.log", columns="GARBAGE"),
            "'arg' should be one of")
    })

    df <- parse_request(snake$request)
    test_that("parse_request makes the right shape", {
        expect_identical(dim(df), c(97L, 3L))
        expect_identical(names(df),
            c("request_verb", "request_url", "request_protocol"))
        expect_identical(df$request_verb[1], "GET")
    })
})

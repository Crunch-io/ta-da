context("dplyr methods")

library(magrittr)

test_that("select, filter, then collect", {
    df <- ELBLog() %>%
        select(elb_status_code, user_agent) %>%
        filter(elb_status_code == 200) %>%
        collect()
    expect_identical(dim(df), c(230L, 2L))
})

test_that("filter only", {
    df <- ELBLog() %>%
        filter(elb_status_code == 504) %>%
        collect()
    expect_identical(dim(df), c(1L, 15L))
    expect_true(grepl("226bc5fcea8b45588a542879636edafe", df$request))
})

test_that("select twice, with date range", {
    df <- ELBLog("2017-11-15", "2018-01-01") %>%
        select(elb_status_code, user_agent) %>%
        select(elb_status_code) %>%
        collect()
    expect_identical(dim(df), c(97L, 1L))
})

test_that("selected columns are in the requested order", {
    df <- ELBLog() %>%
        select(elb_status_code, timestamp) %>%
        collect()
    expect_identical(names(df), c("elb_status_code", "timestamp"))
})

context("dplyr methods")

library(magrittr)

test_that("select, filter, then collect", {
    elb <- ELBLog()
    elb$files <- c("example.log", "example2.log")
    df <- elb %>%
        select(elb_status_code, user_agent) %>%
        filter(elb_status_code == 200) %>%
        collect()
    expect_identical(dim(df), c(230L, 2L))
})

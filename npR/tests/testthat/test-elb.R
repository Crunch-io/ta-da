context("ELB report")

options(elbr.dir="./elb", mc.cores=1)

test_that("elbSummary", {
    ## TODO: assert
    expect_output(print(elbSummary(1, "2016-01-02", send=FALSE)))
})

test_that("pretty", {
    expect_identical(pretty(1234.123123), "1,234")
    expect_identical(pretty(1234.123123, 2), "1,234.12")
    expect_identical(pretty(1234.1, 2), "1,234.10")
    expect_identical(pretty(0.000082123, 4), "<0.0001")
    expect_identical(pretty(0.000082123, 5), "0.00008")
})

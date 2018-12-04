context("ELB report")

options(elbr.dir="./elb", mc.cores=1)

test_that("elbSummary", {
    ## TODO: assert
    expect_output(print(elbSummary(1, "2016-01-02", send=FALSE)))
})

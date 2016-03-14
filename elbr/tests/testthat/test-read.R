context("read.elb")

public({
    test_that("read.elb reads a log file", {
        df <- read.elb("example.log")
        expect_identical(dim(df), c(96L, 15L))
        expect_identical(df$backend_processing_time[1], 0.0181)
    })
})

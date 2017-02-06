context("Datasets")

public({
    with_mock_API({
        test_that("getDatasets gets datasets", {
            expect_is(getDatasets(), "data.frame")
        })
        test_that("getDatasets with a query", {
            df2 <- getDatasets(dsid="a2250e623c2a40d988ab7221d078034f")
            expect_is(df2, "data.frame")
            expect_identical(dim(df2), c(1L, 8L))
        })
        test_that("getDatasets with no results found", {
            df3 <- getDatasets(email="NOMATCHES")
            expect_is(df3, "data.frame")
            expect_identical(dim(df3), c(0L, 8L))
        })
    })
})

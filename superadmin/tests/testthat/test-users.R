context("Users")

public({
    with_mock_API({
        test_that("getUsers gets users", {
            expect_is(getUsers(), "data.frame")
        })
        test_that("getUsers with a query", {
            expect_is(getUsers("rees"), "data.frame")
        })
        test_that("getUsers with no results found", {
            df3 <- getUsers("NOMATCHES")
            expect_is(df3, "data.frame")
            expect_identical(dim(df3), c(0L, 4L))
        })
    })
})

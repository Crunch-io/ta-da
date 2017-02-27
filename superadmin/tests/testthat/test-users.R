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

        test_that("getUser by id", {
            u <- getUser("4091a7")
            expect_identical(u$user$id, "4091a7")
        })

        test_that("featureFlags", {
            u <- getUser("4091a7")
            expect_identical(featureFlags(u), list(projects=TRUE))
            expect_POST(featureFlags(u)$something_else <- TRUE,
                "mockapi/users/4091a7/edit")
        })
    })
})

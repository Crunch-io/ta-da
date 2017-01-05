context("URLs")

test_that("superadminURL concatenates correctly", {
    with_options(superadmin.api="http://localhost:28081/", expr={
        expect_identical(superadminURL("/users"), "http://localhost:28081/users")
    })
})

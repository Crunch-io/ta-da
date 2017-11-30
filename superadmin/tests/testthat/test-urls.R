context("URLs")

test_that("superadminURL concatenates correctly", {
    expect_identical(superadminURL("/users"), "http://localhost:28081/users")
    expect_identical(superadminURL("users"), "http://localhost:28081/users")
})

context("Reading the auth cookie")

test_that("setToken returns correctly", {
    expect_true(setToken("token=123"))
    expect_true(setToken("foo=bar; token=123; more=stuff"))
    expect_false(setToken(NULL))
    expect_false(setToken("asdf"))
})
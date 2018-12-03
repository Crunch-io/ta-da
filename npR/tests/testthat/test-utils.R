context("Utilities")

test_that("ellipsize_middle", {
    em <- ellipsize_middle # For brevity
    x <- "asdfghjkl;"
    expect_identical(em(x, 10), x)
    expect_identical(em(x, 100), x)
    expect_identical(em(x, 9), "asd...kl;")
    expect_identical(em(x, 8), "asd...l;")
    expect_identical(em(x, 7), "as...l;")
})

context("Comment reading/parsing")

comms <- readRDS("comments.rds")

test_that("parse_comments is right shape, handles date prefixes", {
    parsed <- parse_comments(comms)
    expect_equal(dim(parsed), c(5, 2))
    expect_false(any(vapply(parsed$comments,
        function (x) any(is.na(x$date)), logical(1))))
    expect_false(any(vapply(parsed$comments,
        function (x) any(startsWith("2018", x$comment)), logical(1))))
})

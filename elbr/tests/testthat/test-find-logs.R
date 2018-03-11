context("Finding log files")

test_that("find_log_files: default is all log files in dir", {
    expect_identical(basename(find_log_files()), c("example.log", "example2.log"))
})

test_that("find_log_files: single date", {
    expect_identical(basename(find_log_files("2017-12-31")), "example.log")
})

test_that("find_log_files: date range", {
    expect_identical(basename(find_log_files("2017-12-12", "2018-02-04")),
        c("example.log", "example2.log"))
})

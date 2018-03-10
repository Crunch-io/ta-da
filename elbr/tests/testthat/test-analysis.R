context("Analysis")

test_that("sumTables", {
    x <- c(1, 3, 3, 3, 3, 4, 7)
    y <- c(2, 2, 2, 2, 4)
    z <- c(7, 1, 5, 5, 5)
    tbls <- list(table(x), table(y), table(z))
    expect_equal(sumTables(tbls), table(c(x, y, z)))
})

test_that("analyzeELB reads and binds if returning data.frame", {
    df <- analyzeELB(function (x) dplyr::select(x, received_bytes, user_agent))
    expect_identical(dim(df), c(97L + 146L, 2L))
})

test_that("analyzeELB can return the full data.frame", {
    df <- analyzeELB(force, select_vars=FALSE)
    expect_identical(dim(df), c(97L + 146L, 15L))
})

test_that("analyzeELB function mapping", {
    expect_equal(analyzeELB(function (df) {
            list(
                n=nrow(df),
                status_table=table(df$elb_status_code),
                response_size_max=max(df$sent_bytes)#,
                # TODO: mean() needs to be smarter about NAs
                #response_time_mean=mean(df$request_processing_time + df$backend_processing_time + df$response_processing_time, na.rm=TRUE)
            )
        }),
        list(
            n=97L + 146L,
            status_table=structure(
                c(230L, 1L, 4L, 2L, 3L, 2L, 1L),
                .Dim = 7L,
                .Dimnames = structure(
                    list(c("200", "201", "204", "301", "304", "404", "504")),
                    .Names = ""
                ),
                class = "table"
            ),
            response_size_max=58637L#,
            #response_time_mean=0.05812746
        ),
        tolerance=0.000001
    )
})

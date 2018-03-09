context("Analysis")

public({
    logs <- cleanLog(read_elb("example.log"))
    test_that("summarizeLog", {
        print(summarizeLog(logs))
    })

    test_that("summarizeLog byRollup", {
        print(byRollup(logs, "day"))
        print(byRollup(logs, "hour"))
    })
})

test_that("sumTables", {
    x <- c(1, 3, 3, 3, 3, 4, 7)
    y <- c(2, 2, 2, 2, 4)
    z <- c(7, 1, 5, 5, 5)
    tbls <- list(table(x), table(y), table(z))
    expect_equal(sumTables(tbls), table(c(x, y, z)))
})

test_that("analyzeELB", {
    files <- c("example.log", "example2.log")
    print(analyzeELB(function (df) {
        list(
            n=nrow(df),
            status_table=table(df$elb_status_code),
            response_size_max=max(df$sent_bytes),
            response_time_mean=mean(Reduce("+", df[grep("processing_time", names(df))]))
        )
    }, files=files))
})

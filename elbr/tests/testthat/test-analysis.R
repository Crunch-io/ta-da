context("Analysis")

public({
    logs <- cleanLog(read.elb("example.log"))
    test_that("summarizeLog", {
        print(summarizeLog(logs))
    })

    test_that("summarizeLog byRollup", {
        print(byRollup(logs, "day"))
        print(byRollup(logs, "hour"))
    })
})

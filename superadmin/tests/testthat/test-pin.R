context("Pinning and unpinning")

public({
    url <- "https://app.crunch.io/api/datasets/0fb1f66743a9407c9b4684d5291cb691/"
    id <- "0fb1f66743a9407c9b4684d5291cb691"
    without_internet({
        test_that("Pin makes the right request with a URL", {
            expect_POST(pin(url),
                "http://localhost:28081/datasets/pin?dsid=0fb1f66743a9407c9b4684d5291cb691")
        })
        test_that("Pin makes the right request with an id", {
            expect_POST(pin(id),
                "http://localhost:28081/datasets/pin?dsid=0fb1f66743a9407c9b4684d5291cb691")
        })
        test_that("Likewise with unpin", {
            expect_POST(unpin(url),
                "http://localhost:28081/datasets/unpin?dsid=0fb1f66743a9407c9b4684d5291cb691")
            expect_POST(unpin(id),
                "http://localhost:28081/datasets/unpin?dsid=0fb1f66743a9407c9b4684d5291cb691")
        })
    })
})

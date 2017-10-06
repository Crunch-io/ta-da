context("summarize504s")

with_mock(
    `superadmin::getDatasets`=function (dsid) {
        list(name=list(
            a159d0c4e26fef8ea371a2d9338ceb91="foo",
            b159d0c4e26fef8ea371a2d9338ceb91="bar"
        )[[dsid]])
    },
    test_that("We get table with dataset names", {
        urls <- c("/datasets/a159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/b159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/b159d0c4e26fef8ea371a2d9338ceb91/")
        expect_equal(tablulateDatasetsByName(urls),
            structure(list(
                timeouts = 2:1,
                name = c("bar", "foo")),
                row.names = c("b159d0c4e26fef8ea371a2d9338ceb91", "a159d0c4e26fef8ea371a2d9338ceb91"),
            class = "data.frame"))
    })
)

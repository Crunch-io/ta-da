context("summarize504s")

with_mock(
    `superadmin::getDatasets`=function (dsid) {
        list(name=list(
            a159d0c4e26fef8ea371a2d9338ceb91="foo ELB summary for November 26 to December 02",
            b159d0c4e26fef8ea371a2d9338ceb91="bar",
            c159d0c4e26fef8ea371a2d9338ceb91="baz",
            d159d0c4e26fef8ea371a2d9338ceb91="ds1",
            e159d0c4e26fef8ea371a2d9338ceb91="ds4"
        )[[dsid]])
    }, {
        urls <- c("/datasets/a159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/b159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/b159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/c159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/d159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/a159d0c4e26fef8ea371a2d9338ceb91/",
                "/datasets/b159d0c4e26fef8ea371a2d9338ceb91/")
        test_that("We get table with dataset names (ellipsized)", {
            expect_equal(tablulateDatasetsByName(urls),
                structure(list(
                    N = c(3, 2, 1, 1),
                    name = c("bar", "foo ELB summary f...6 to December 02", "baz", "ds1")),
                    row.names = c("b159d0c4e26fef8ea371a2d9338ceb91", "a159d0c4e26fef8ea371a2d9338ceb91", "c159d0c4e26fef8ea371a2d9338ceb91", "d159d0c4e26fef8ea371a2d9338ceb91"),
                class = "data.frame")
            )
        })
        test_that("We truncate the table", {
            expect_equal(tablulateDatasetsByName(urls, rows=3),
                structure(list(
                    N = c(3, 2, 2),
                    name = c("bar", "foo ELB summary f...6 to December 02", "[2 others]")),
                    row.names = c("b159d0c4e26fef8ea371a2d9338ceb91", "a159d0c4e26fef8ea371a2d9338ceb91", "and"),
                class = "data.frame"))
        })
    }
)

urls <- c("https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/variables/?nosubvars=1&relative=on",
"https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/variables/0000001XX/",
"https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/batches/",
"https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/batches/1/",
"https://beta.crunch.io:443/api/datasets/4b4f77ef52df4e32891ebe85c7723477/batches/",
"https://beta.crunch.io:443/api/datasets/aa11f912d45e4a45b336576e036f3420/cube/?query=%7B%22dimensions%22:%5B%7B%22function%22:%22selected_array%22",
"https://beta.crunch.io:443/api/datasets/aa11f912d45e4a45b336576e036f3420/cube/query=%7B%22dimensions%22:%5B%7B%22function%22:%22selected_array%22",
"https://beta.crunch.io:443/api/datasets/aa11f912d45e4a45b336576e036f3420/cube/query=%7B%22dimensions%22:%5B%7B%22function%22:%22selected_array%22/12345/",
"https://beta.crunch.io:443/api/datasets/",
"https://beta.crunch.io:443/api/datasets/https://beta.crunch.io/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/",
"https://beta.crunch.io:443/api/datasets/2159d0c4e26f4f8ea871a2d0338ceb91/permissions/",
"https://app.crunch.io/api/progress/tabbook%3A2aa29ff38fd9ab380c77744335d0607b/",
"https://app.crunch.io:443/dataset/4b4f77ef52df4e32891ebe85c7723477/filter/edit/eyJhcHBTdGF0ZVN0b3JlIjp0cnVlLCJhbmFseXplIjp7fSwidmFyaWFibGVzTmF2aWdhdG9yIjp7Iml0ZW0iOiIvMDAzNzc3LyJ9fQ=="
)

test_that("standardizeURLs", {
    expect_identical(standardizeURLs(urls),
        c("/datasets/ID/variables/?QUERY",
          "/datasets/ID/variables/ID/",
          "/datasets/ID/batches/",
          "/datasets/ID/batches/ID/",
          "/datasets/ID/batches/",
          "/datasets/ID/cube/?QUERY",
          "/datasets/ID/cube/TOOLONG",
          "/datasets/ID/cube/TOOLONG/ID/",
          "/datasets/",
          "/datasets/PEBCAK",
          "/datasets/ID/permissions/",
          "/progress/tabbook/",
          "/dataset/ID/filter/edit/WHAAM"))
})

reqs <- data.frame(
    request_url=urls[1:5],
    request_verb=c("GET", "GET", "POST", "GET", "POST")
)

test_that("tabulatedRequests", {
    expect_identical(tabulatedRequests(reqs),
        data.frame(
            N=c(2, 1, 1, 1),
            row.names=c(
                "POST /datasets/ID/batches/",
                "GET /datasets/ID/batches/ID/",
                "GET /datasets/ID/variables/?QUERY",
                "GET /datasets/ID/variables/ID/"
            )
        )
    )
})

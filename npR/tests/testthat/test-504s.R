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

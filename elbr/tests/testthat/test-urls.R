context("URL parsing")

public({
    urls <- c("https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/variables/?nosubvars=1&relative=on",
    "https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/batches/",
    "https://beta.crunch.io:443/api/datasets/bca1e06094b24bb2a0e377ad2d96a3cd/batches/1/",
    "https://beta.crunch.io:443/api/datasets/4b4f77ef52df4e32891ebe85c7723477/batches/",
    "https://beta.crunch.io:443/api/datasets/aa11f912d45e4a45b336576e036f3420/cube/?query=%7B%22dimensions%22:%5B%7B%22function%22:%22selected_array%22",
    "https://beta.crunch.io:443/api/datasets/",
    "https://beta.crunch.io:443/api/datasets/2159d0c4e26f4f8ea871a2d0338ceb91/permissions/"
    )

    test_that("extractDatasetID", {
        expect_identical(extractDatasetID(urls),
            c("bca1e06094b24bb2a0e377ad2d96a3cd",
              "bca1e06094b24bb2a0e377ad2d96a3cd",
              "bca1e06094b24bb2a0e377ad2d96a3cd",
              "4b4f77ef52df4e32891ebe85c7723477",
              "aa11f912d45e4a45b336576e036f3420",
              NA,
              "2159d0c4e26f4f8ea871a2d0338ceb91"))
    })

    test_that("standardizeURLs", {
        expect_identical(standardizeURLs(urls),
            c("/datasets/ID/variables/?QUERY",
              "/datasets/ID/batches/",
              "/datasets/ID/batches/ID/",
              "/datasets/ID/batches/",
              "/datasets/ID/cube/?QUERY",
              "/datasets/",
              "/datasets/ID/permissions/"))
    })
})

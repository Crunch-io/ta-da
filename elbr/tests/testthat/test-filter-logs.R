context("Filtered log reading")

public({
    test_that("find504s finds it", {
        df <- find504s()
        expect_equal(nrow(df), 1)
        expect_true(grepl("226bc5fcea8b45588a542879636edafe", df$request))
    })
})

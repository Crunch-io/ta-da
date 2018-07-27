context("Pivotal-Trello links")

test_that("get_epics_from_desc", {
    descs <- c(
        "asd\n\nPivotal epic: epic one",
        "Pivotal epic: an epic, another one",
        "",
        "\n",
        "f\nPivotal epic: something\nmore text\n",
        "f\nPivotal epic: something\nPivotal epic: heres another\n"
    )
    expect_identical(get_epics_from_desc(descs), list(
        "epic one",
        c("an epic", "another one"),
        character(0),
        character(0),
        "something",
        c("something", "heres another")
    ))
    expect_identical(unlist(get_epics_from_desc(descs)),
        c("epic one", "an epic", "another one", "something", "something", "heres another"))
})

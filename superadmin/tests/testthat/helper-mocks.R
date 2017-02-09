mockURL <- function (path, host) {
    paste0("mockapi", path)
}

with_mock_API <- function (...) {
    with_mock(
        `superadmin:::superadminURL`=mockURL,
        httptest::with_mock_API(...)
    )
}

with_options <- function (..., expr) {
    oldopts <- options(...)
    on.exit(do.call(options, oldopts))
    eval.parent(expr)
}

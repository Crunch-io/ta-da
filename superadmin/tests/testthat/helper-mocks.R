mockURL <- function (path, host=getOption("superadmin.api")) {
    paste0(host, path)
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

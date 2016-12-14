## Mock backend for no connectivity
without_internet <- function (expr) {
    with_mock(
        `httr::GET`=function (url, ...) halt("GET ", addQuery(url, ...)),
        `httr::PUT`=function (url, body=NULL, ...) halt("PUT ", addQuery(url, ...), " ", body),
        `httr::PATCH`=function (url, body=NULL, ...) halt("PATCH ", addQuery(url, ...), " ", body),
        `httr::POST`=function (url, body=NULL, ...) halt("POST ", addQuery(url, ...), " ", body),
        `httr::DELETE`=function (url, ...) halt("DELETE ", addQuery(url, ...)),
        eval.parent(expr)
    )
}

addQuery <- function (url, ...) {
    q <- list(...)$query
    if (!is.null(q)) {
        url <- paste0(url, "?", httr:::compose_query(q))
    }
    return(url)
}

halt <- function (...) stop(..., call.=FALSE)

expect_mock_request <- function (object, ...) {
    ## With mock HTTP, POST/PUT/PATCH throw errors with their request info
    expect_error(object, paste0(...), fixed=TRUE)
}

expect_POST <- function (object, url, ...) {
    expect_mock_request(object, "POST ", url, " ", ...)
}

expect_PATCH <- function (object, url, ...) {
    expect_mock_request(object, "PATCH ", url, " ", ...)
}

expect_PUT <- function (object, url, ...) {
    expect_mock_request(object, "PUT ", url, " ", ...)
}

expect_DELETE <- function (object, url) {
    expect_mock_request(object, "DELETE ", url)
}

expect_no_request <- function (object, ...) {
    ## No request means no error thrown
    expect_error(object, NA)
}

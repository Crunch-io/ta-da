#' HTTP for superadmin
#'
#' These functions auto-tunnel to the superadmin host:port if you're not already
#' connected.
#'
#' @param ... Arguments passed to httr VERBs
#' @return Whatever those HTTP requests return.
#' @importFrom httpcache GET POST
#' @export
superGET <- function (...) {
    Call <- match.call()
    Call[[1]] <- as.name("GET")
    env <- parent.frame()
    retryWithNewTunnel(Call, env)
}

#' @rdname superGET
#' @export
superPOST <- function (...) {
    Call <- match.call()
    Call[[1]] <- as.name("POST")
    env <- parent.frame()
    retryWithNewTunnel(Call, env)
}

#' Construct a superadmin URL
#'
#' @param path character relative path
#' @param host character path that `path` is relative to
#' @return A valid URL.
#' @export
superadminURL <- function (path,
        host=paste0("http://localhost:", getOption("superadmin.local.port"))) {

    paste(host, path, sep=ifelse(substr(path, 1, 1) == "/", "", "/"))
}

retryWithNewTunnel <- function (call, envir) {
    tryCatch(eval(call, envir=envir), error=function (e) {
        if (grepl("curl", deparse(e$call))) {
            superConnect()
            eval(call, envir=envir)
        } else {
            stop(e)
        }
    })
}

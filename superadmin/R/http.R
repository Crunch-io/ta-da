superGET <- function (...) {
    Call <- match.call()
    Call[[1]] <- as.name("GET")
    env <- parent.frame()
    retryWithNewTunnel(Call, env)
}

superPOST <- function (...) {
    Call <- match.call()
    Call[[1]] <- as.name("POST")
    env <- parent.frame()
    retryWithNewTunnel(Call, env)
}

retryWithNewTunnel <- function (call, envir) {
    tryCatch(eval(call, envir=envir), error=function (e) {
        if (grepl("Couldn't connect", e$message)) {
            superConnect()
            eval(call, envir=envir)
        } else {
            stop(e)
        }
    })
}

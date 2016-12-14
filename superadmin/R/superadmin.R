.onAttach <- function (lib, pkgname="superadmin") {
    setIfNotAlready(
        superadmin.api="http://localhost:28081/"
    )
    invisible()
}

setIfNotAlready <- function (...) {
    newopts <- list(...)
    oldopts <- options()
    oldopts <- oldopts[intersect(names(newopts), names(oldopts))]
    newopts <- modifyList(newopts, oldopts)
    do.call(options, newopts)
    invisible(oldopts)
}

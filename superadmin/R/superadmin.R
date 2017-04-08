bye <- new.env() ## For the finalizer

.onAttach <- function (lib, pkgname="superadmin") {
    setIfNotAlready(
        superadmin.local.port=28081
    )

    reg.finalizer(bye, function (x) {
        ## Disconnect when R exits
        if (isTRUE(getOption("superadmin.is.connected"))) {
            superDisconnect()
        }
    }, onexit=TRUE)

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

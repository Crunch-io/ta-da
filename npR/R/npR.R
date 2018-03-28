# Here's a good place to put your top-level package documentation

.onLoad <- function (lib, pkgname="npR") {
    setIfNotAlready(
        elbr.dir="/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/"
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

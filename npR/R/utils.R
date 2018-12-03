ellipsize_middle <- function (str, n=40) {
    # Note: starting with scalar case, TODO generalize
    # TODO: handle edge cases
    size <- nchar(str)
    if (size > n) {
        allowed <- n - 3
        pre <- ceiling(allowed / 2)
        post <- floor(allowed / 2)
        str <- paste0(substr(str, 1, pre), "...", substr(str, size - post + 1, size))
    }
    return(str)
}

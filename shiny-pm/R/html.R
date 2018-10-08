ul <- function (..., data=NULL) {
    out <- tags$ul(...)
    if (is.list(data)) {
        out$children <- data
    }
    return(out)
}

li <- function (...) tags$li(...)

as.ul <- function (data, FUN, ...) {
    contents <- lapply(seq_len(nrow(data)),
        function (i) FUN(data[i, , drop=FALSE]))
    return(ul(
        data=lapply(contents, function (x) {
            if (!is.tag(x, "li")) {
                x <- li(x)
            }
            x
        }),
        ...
    ))
}

is.tag <- function (x, tag) {
    inherits(x, "shiny.tag") && x$name == tag
}

tag.append <- function (tag, ...) {
    tag$children <- c(tag$children, list(...))
    return(tag)
}

bold <- function (...) tags$b(...)

italics <- function (...) tags$i(...)

collapsable <- function (caption, content, ...) {
    tags$details(tags$summary(caption, ...), content)
}

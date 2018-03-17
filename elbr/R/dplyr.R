#' @export
ELBLog <- function (start_date=NULL, end_date=start_date, path=getOption("elbr.dir", ".")) {
    structure(list(
        select=list(),
        filter=list(),
        start_date=start_date,
        end_date=end_date,
        path=path
    ), class="ELBLog")
}

#' @importFrom dplyr select
#' @importFrom rlang quos
#' @export
select.ELBLog <- function (.data, ...) {
    .data$select <- c(.data$select, list(quos(...)))
    return(.data)
}

#' @importFrom dplyr filter
#' @export
filter.ELBLog <- function (.data, ...) {
    .data$filter <- c(.data$filter, list(quos(...)))
    return(.data)
}

#' @importFrom dplyr collect
#' @importFrom rlang !!!
#' @importFrom tidyselect vars_select
#' @export
collect.ELBLog <- function (.data) {
    return(bind_rows(map_elb(.data)))
}

map_elb <- function (.data, FUN=NULL, ...) {
    ## Read data from all files, following the select/filter instructions
    if (is.null(FUN)) {
        fn <- function (f) collect_one(f, vars=colnames, filter=.data$filter)
    } else {
        fn <- function (f) FUN(collect_one(f, vars=colnames, filter=.data$filter), ...)
    }

    colnames <- eval(formals(read_elb)[["columns"]])
    for (q in .data$select) {
        colnames <- vars_select(colnames, !!! q)
    }
    if (is.null(.data$files)) {
        ## is.null check is to be able to poke in select files
        .data$files <- find_log_files(.data$start_date, .data$end_date, .data$path)
    }
    ## To turn off parallel, set options(mc.cores=1); makes it call lapply
    dfs <- parallel::mclapply(.data$files, fn)
    return(dfs)
}

collect_one <- function (file, vars, filter) {
    df <- read_elb(file, columns=vars)
    for (f in filter) {
        df <- filter(df, !!! f)
    }
    return(df)
}

#' @importFrom dplyr summarise summarize
#' @export
summarise.ELBLog <- function (.data, ...) {
    ## TODO: map-then-reduce when possible
    return(summarise(collect(.data), ...))
}

summarize2 <- function (.data, ...) {
    fns <- lapply(quos(...), quo_get_function)
    if (all(unlist(fns)) %in% c("sum", "max", "min")) {
        ## We can aggregate these in pieces

    }
}

quo_get_function <- function (x) as.character(rlang::quo_get_expr(x)[[1]])

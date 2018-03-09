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
    colnames <- eval(formals(read_elb)[["col_names"]])
    for (q in .data$select) {
        colnames <- tidyselect::vars_select(colnames, !!! q)
    }
    if (is.null(.data$files)) {
        ## is.null check is to be able to poke in select files
        .data$files <- findLogFiles(.data$start_date, .data$end_date, path)
    }
    #parallel::mc
    dfs <- lapply(.data$files,
        function (f) collect_one(f, vars=colnames, filter=.data$filter))
    return(bind_rows(dfs))
}

collect_one <- function (file, vars, filter) {
    df <- read_elb(file, col_names=vars)
    for (f in filter) {
        df <- filter(df, !!! f)
    }
    return(df)
}

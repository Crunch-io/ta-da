parse_date <- function (x) as.Date(crunch:::from8601(x))

#' @importFrom lubridate wday wday<- year isoweek
get_week_range <- function (date) {
    if (wday(date) < 2) {
        # Sunday is wday 1, but we want that to be a part of _last_ week
        date <- date - 7
    }
    # Set wday to Monday
    wday(date) <- 2
    return(c(date, date + 6))
}

same_week <- function (x, date) {
    # x can be vector but date is scalar
    year(x) %in% year(date) & isoweek(x) %in% isoweek(date)
}

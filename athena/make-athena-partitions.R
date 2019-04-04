"PARTITION (year='2019',month='02',day='05') location 's3://accesslogs-eu-crunch-io/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2019/02/05'"

partition_statement <- function (date) {
    date <- format(date, "%Y/%m/%d")
    parts <- unlist(strsplit(date, "/", fixed=TRUE))
    part1 <- paste0("(year='", parts[1], "',month='", parts[2], "',day='", parts[3], "')")
    paste0(
        "  PARTITION ", part1,
        " location 's3://accesslogs-eu-crunch-io/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/", date, "'"
    )
}

dates <- seq(as.Date("2015-10-22"), as.Date("2019-02-05"), 1)
cat(sapply(dates, partition_statement), file="~/c/athena-partitions.sql")

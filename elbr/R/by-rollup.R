byRollup <- function (logdf, unit, FUN=summarizeLog) {
    dfs <- split(dfs, floor_time(logdf$timestamp, unit))
    do.call(rbind, lapply(dfs, FUN))
}

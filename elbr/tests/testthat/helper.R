Sys.setlocale("LC_COLLATE", "C") ## What CRAN does
set.seed(999)
options(elbr.dir=".")

public <- function (...) with(globalenv(), ...)

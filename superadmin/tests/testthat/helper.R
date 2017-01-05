Sys.setlocale("LC_COLLATE", "C") ## What CRAN does
set.seed(999)
options(
    warn=1,
    superadmin.api="mockapi"
)

public({
    source("helper-mocks.R")
})

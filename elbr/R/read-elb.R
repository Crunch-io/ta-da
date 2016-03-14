##' Load an ELB log file
##'
##' @param file A file name or connection. See \code{\link[utils]{read.table}}
##' @param stringsAsFactors The standard \code{data.frame} argument, but
##' defaulted to \code{TRUE}.
##' @return A \code{data.frame}.
##' @export
read.elb <- function (file, stringsAsFactors=FALSE, ...) {
    read.delim(file,
        sep=" ",
        header=FALSE,
        stringsAsFactors=stringsAsFactors,
        col.names=c("timestamp", "elb", "client_port", "backend_port",
                    "request_processing_time", "backend_processing_time",
                    "response_processing_time", "elb_status_code",
                    "backend_status_code", "received_bytes", "sent_bytes",
                    "request", "user_agent", "ssl_cipher", "ssl_protocol"),
        ...)
}

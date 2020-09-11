#' Connect and Disconnect to the Admin Server
#'
#' `superConnect` sets up an ssh tunnel. `superDisconnect` closes the tunnel.
#' You shouldn't need to call either directly: `superConnect` will be called
#' for you when you attempt to get a superadmin URL if the tunnel is not already
#' set up, and `superDisconnect` is called automatically on process exit.
#' @param host character, default is "eu" for production. Alternative is
#' "alpha"
#' @param local.port What port to use on your local host
#' @param remote.port What port the admin server is on
#' @return Whatever exit status that `system2` returns.
#' @export
superConnect <- function (host="eu",
                          local.port=getOption("superadmin.local.port"),
                          remote.port=8081) {

    message("Connecting...")
    cmd <- paste0("-A -f -N -L ", local.port, ":", findAdminHost(host),
        ":", remote.port, " centos@jump.eu.crint.net")
    out <- system_call("ssh", cmd)
    options(superadmin.is.connected=TRUE)
    invisible(out)
}

#' @rdname superConnect
#' @export
superDisconnect <- function (local.port=getOption("superadmin.local.port")) {
    message("Disconnecting...")
    cmd <- paste0('-f "ssh -A -f -N -L ', local.port, '"')
    out <- system_call("pkill", cmd)
    options(superadmin.is.connected=FALSE)
    invisible(out)
}

#' @importFrom utils head read.table
findAdminHost <- function (host="eu") {
    ## Hostnames are dynamic. Read from this table to find out the web server
    ## to connect to for superadmin access
    df <- loadHostTable("https://paster:youseeit@dev.crunch.io/ec2-hosts.txt")
    hosts <- df$Name[df$System == host &
                     df$State == "running" &
                     grepl("webservers", df$Ansible.Role)]
    if (length(hosts)) {
        ## Any of them should be fine
        return(head(hosts, 1))
    } else {
        stop("No running webserver found for ", host, call.=FALSE)
    }
}

loadHostTable <- function (url) {
    tab <- GET(url)
    read.table(textConnection(content(tab, "text", encoding="UTF-8")),
        sep="\t", header=1, fill=TRUE, stringsAsFactors=FALSE)
}

## For test mocking
system_call <- function (...) system2(...)

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
        ":", remote.port, " ec2-user@vpc-nat.eu.crunch.io")
    out <- system2("ssh", cmd)
    options(superadmin.is.connected=TRUE)
    invisible(out)
}

#' @rdname superConnect
#' @export
superDisconnect <- function (local.port=getOption("superadmin.local.port")) {
    message("Disconnecting...")
    cmd <- paste0('-f "ssh -A -f -N -L ', local.port, '"')
    out <- system2("pkill", cmd)
    options(superadmin.is.connected=FALSE)
    invisible(out)
}

#' @importFrom utils head read.table
findAdminHost <- function (host="eu") {
    ## Hostnames are dynamic. Read from this table to find out the web server
    ## to connect to for superadmin access
    df <- read.table("https://paster:youseeit@dev.crunch.io/ec2-hosts.txt",
        sep="\t", header=1, stringsAsFactors=FALSE)
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

#' Connect and Disconnect to the Admin Server
#'
#' `superConnect` sets up an ssh tunnel. `superDisconnect` closes the tunnel.
#' You shouldn't need to call either directly: `superConnect` will be called
#' for you when you attempt to get a superadmin URL if the tunnel is not already
#' set up, and `superDisconnect` is called automatically on process exit.
#' @param host.prefix character, default is "eu" for production. Alternative is
#' "alpha"
#' @param local.port What port to use on your local host
#' @param remote.port What port the admin server is on
#' @return Whatever exit status that `system2` returns.
#' @export
superConnect <- function (host.prefix="eu",
                          local.port=getOption("superadmin.local.port"),
                          remote.port=8081) {

    message("Connecting...")
    cmd <- paste0("-A -f -N -L ", local.port, ":", host.prefix,
        "-backend.priveu.crunch.io:", remote.port,
        " ec2-user@vpc-nat.eu.crunch.io")
    system2("ssh", cmd)
}

#' @rdname superConnect
#' @export
superDisconnect <- function (local.port=getOption("superadmin.local.port")) {
    message("Disconnecting...")
    cmd <- paste0('-f "ssh -A -f -N -L ', local.port, '"')
    system2("pkill", cmd)
}

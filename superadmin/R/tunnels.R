superConnect <- function (host.prefix="eu",
                          local.port=getOption("superadmin.local.port"),
                          remote.port=8081) {

    message("Connecting...")
    cmd <- paste0("-A -f -N -L ", local.port, ":", host.prefix,
        "-backend.priveu.crunch.io:", remote.port,
        " ec2-user@vpc-nat.eu.crunch.io")
    system2("ssh", cmd)
}

superDisconnect <- function (local.port=getOption("superadmin.local.port")) {
    message("Disconnecting...")
    cmd <- paste0('-f "ssh -A -f -N -L ', local.port, '"')
    system2("pkill", cmd)
}

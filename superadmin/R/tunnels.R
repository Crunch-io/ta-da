superConnect <- function (host.prefix="eu", local.port=28081, remote.port=8081) {
    cmd <- paste0("-A -f -N -L ", local.port, ":", host.prefix,
        "-backend.priveu.crunch.io:", remote.port,
        " ec2-user@vpc-nat.eu.crunch.io")
    system2("ssh", cmd)
}

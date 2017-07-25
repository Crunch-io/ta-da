context("Auto-tunneling")

suppressMessages(trace("loadHostTable", where=superGET, at=1, print=FALSE,
    tracer=quote({
            GET <- function (url, ...) readLines(basename(url))
            content <- function (x, ...) x
        })))
on.exit(suppressMessages(untrace("loadHostTable", where=superGET)))

test_that("findAdminHost", {
    expect_identical(findAdminHost("eu"),
        "eu-backend-216.priveu.crunch.io")
    expect_identical(findAdminHost("alpha"),
        "alpha-backend-39.priveu.crunch.io")
    expect_identical(findAdminHost("stable"),
        "stable-75.privaws.crunch.io")
    expect_error(findAdminHost("not-a-host"),
        "No running webserver found for not-a-host")
})

with_mock(
    `httr:::request_perform`=function (...) stop("Couldn't connect to server"),
    `base::system2`=function (command, args, ...) print(paste(command, args)), {

    test_that("superGET tries to connect and retry", {
        expect_output(
            expect_message(
                expect_error(
                    superGET("foo"),
                        "Couldn't connect to server"), ## This is the retry
                    "Connecting..."),
            "ssh -A -f -N -L 28081:eu-backend-216.priveu.crunch.io:8081 ec2-user@vpc-nat.eu.crunch.io")
    })
    test_that("superPOST tries to connect and retry", {
        expect_output(
            expect_message(
                expect_error(
                    superPOST("foo"),
                        "Couldn't connect to server"), ## This is the retry
                    "Connecting..."),
            "ssh")
    })

    test_that("superDisconnect", {
        expect_output(
            expect_message(superDisconnect(), "Disconnecting..."),
            "ssh")
    })
})

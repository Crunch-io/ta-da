context("Auto-tunneling")

with_mock(
    `httr:::request_perform`=function (...) stop("Couldn't connect to server"),
    `base::system2`=function (...) print("ssh"), {

    test_that("superGET tries to connect and retry", {
        expect_output(
            expect_message(
                expect_error(
                    superGET("foo"),
                        "Couldn't connect to server"), ## This is the retry
                    "Connecting..."),
            "ssh")
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
})

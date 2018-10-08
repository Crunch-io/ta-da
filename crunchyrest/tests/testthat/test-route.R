context("setRoute and handler functions")

test_that("buildHandlerFun returns a function", {
    expect_is(buildHandlerFun(quote(42)), "function")
})

fun <- buildHandlerFun(quote(list(value=42)))
fun2 <- buildHandlerFun(quote(stop("Kaboom")))
req <- new.env()

test_that("evaluating what buildHandlerFun returns: unauthenticated", {
    expect_identical(fun(new.env()), list(
        status=403L,
        headers=list('Content-Type' = 'application/json'),
        body=structure('{"message":"Not authorized"}', class="json")
    ))
    expect_silent(
        # If the code were to evaluate, it would error and print a message,
        # but it shouldn't evaluate because we aren't authenticated
        expect_identical(fun2(new.env()), list(
            status=403L,
            headers=list('Content-Type' = 'application/json'),
            body=structure('{"message":"Not authorized"}', class="json")
        ))
    )
})

req$HTTP_COOKIE <- "token=123"
test_that("evaluating what buildHandlerFun returns: authenticated", {
    expect_identical(fun(req), list(
        status=200L,
        headers=list('Content-Type' = 'application/json'),
        body=structure('{"value":42}', class="json")
    ))
})

test_that("errors are caught", {
    expect_output(
        expect_identical(fun2(req), list(
            status=500L,
            headers=list('Content-Type' = 'application/json'),
            body=structure('{"message":"Internal Server Error"}', class="json")
        )),
        "Kaboom"
    )
})

test_that("You can add headers and change the status", {
    fun3 <- buildHandlerFun(quote({
        status <- 202
        headers[["X-Something"]] <- "Special header"
        list(value=42)
    }))
    expect_identical(fun3(req), list(
        status=202,
        headers=list(
            "Content-Type" = "application/json",
            "X-Something" = "Special header"
        ),
        body=structure('{"value":42}', class="json")
    ))
})

test_that("setRoute sets", {
    # Generate a random path to mount, in case of interactive/repeat testing
    route <- paste0("/hackhack", rnorm(1))
    setRoute(route, {
        response_body <- list()
    })
    skip("TODO: assert something; this at least confirms that it doesn't error")
})

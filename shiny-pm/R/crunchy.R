# Simple version: use crunchyServer instead of shinyServer, and wrap your UI
# body that you want protected by auth inside of crunchyBody
# Options:
# * Specify a different "unauthenticated" page with crunchyPublicBody in your UI,
# after you specify crunchyBody
# * Add authorization requirements so that you require more than just being logged
# into crunch. Either specify an expression in the `authz` arg to crunchyServer,
# or setCrunchyAuthorization() outside of the server function
# * Add a different "unauthorized" page with crunchyUnauthorizedBody in your UI


crunchyBody <- function (...) {
    # This is called inside a ui function. It captures the body content you
    # request, stores it for lazy calling inside crunchyServer(), then returns
    # the div that crunchyServer() will write into
    crunchUIOutput(...)
    uiOutput("crunch_body")
}

crunchyPublicBody <- function (...) {
    crunchPublicUIOutput(...)
    return("")
}

crunchyUnauthorizedBody <- function (...) {
    crunchUnauthorizedUIOutput(...)
    return("")
}

crunchyServer <- function (func, authz=getOption("crunchy.authorization")) {
    shinyServer(function(input, output, session) {
        public_ui <- getOption("crunchy.body.public", crunchyDefaultPublicUI)
        output$crunch_body <- renderUI({
            # First, check whether this user is authenticated.
            #
            # Note that this doesn't check the server, just for the existence of
            # a *.crunch.io token. Generally good enough, and fast. If you
            # really want to lock it down, specify an authorization function.
            # E.g. `inherits(shinyUser()(), "UserEntity")` checks that we get a
            # valid server response that requires authentication
            if (is.character(input$token) && nchar(input$token) > 0) {
                # Next, if the user has supplied an authorization requirement,
                # check that.
                if (is.null(authz) || is.truthy(authz(input, output, session))) {
                    # We're good, so call the "normal" server function
                    func(input, output, session)
                    # Return the UI body. It is a "lazyUIOutput" that needs to
                    # be evaluated in the server context.
                    getOption("crunchy.body")()
                } else {
                    # Show the unauthorized page, which defaults to the unauthenticated
                    getOption("crunchy.body.unauthorized", public_ui)()
                }
            } else {
                # Not authenticated.
                public_ui()
            }
        })
    })
}

crunchUIOutput <- function (...) {
    ui <- lazyUIOutput(...)
    options(crunchy.body=ui)
    ui
}

crunchPublicUIOutput <- function (...) {
    ui <- lazyUIOutput(...)
    options(crunchy.body.public=ui)
    ui
}

crunchUnauthorizedUIOutput <- function (...) {
    ui <- lazyUIOutput(...)
    options(crunchy.body.unauthorized=ui)
    ui
}

lazyUIOutput <- function (...) {
    function () {
        tags$div(...)
    }
}

crunchyDefaultPublicUI <- lazyUIOutput(h1("You are not authenticated"))

is.truthy <- function (expr) {
    # Evaluate code in a server-like function, and always return TRUE/FALSE
    tryCatch(isTRUE(expr), error=function (e) FALSE)
}

setCrunchyAuthorization <- function (expr) {
    fun <- as.server(expr)
    options(crunchy.authz=fun)
    return(fun)
}

as.server <- function (expr) {
    e <- substitute(expr)
    out <- function (input, output, session) {}
    body(out) <- e
    out
}

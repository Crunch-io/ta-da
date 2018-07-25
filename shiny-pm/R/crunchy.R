crunchyServer <- function (server,
                           auth=getOption("crunchy.auth", crunchyDefaultAuth),
                           authed_ui=getOption("crunchy.body"),
                           public_ui=getOption("crunchy.body.public", crunchyDefaultPublicUI)) {

    shinyServer(function(input, output, session) {
        output$crunch_body <- renderUI({
            if (is.crunch.authenticated(auth(input, output, session))) {
                # Call the server function
                server(input, output, session)
                # Return the UI body
                authed_ui()
            } else {
                public_ui()
            }
        })
    })
}

lazyUIOutput <- function (...) {
    function () {
        tags$div(...)
    }
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

crunchyBody <- function (...) {
    # This is called inside a ui function. It captures the body content you
    # request, stores it for lazy calling inside crunchyServer(), then returns
    # the div that crunchyServer() will write into
    crunchUIOutput(...)
    uiOutput("crunch_body")
}

crunchyDefaultPublicUI <- lazyUIOutput(h1("You are not authenticated"))

is.crunch.authenticated <- function (expr) {
    # Evaluate code in a server-like function, and always return TRUE/FALSE
    tryCatch(isTRUE(expr), error=function (e) FALSE)
}

setCrunchyAuthenticator <- function (expr) {
    ## TODO: crunchyAuthenticator() that is ~ like in constructing expr?
    ## TODO: separate authentication and authorization?
    fun <- crunchyAuthenticator(expr)
    options(crunchy.auth=fun)
    return(fun)
}

crunchyDefaultAuth <- function (input, output, session) {
    # Temporary: This doesn't check the server, just for the existence of a *.crunch.io token
    is.character(input$token) && nchar(input$token) > 0
}

# crunchyDefaultAuth <- crunchyAuthenticator({
#     # This checks that we get a valid server response that requires authentication
#     inherits(shinyUser()(), "UserEntity")
# }

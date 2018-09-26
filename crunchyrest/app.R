library(crunchyrest)
devtools::load_all()

# These need to exist and can't return/be NULL but can otherwise be blank
ui <- ""
server <- function(input, output, session) ""

setRoute("/hack", {
    list(
        body = getRequestBody(req),
        query = parseQueryString(req$QUERY_STRING)
    )
})

# Run the application
shinyApp(ui = ui, server = server)

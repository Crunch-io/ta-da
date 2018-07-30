board_url <- "https://trello.com/b/kchAl4Hx/product-management"
token <- "dd2cc7d91c341e37596ae4f0fff54c6d"
secret <- "346eb20f0da81962755b153402df12e414a9289325429ac711cc5ee9ef7f29f8"

# setCrunchyAuthorization({
#     endsWith(email(shinyUser()()), "@crunch.io")
# })

global_cache <- new.env()

my_server <- function () {
    crunchyServer(function (input, output, session) {
        # observe({
        #     # Trigger this observer every time an input changes
        #     ## This is bad because it serializes a lot of crap we don't want to show
        #     reactiveValuesToList(input)
        #     session$doBookmark()
        # })
        # onBookmarked(function(url) {
        #     updateQueryString(url)
        # })
        try(
            # try() in case we're offline (dev only)
            output$current_user <- renderUI(paste0("Hello ", email(shinyUser()()), "!"))
        )
        tok <- get_token(token,
            secret,
            appname="shiny-board",
            scope="read,write",
            expiration="never"
        )
        if (file.exists("trellodata.RData") &&
            as.Date(file.mtime("trellodata.RData")) == Sys.Date()) {

            load("trellodata.RData")
        } else {
            # TODO: only update if they're NULL
            cards <- trello_cards(board_url, tok)
            membs <- get_board_members(board_url, tok)
            labs <- get_board_labels(board_url, tok)
            # Local cache for quicker testing
            save(cards, membs, labs, file="trellodata.RData")
        }

        rv <- reactiveValues()
        rv$cards <- cards
        rv$last_update <- Sys.time()

        output$time <- renderUI(tags$p(paste("Last updated", rv$last_update)))
        observeEvent(input$refresh, {
            rv$last_update <- Sys.time()
            rv$cards <- cards <- trello_cards(board_url, tok)
            # Local cache for quicker testing
            save(cards, membs, labs, file="trellodata.RData")
        })
        # reactivePoll(
        #     1000, ## TODO: back off
        #     session,
        #     function () {
        #         message(email(shinyUser()()))
        #         message(global_cache$last_update)
        #         global_cache$last_update
        #     },
        #     function () {
        #         rv$cards <<- global_cache$cards
        #         rv$last_update <<- global_cache$last_update
        #     }
        # )

        # Set up filters, which require data that the server has to fetch
        output$user <- renderUI({
            selectInput("user", "Person",
                structure(c("all", membs$id), .Names=c("All", membs$fullName)))
        })
        output$label <- renderUI({
            selectInput("label", "Label",
                structure(c("all", labs$id), .Names=c("All", labs$name)))
        })
        user_filter <- reactive({
            if (is.null(input$user) || input$user == "all") {
                TRUE
            } else {
                vapply(rv$cards$idMembers, function (x) any(unlist(x) %in% input$user), logical(1))
            }
        })
        label_filter <- reactive({
            if (is.null(input$label) || input$label == "all") {
                TRUE
            } else {
                vapply(rv$cards$idLabels, function (x) any(unlist(x) %in% input$label), logical(1))
            }
        })

        selected_cards <- reactive({
            rv$cards[user_filter() & label_filter(), ]
        })

        # Team board
        output$last_week <- renderUI({
            selected_cards() %>%
                get_team_activity(input$user, Sys.Date() - 7L) %>%
                format_team_cards()
        })
        output$this_week <- renderUI({
            selected_cards() %>%
                get_team_activity(input$user) %>%
                format_team_cards()
        })
        output$team_next <- renderUI({
            selected_cards() %>%
                up_next() %>%
                format_team_coming_cards()
        })

        output$doing_now <- renderDT({
            selected_cards() %>%
                filter(listName %in% building) %>%
                select(name, due) %>%
                datatable(options=list(order=list(list(2, "asc")))) %>%
                formatDate(2)
        })
        output$done <- renderDT({
            selected_cards() %>%
                filter(listName %in% "Done") %>%
                select(name, due) %>%
                datatable(options=list(order=list(list(2, "desc")))) %>%
                formatDate(2)
        })
        output$coming <- renderDT({
            selected_cards() %>%
                filter(listName %in% c(specing, "Ready to build")) %>%
                filter(!is.na(due)) %>%
                select(name, due) %>%
                datatable(options=list(order=list(list(2, "asc")))) %>%
                formatDate(2)
        })
    },
    authz=as.server(endsWith(email(shinyUser()()), "@crunch.io")))
}

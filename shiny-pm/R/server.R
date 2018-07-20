options(pivotal.token="019f16cff073f84e32e89562c131b6e3", pivotal.project=931610)
board_url <- "https://trello.com/b/kchAl4Hx/product-management"
token <- "dd2cc7d91c341e37596ae4f0fff54c6d"
secret <- "346eb20f0da81962755b153402df12e414a9289325429ac711cc5ee9ef7f29f8"


my_server <- shinyServer(function(input, output) {
    tok <- get_token(token,
            secret,
            appname="shiny-board",
            scope="read,write",
            expiration="never"
    )
    if (file.exists("trellodata.RData")) {
        load("trellodata.RData")
    } else {
        cards <- trello_cards(board_url, tok)
        membs <- get_board_members(board_url, tok)
        labs <- get_board_labels(board_url, tok)
        save(cards, membs, labs, file="trellodata.RData")
    }

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
            vapply(cards$idMembers, function (x) any(unlist(x) %in% input$user), logical(1))
        }
    })
    label_filter <- reactive({
        if (is.null(input$label) || input$label == "all") {
            TRUE
        } else {
            vapply(cards$idLabels, function (x) any(unlist(x) %in% input$label), logical(1))
        }
    })

    selected_cards <- reactive({
        cards[user_filter() & label_filter(), ]
    })

    # Team board
    output$last_week <- renderUI({
        card_list <-
            selected_cards() %>%
            last_week()
        card_list <- card_list[order(card_list$due),]
        format_cards(card_list)
    })
    output$this_week <- renderUI({
        card_list <-
            selected_cards() %>%
            this_week()
        card_list <- card_list[order(card_list$due),]
        format_cards(card_list)
    })
    output$team_next <- renderUI({
        card_list <-
            selected_cards() %>%
            up_next()
        card_list <- card_list[order(card_list$due),]
        format_cards(card_list)
    })

    output$doing_now <- renderDT({
        selected_cards() %>%
            filter(listName %in% building) %>%
            select(name, due) %>%
            datatable(options=list(order=list(list(2, "asc")))) %>%
            formatDate(2)
    })
    # output$doing_now <- renderUI({
    #     card_list <-
    #         selected_cards() %>%
    #         filter(listName %in% building)
    #     card_list <- card_list[order(card_list$due),]
    #     format_cards(card_list)
    # })

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
})

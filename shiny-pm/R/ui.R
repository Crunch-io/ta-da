my_ui <- function () shinyUI(fluidPage(

    # Application title
    h1("Trello Report"),
    div(uiOutput("label"), uiOutput("user")),
    tabsetPanel(type = "tabs",
                            tabPanel("Roadmap",
                                             tabsetPanel(type = "tabs",
                                                                     tabPanel("Building now", uiOutput("doing_now")),
                                                                     tabPanel("Done", DT::dataTableOutput("done")),
                                                                     tabPanel("Coming up", DT::dataTableOutput("coming"))
                                                                     )
                                             # h1("Building now"),
                                             # DT::dataTableOutput("doing_now"),
                                             # h1("Done"),
                                             # DT::dataTableOutput("done"),
                                             # h1("Coming up"),
                                             # DT::dataTableOutput("coming")
                            ),
                            tabPanel("Team board",
                                             h1("Last week"),
                                             DT::dataTableOutput("last_week"),
                                             h1("This week"),
                                             DT::dataTableOutput("this_week"),
                                             h1("Coming up"),
                                             DT::dataTableOutput("team_next")
                            )
        )
))

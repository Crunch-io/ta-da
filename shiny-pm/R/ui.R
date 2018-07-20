my_ui <- function () shinyUI(fluidPage(
    # Application title
    h1("Trello Report"),
    div(
        uiOutput("label"),
        uiOutput("user")
    ),
    tabsetPanel(type = "tabs",
        tabPanel("Roadmap",
            tabsetPanel(type = "tabs",
                tabPanel("Building now", DT::dataTableOutput("doing_now")),
                tabPanel("Done", DT::dataTableOutput("done")),
                tabPanel("Coming up", DT::dataTableOutput("coming"))
            )
        ),
        tabPanel("Team board",
            h2("Last week"),
            uiOutput("last_week"),
            h2("This week"),
            uiOutput("this_week"),
            h2("Coming up"),
            uiOutput("team_next")
        )
    )
))

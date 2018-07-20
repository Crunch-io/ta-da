my_ui <- function () shinyUI(fluidPage(
    # Application title
    h1("Trello Report"),
    fluidRow(
        column(6, uiOutput("label")),
        column(6, uiOutput("user"))
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
            tabsetPanel(type = "tabs",
                tabPanel("Last week", uiOutput("last_week")),
                tabPanel("This week", uiOutput("this_week")),
                tabPanel("Coming up", uiOutput("team_next"))
            )
        )
    )
))

#' @importFrom plotly plotlyOutput
my_ui <- function (request) shinyUI(fluidPage(
    tags$head(
        tags$title("Product Roadmap"),
        tags$style(HTML("
        .ul-top {
            list-style: none;
        }

        .btn {
            margin-top: 10px;
        }

        p {
            margin-top: 10px;
        }

        .center-column {
            padding-bottom: 20px;
            border: #107f65;
            border-width: thin;
            border-style: dashed;
        }
        "))
    ),
    "",
    crunchyBody(
        fluidRow(
            column(6, h1("Product Roadmap")),
            column(6, actionButton('refresh', 'Refresh'))
        ),
        fluidRow(
            column(6, uiOutput("label")),
            column(6, uiOutput("user"))
        ),
        tabsetPanel(type = "tabs",
            tabPanel("Team board",
                value="dev",
                fluidRow(
                    column(4, h2("Last week"), uiOutput("last_week")),
                    column(4, class="center-column", h2("This week"), uiOutput("this_week")),
                    column(4, h2("Coming up"), uiOutput("team_next"))
                )
            ),
            tabPanel("Calendar",
                value="cal",
                plotlyOutput("calendar", height="100%")
            ),
            tabPanel("Roadmap",
                value="roadmap",
                tabsetPanel(type = "tabs",
                    tabPanel("Building now", DT::dataTableOutput("doing_now")),
                    tabPanel("Done", DT::dataTableOutput("done")),
                    tabPanel("Coming up", DT::dataTableOutput("coming"))
                )
            )
        ),
        uiOutput("current_user"),
        uiOutput("time")
    ),
    crunchyUnauthorizedBody(
        h1("Soory"),
        tags$p("You must be a Crunch team member to access this."),
        tags$div("Try logging in at ", tags$a(href="https://app.crunch.io/login", "https://app.crunch.io/login"), ".")
    )
))

#' @importFrom plotly plotlyOutput
my_ui <- function (request) shinyUI(fluidPage(
    tags$head(
        tags$title("Product Roadmap"),
        tags$style(HTML("
            h1 {
                font-size: 2em;
                line-height: 2;
                color: #0064CA;
            }
            h2 {
                font-size: 1.4em;
                line-height: 2;
                color: #107f65;
            }
            ul {
               list-style: square;
               padding-left: 20px;
            }
            .ul-top {
                list-style: none;
            }

            a {
                color: #0064a4;
            }

            li {
                padding-top: .5em;
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
            tabPanel("Roadmap",
                value="roadmap",
                tabsetPanel(type = "tabs",
                    tabPanel("Building now", DT::dataTableOutput("doing_now")),
                    tabPanel("Done", DT::dataTableOutput("done")),
                    tabPanel("Coming up", DT::dataTableOutput("coming"))
                )
            ),
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
            )
        ),
        uiOutput("current_user"),
        uiOutput("time")
    ),
    crunchyPublicBody(
        h1("You can't sit here."),
        tags$div("Try logging in at ", tags$a(href="https://app.crunch.io/login", "https://app.crunch.io/login"), ".")
    ),
    crunchyUnauthorizedBody(
        h1("Soory"),
        tags$p("You must be a Crunch team member to access this."),
        tags$div("Try logging in at ", tags$a(href="https://app.crunch.io/login", "https://app.crunch.io/login"), ".")
    )
))

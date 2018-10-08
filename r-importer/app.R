library(crunchy)
library(haven)

# By default, the file size limit is 5MB. It can be changed by
# setting this option. Here we'll raise limit to 25MB.
options(shiny.maxRequestSize = 25 * 1024 ^ 2)

css <- "
.shiny-notification {
    position: fixed;
    top: 130px;
    left: 0px;
    right:80%;
    width: 300px
}

.btn:not(.ui-select-match-item) {
    background: #0064a4;
    color: #fff;
}

.input-group .form-control {
    height: 38px
}

.container-fluid {
    padding: 0;
}
"

ui <- fluidPage(
    tags$head(tags$style(css)),
    crunchyBody(
        tags$div(
            class = "dataset-importer-text",
            style = "height:500px;",
            h3("Import data", class = "title"),
            fileInput('file1', label = NULL, buttonLabel = "Select File"),
            uiOutput('contents')
        )
    )
)

options(httpcache.log = "")

withCrunchyProgress <- function (expr, ...) {
    tracer <- quote({
        setup_progress_bar <- function (...) NULL
        update_progress_bar <- function (p, value) {
            shiny::setProgress(value, message = NULL)
        }
        close <- function (...) NULL
    })
    trace("pollProgress", tracer = tracer, where = newDataset)
    on.exit(untrace("pollProgress", where = newDataset))
    shiny::withProgress(expr,
                        min = 0,
                        max = 100,
                        value = 0,
                        ...)
}

server <- crunchyServer(function(input, output, session) {
    output$contents <- renderUI({
        # input$file1 will be NULL initially. After the user selects
        # and uploads a file, it will be a data frame with 'name',
        # 'size', 'type', and 'datapath' columns. The 'datapath'
        # column will contain the local filenames where the data can
        # be found.
        
        inFile <- input$file1
        
        if (is.null(inFile)) {
            return(NULL)
        }
        ext <- tail(unlist(strsplit(inFile$datapath, ".", fixed = TRUE)), 1)
        if (ext == "sav") {
            df <- read_sav(inFile$datapath)
        } else if (ext == "dta") {
            df <- read_dta(inFile$datapath)
        } else {
            return("Unsupported file type")
        }
        
        tokenAuth(input$token, "shiny.crunch.io")
        withCrunchyProgress({
            ds <- newDataset(df, name = basename(inFile$name))
        }, message = "Importing")
        return(tags$a(
            "Done",
            class = "btn primary",
            href = crunch:::APIToWebURL(ds),
            target = "_top"
        ))
    })
})

# Run the application
shinyApp(ui = ui, server = server)

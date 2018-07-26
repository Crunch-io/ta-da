# Here's a good place to put your top-level package documentation

#' @import shiny
#' @import DT
#' @import trelloR
#' @import dplyr
.onLoad <- function (lib, pkgname="shinyPM") {
    ## Put stuff here you want to run when your package is loaded
    invisible()
}

#' @title Run the Shiny app
#' @export
my_app = function () {
    shinyApp(ui = my_ui(), server = my_server())
}

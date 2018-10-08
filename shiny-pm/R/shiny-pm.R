# Here's a good place to put your top-level package documentation

#' @import shiny
#' @import DT
#' @import trelloR
#' @import dplyr
.onLoad <- function (lib, pkgname="shinyPM") {
    ## Put stuff here you want to run when your package is loaded
    options(
        pivotal.token="019f16cff073f84e32e89562c131b6e3",
        pivotal.project=931610
    )
    invisible()
}

#' @title Run the Shiny app
#' @export
my_app = function () {
    shinyApp(ui = my_ui, server = my_server())
}

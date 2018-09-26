#' Get request body from request object
#' @param req The request object
#' @return The content, correctly parsed according to Content-Type. If there
#' is no content, the function returns NULL
#' @export
#' @importFrom httr content
getRequestBody <- function (req) {
    cont <- req$rook.input$read()
    if (length(cont)) {
        # Confect a "response"-class object so we can use httr's `content` 
        # method to parse the body according to the specified content-type
        httr_req <- structure(
            list(
                headers=structure(as.list(req$HEADERS), class="insensitive"), 
                content=cont
            ), 
            class="response"
        )
        return(content(httr_req))
    } else {
        # No content but for some reason `httr::content` fails on it
        return(NULL)
    }
}

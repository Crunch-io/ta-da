#' Set a custom request handler for a path
#'
#' This function lets you supply a function that handles requests directly. You
#' can use it to build a JSON API with Shiny, which you otherwise can't do
#' because a proper Shiny app always returns HTML and may require JavaScript to
#' execute in a browser.
#'
#' Of course, this isn't a good way to set up a JSON API server. You shouldn't
#' use Shiny for that. But if you only have the ability to deploy Shiny apps,
#' this will work :)
#'
#' `registerRoute` lets you supply an arbitrary function of a "request" object
#' to map to the `path`. `setRoute` provides some boilerplate wrapping that
#' includes default values and ensures that the current request is
#' authenticated. If the user is not authenticated, the default is to return
#' status 403 Not Authorized with a JSON message. If authenticated, default is
#' 200 OK status. If the code in `handler` errors, 500 Internal Server Error
#' will be returned and the R exception message will be trapped, printed to
#' stdout, and not shown to the user.
#'
#' In `setRoute`, the other values you can set are:
#'
#' * `status`, if you want to return something other than `200 OK` on success 
#' * `headers`, if you want to supply more than `Content-Type: application/json`
#'
#' Because `setRoute` manages Crunch authentication, any functions from the
#' `crunch` package are valid to use inside the `handler`, as if you were using
#' R locally. There is no Shiny reactivity or other (relevant) magic to 
#' consider.
#'
#' See the example for how to extract important parameters from the request, and
#' for a full list of available parameters in the request object, see the source
#' in `route.R`.
#'
#' @param path character URL segment. Unfortunately, `"/"` is not valid.
#' @param handler For `setRoute`, code that will be quoted and executed inside a
#'   `function (req) ...` if the current request is authenticated. It should end
#'   with the desired response content (but do _not_ call `return()`), which  
#'   will be converted to JSON. For more control, call `registerRoute` with an 
#'   explicit `function (req) ...`
#' @seealso https://stackoverflow.com/a/34198825 for inspiration
#' @return Called for its side effects of registering the request handler.
#' @export
#' @examples
#' \dontrun{
#' setRoute("/hack", {
#' # If you're concerned about state bleeding across sessions, uncomment:
#' # on.exit(httpcache::clearCache())
#'
#' # If you're in this code, the response `status` has been set to 200,
#' # but you can override it like:
#' # status <- 202L
#'
#' # You can also add to or override response headers like this:
#' # headers[["Location"]] <- "https://some.url/
#'
#' # The handler code should end with (but not `return()`) the desired response
#' # body content, which will be converted to JSON.
#' # Here is an example of how to get useful content from the `req` object:
#' list(
#'     body = getRequestBody(req),
#'     query = parseQueryString(req$QUERY_STRING)
#' )
#' })
#' }
setRoute <- function (path, handler) {
    stuff_to_do <- substitute(handler)
    fun <- buildHandlerFun(stuff_to_do)
    registerRoute(path, fun)
}

#' @rdname setRoute
#' @export
#' @importFrom digest digest
registerRoute <- function (path, handler) {
    # digest ensures a unique "id" for different functions + path
    id <- digest(list(path, handler))
    shiny:::handlerManager$addHandler(
        shiny:::routeHandler(path, handler),
        id 
    )
}

#' @importFrom jsonlite toJSON
buildHandlerFun <- function (stuff_to_do) {
    eval(substitute(function (req) {
        # Set default response
        response_body <- list(message = "Not authorized")
        status <- 403L
        headers <- list('Content-Type' = 'application/json')

        if (setToken(req$HTTP_COOKIE)) {
            # We're authenticated.
            status <- 200L
            tryCatch(
                response_body <- do_stuff, 
                error=function (e) {
                    # Catch errors, "log" the original message, and sanitize
                    print(e$message)
                    response_body <<- list(message="Internal Server Error")
                    status <<- 500L
                }
            )
        }
        
        # TODO: allow returning no content
        return(list(
            status = status,
            headers = headers,
            body = toJSON(response_body, auto_unbox = TRUE)
        ))
    }, list(do_stuff=stuff_to_do)))
}

# Here's what's in the `req` object:
# options(width=76)
# print(ls(envir = req))
#  [1] "HEADERS"                        "HTTP_ACCEPT"                   
#  [3] "HTTP_ACCEPT_ENCODING"           "HTTP_ACCEPT_LANGUAGE"          
#  [5] "HTTP_CACHE_CONTROL"             "HTTP_CONNECTION"               
#  [7] "HTTP_COOKIE"                    "HTTP_HOST"                     
#  [9] "HTTP_UPGRADE_INSECURE_REQUESTS" "HTTP_USER_AGENT"               
# [11] "httpuv.version"                 "PATH_INFO"                     
# [13] "QUERY_STRING"                   "REMOTE_ADDR"                   
# [15] "REMOTE_PORT"                    "REQUEST_METHOD"                
# [17] "rook.errors"                    "rook.input"                    
# [19] "rook.url_scheme"                "rook.version"                  
# [21] "SCRIPT_NAME"                    "SERVER_NAME"                   
# [23] "SERVER_PORT"  
# body <- sapply(ls(pattern="^[A-Z]", envir=req), 
#     function (x) get(x, req), simplify=FALSE)


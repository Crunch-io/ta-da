## To Do list:
## X Wrap the cookie auth more magically
## * Handle 401 on renderPlot with a static file
## X Move static files to here
## * Update whaam CSS link with a permanent URL
## * Performance auditing
    ## x Disable check for updates
    ## * Load dataset from URL
    ## * Session object that doesn't fetch when returned (actually not a problem here)
    ## x Logging/profiling
        ## Page load in example is 9s
            # 2s loading code, deps
            ## -> Save 1s by loading packages in the runApp command; TODO: document best practice?
            # 1.2s on first attempt before auth token set
            ## -> DONE. Beat the race by switching to hidden input
            # 2.1s loading dataset
            ## TODO: save 1.2s by loading from URL; document best practice
            # each GET after that is 200ms, 2-3 per table, executed sequentially
            ## -> will be a little faster when running on the server
            ## TODO: hack shiny to parallelize those?
## * Auth protections/per-user caching?

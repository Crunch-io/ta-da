library(elbr)
df <- cleanLog(read.elb("/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/april-500s.log"))

table(standardizeURLs(df$request_url), df$request_verb)

library(elbr)

logs <- system('cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2016/04 && find . | xargs -n 1 egrep "\\-1 \\-1 \\-1"', intern=TRUE)
df <- cleanLog(read.elb(textConnection(logs)))

table(standardizeURLs(df$request_url), df$request_verb)

library(elbr)

logs <- system('cd /var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2016/05/05 && find . | xargs -n 1 egrep " 500 500 "', intern=TRUE)
df <- cleanLog(read.elb(textConnection(logs)))

table(standardizeURLs(df$request_url), df$request_verb)

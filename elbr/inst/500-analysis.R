## Made file with:
## root@ahsoka:/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/eu-west-1/2016/04# find . | xargs -n 1 egrep "\-1 \-1 \-1" > ../../../april-500s.log

library(elbr)
df <- cleanLog(read.elb("/var/www/logs/AWSLogs/910774676937/elasticloadbalancing/april-500s.log"))

table(standardizeURLs(df$request_url), df$request_verb)

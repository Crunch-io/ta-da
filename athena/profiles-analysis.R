# Various things done with results from Athena and Mongo results to make the
# charts in https://docs.google.com/document/d/1Tu2eO32WEbr5qk_BV_q5YTakHRdXF1w6dLf7utu6-Dc/edit

library(dplyr)
library(readr)
library(ggplot2)

df <- read_csv("~/c/athena-results.csv")
df$date <- as.Date(paste(df$year, df$month, df$day, sep="-"))
df$week <- as.integer(df$date + 3) %/% 7

df %>%
    arrange(date) %>%
    group_by(week, segment, state) %>%
    summarize(
        n=sum(n),
        total_time=sum(total_time),
        n_5xx=sum(n_5xx),
        n_504=sum(n_504),
        n_under200ms=sum(n_under200ms),
        date=min(date)
    ) %>%
    group_by(week) %>% # Once more so that every segment/state has the same date
    mutate(date=min(date)) ->
    weekly

weekly %>%
    mutate(
        n_stream = n * as.numeric(segment %in% "Stream"),
        n_web = n * as.numeric(segment %in% c("Profiles", "Web App")),
        n_profiles = n * as.numeric(segment %in% "Profiles"),
        n_state = n * state
    ) %>%
    group_by(week) %>%
    summarize(
        date=min(date),
        n=sum(n),
        under200=sum(n_under200ms)/sum(n),
        n_stream=sum(n_stream),
        n_web=sum(n_web),
        n_profiles=sum(n_profiles),
        n_state=sum(n_state)
    ) %>%
    write.csv("~/c/elb-weekly-athena.csv")

weekly <- weekly[-nrow(weekly),] # Last week is partial

weekly %>%
    group_by(segment, state, date) %>%
    summarize(
        under200=100*sum(n_under200ms)/sum(n)
    ) ->
    pct200

pct200 %>%
    filter(state == 0 & date > "2017-01-01" & segment %in% c("Profiles", "Web App")) %>%
    ggplot(aes(x=date, y=under200, col=segment)) ->
    plt

plt + geom_smooth(se=FALSE, span=.4) + geom_line()


weekly %>%
    filter(state == 0 & date > "2017-01-01" & segment %in% c("Profiles", "Web App")) %>%
    mutate(`Requests (millions per week)`=n/1000000) %>%
    ggplot(aes(x=date, y=`Requests (millions per week)`, col=segment)) ->
    plt_traffic

plt_traffic + geom_smooth(se=FALSE, span=.4) + geom_line()

weekly %>%
    filter(state == 0 & date > "2017-01-01" & segment %in% c("Profiles", "Web App")) %>%
    mutate(hours=total_time/3600) %>%
    ggplot(aes(x=date, y=hours, col=segment)) ->
    plt_time

plt_time + geom_smooth(se=FALSE, span=.4) + geom_line()


#####

# File isn't delimited by a single char so it needs to be munged first
userlines <- readLines("~/c/profiles-user-creation.txt")[-(1:11)]
userlines <- sub("^(.*):\t\t(.*)\\+00:00$", "\\1\t\\2", userlines)
users <- read_tsv(userlines, col_names=c("email", "timestamp"), col_types="cT")

users %>%
    filter(!grepl("@crunch\\.io|@yougov\\.", email)) %>%
    mutate(
        date = as.Date(timestamp),
        week = as.integer(date + 3) %/% 7,
        weekday = as.Date(week * 7 - 3, origin="1970-01-01")
    ) %>%
    group_by(date) %>%
    summarize(count=n()) %>%
    mutate(
        total = cumsum(count)
    ) ->
    weekly_users

ggplot(weekly_users[weekly_users$date > "2017-01-01",], aes(x=date, y=total)) + geom_step()

#####

datasets <- read_tsv("~/c/profiles-dataset-dims.txt", skip=8, col_names=c("rows", "cols", "id", "name"), col_types="ddcc")
datasets$type <- sub("^(.*?) .*", "\\1", datasets$name)
datasets$country <- sub("^.*? (.*?) .*", "\\1", datasets$name)
datasets$date <- as.Date(sub("^.*? .*? ([0-9\\-]{10}).*", "\\1", datasets$name))

datasets %>%
    filter(!grepl("_", name) & rows > 0 & cols > 0) %>%
    arrange(date) %>%
    mutate(
        week = as.integer(date + 3) %/% 7,
        weekday = as.Date(week * 7 - 3, origin="1970-01-01"),
        size = rows * cols
    ) %>%
    group_by(weekday) %>%
    summarize(
        biggest = max(size),
        size = sum(size)
    ) %>%
    mutate(
        total = cumsum(size)
    ) ->
    dataset_mass

ggplot(dataset_mass[dataset_mass$weekday > "2017-01-01",], aes(x=weekday, y=size)) + geom_step()
ggplot(dataset_mass[dataset_mass$weekday > "2017-01-01",], aes(x=weekday, y=total)) + geom_step()
ggplot(dataset_mass[dataset_mass$weekday > "2017-01-01" & dataset_mass$biggest > 7e9,], aes(x=weekday, y=biggest)) + geom_step()

# tab book, progress, cube, deck, dataset export

import {Parser} from 'json2csv'
import {fetchRecentlyAcceptedStories, storyUpdated} from './pivotal'

const json2csvParser = new Parser()

// @ts-ignore
Date.prototype.formatMMDDYYYY = function () {
    return (this.getMonth() + 1) +
        "/" + this.getDate() +
        "/" + this.getFullYear();
}


// load env variables from .creds file (serverless doesn't copy in .env file)
require('dotenv').config({path: '.creds'})

export const pivotalStoryWebhook = async (event, context, callback) => {
    const data = JSON.parse(event.body)

    // update pivotal story
    await storyUpdated(data)

    // create a response
    const response = {
        statusCode: 200,
        // body: JSON.stringify(data)
    }

    callback(null, response)
}

export const recentlyAcceptedStories = async (event, context, callback) => {

    const stories = await fetchRecentlyAcceptedStories()

    // create a response
    const csv = json2csvParser.parse(stories)
    const response = {
        headers: {
            'Content-Type': 'text/csv',
            'Content-disposition': 'attachment; filename=RecentlyShippedStories.csv'
        },
        body: csv,
        statusCode: 200
    }

    callback(null, response)
}

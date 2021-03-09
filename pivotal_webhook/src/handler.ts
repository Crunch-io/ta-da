import axios from 'axios'
import * as qs from 'qs'
import {sendEmail} from './email'

// See https://www.pivotaltracker.com/help/api/rest/v5#Stories for additional parameters
interface pivotalStoryFilter {
    accepted_after?: string,
    limit?: number
}

// @ts-ignore
Date.prototype.formatMMDDYYYY = function () {
    return (this.getMonth() + 1) +
        "/" + this.getDate() +
        "/" + this.getFullYear();
}

// set up pivotal network request client
const pivotal = axios.create({
    baseURL: 'https://www.pivotaltracker.com/services/v5/',
    timeout: 30000,
    headers: {
        'X-TrackerToken': process.env.PIVOTAL_API_KEY
    }
})

// load env variables from .creds file (serverless doesn't copy in .env file)
require('dotenv').config({path: '.creds'})

// set up pivotal people dictionary
const pivotalPeople = {}

const fetchPivotalProjectPeople = async () => {
    const url = `projects/${process.env.PIVOTAL_PROJECT_ID}/memberships`
    return pivotal.get(url)
        .then(res => {
            const people = {}
            const peopleArray = res.data.map(p => {
                pivotalPeople[p.person.id] = p.person
                people[p.person.id] = p.person
                return p.person
            })
            return people
        })
        .catch(err => console.log(err))
}

const fetchMe = async () => {
    const url = `me`
    return pivotal.get(url)
        .then(res => {
            pivotalPeople[res.data.id] = res.data
            return res.data
        })
        .catch(err => console.log(err))
}

const fetchPivotalPeople = async () => {
    const apiPath = `my/people`
    const queryString = {
        project_id: process.env.PIVOTAL_PROJECT_ID,
        limit: 1000
    }
    const url = `${apiPath}?${qs.stringify(queryString)}`
    return pivotal.get(url)
        .then(res => {
            const people = {}
            const peopleArray = res.data.map(p => {
                pivotalPeople[p.person.id] = p.person
                people[p.person.id] = p.person
                return p.person
            })
            return people
        })
        .catch(err => console.log(err))
}

const populatePivotalPeople = async () => {
    await fetchPivotalPeople()
    await fetchMe()
    await fetchPivotalProjectPeople()
    console.log(`Fetched all pivotal people`)
}

const storyUpdatedWebhook = async (postBody) => {

    const body = postBody
    const time = new Date().toISOString()
    body.req_time = time


    // story was accepted
    if (postBody.highlight === 'accepted') {
        const storyMeta = postBody.primary_resources[0]
        if ( storyMeta.story_type !== 'release') {
            const url = `projects/${process.env.PIVOTAL_PROJECT_ID}/stories/${storyMeta.id}`
            const story = await pivotal.get(url)
                .then(res => {
                    console.log("query story", JSON.stringify(res.data))
                    return res.data
                })
                .catch(err => console.log(err))
            const ownerId = story.owned_by_id || story.owner_ids[0]
            if (story.description) {

                // copy description to comments
                const commentUrl = `${url}/comments`
                pivotal.post(commentUrl, {
                    text: `Previous story description: ${story.description}`
                }).then(() => {
                    console.log(`Moved story ${story.id} description to comment`)
                })

                // set description
                pivotal.put(url, {
                    description: `[Please write release note here or "RELEASE NOTE N/A"]`
                }).then(() => {
                    console.log(`Reset story ${story.id} description`)
                })
            }
            sendStoryUpdatedWebhookEmail(story, pivotalPeople[ownerId])
        }
    }
}

const sendStoryUpdatedWebhookEmail = async (story, owner) => {
    let ownerEmailAddress = owner.email
    console.log(`Sending email for story ${story.id} to ${owner.email}`)
    const emailHtml = `
Congratulations for shipping <b>${story.name}</b>! Yes that's right - I'm talking about pivotal story ${story.id}. 
Please take a minute right now (while everything is fresh in your mind) to write a sweet release note that we can
communicate to end-users about the awesome work that you just shipped.
<br/><br/>
Instructions:<br/>
<ol>
    <li><a href="${story.url}">Click here to open the pivotal story</a>.</li>
    <li>Write (or copy/paste) your release note into the description field and click UPDATE.</li>
    <li>If the story you shipped would not be interesting to end-users for some reason (paying down technical debt, not
        user-facing, etc.), please enter RELEASE NOTE N/A.
    </li>
</ol>
Keys to success:
<ul>
    <li>For your convenience, I have moved the previous description for this story (if there was one) into the comments
        section so that you can enter your release note into the story <b>description</b> field.
    </li><li>
    Your release note should be concise and easy to understand for an average end-user. 
    </li><li>
    Avoid technical mumbo-jumbo only an engineer could understand and try to minimize market-research jargon that a user 
    would need a PhD to understand. <b>Remember - plain English!</b> Don't be afraid to include additional or redundant 
    context if you think it would be potentially helpful to users.
    </li><li>
    Don't be afraid if English isn't your first language! Just do your best and trust our excellent technical writer
    to re-word things if necessary.
    </li><li>
    Where possible, include html links inside your release note to Help Center articles, our API reference, and/or a
        demo/training video you have created to illustrate a feature.
    </li><li>
    If you have any questions please read 
    <a href="https://www.notion.so/crunch/Release-Notes-FAQ-a9fb1a48b375416c9047a84587c72355">this notion page</a>
    and then DM Jeff Kreger for help.
    </li>
</ul>
Now go and do this right now before you forget!
<br/><br/>
Thanks
    `

    const subject = `Please write a release note for story - ${story.name}`;
    const msg = {
        to: ownerEmailAddress,
        bcc: 'dcarr178@gmail.com',
        from: 'David Carr <david.carr@crunch.io>',
        html: emailHtml,
        subject
    }
    sendEmail(msg)

}

export const post = async (event, context, callback) => {
    const data = JSON.parse(event.body)

    // if lambda stays running long enough then this will already be populated
    if (Object.keys(pivotalPeople).length < 1) await populatePivotalPeople()

    // update pivotal story
    await storyUpdatedWebhook(data)

    // create a response
    const response = {
        statusCode: 200,
        // body: JSON.stringify(data)
    }

    callback(null, response)
}

import * as sgMail from '@sendgrid/mail'

// load env variables from .creds file (serverless doesn't copy in .env file)
require('dotenv').config({path: '.creds'})
sgMail.setApiKey(process.env.SENDGRID_API_KEY)

const sendEmail = msg => {
    msg.to = 'dcarr178+test@gmail.com' // for testing
    sgMail
        .send(msg)
        .then(() => {
            console.log(`Email sent to ${msg.to}`)
        })
        .catch((error) => {
            console.error(JSON.stringify(error, null, 2))
        })
}

export {
    sendEmail
}

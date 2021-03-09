# Pivotal
### Webhook post
This typescript program gets deployed as an AWS lambda function fronted by an api gateway url which pivotal tracker
POSTs to every time a pivotal story is updated. Currently, we filter down to a
specific type of story and status and email developers a friendly reminder to add a release note to the story
description. In the future we may change this webhook to do more things.

### Recently accepted stories
https://f47ajijg3m.execute-api.eu-west-1.amazonaws.com/production/pivotal/recently-accepted-stories

This function is fronted by an api gateway url and returns a csv file containing recently accepted stories. Mainly used by Jeff Kreger.

# Step 0 - configure your environment

### Initialize your environment
```bash
npm run init
```

### Configuration needed for local testing:
Copy `.creds-sample` to `.creds` and fill in the configuration details needed to:

* Query pivotal API
* Send email via sendgrid

The pivotal api key is stored here in [1password](https://start.1password.com/open/i?a=2JQVFSBKL5BIVEN4LLY572FK4M&v=p5bqs2nopqzzsr7e5ldg3qort4&i=3ugfygcy7orekfwisx44geuyyy&h=crunchio.1password.com).

The sendgrid api key is stored here in [1password](https://start.1password.com/open/i?a=2JQVFSBKL5BIVEN4LLY572FK4M&v=yrkn7qszvxq336rvdw22omzgce&i=v4ag4dm4zflhjvahjjkw2mkmkq&h=crunchio.1password.com).

Note: `.creds` contains secrets and should not be checked into the source code repository. It is already included in `.gitignore`.
  
### Additional configuration needed remote deployment and testing:
Follow instructions for your operating system to install aws-cli.
https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html

Now configure the AWS secrets needed to deploy lambda functions:

```bash
/usr/local/bin/aws configure
```
* AWS Access Key ID [None]: abc
* AWS Secret Access Key [None]: abc
* Default region name [None]: eu-west-1
* Default output format [None]:

The credentials we use are for iam user `serverless-admin` stored here in [1password](https://start.1password.com/open/i?a=2JQVFSBKL5BIVEN4LLY572FK4M&v=yrkn7qszvxq336rvdw22omzgce&i=cyf4z353fnul4tn7lp7pe4cj6a&h=crunchio.1password.com).

# Step 1 - make changes and test them locally
Edit the typescript files in `./src/`.

```bash
npm run build
npm run test-local
```
OR
```bash
tsc
node index.js '{"kind":"story_update_activity","guid":"2172644_128130","project_version":128130,"message":"David Carr accepted this feature","highlight":"accepted","changes":[{"kind":"label","change_type":"update","id":21478684,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":30,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":36,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":1,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":32,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":37,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"has no code"},{"kind":"label","change_type":"update","id":22825522,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":9,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":1,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":12,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"2021-q1 - collaborations - documentation"},{"kind":"story","change_type":"update","id":176645899,"original_values":{"current_state":"delivered","accepted_at":null,"updated_at":1615250427000},"new_values":{"current_state":"accepted","accepted_at":1615250431000,"updated_at":1615250431000},"name":"Create release notes page and rss feed on website","story_type":"feature"}],"primary_resources":[{"kind":"story","id":176645899,"name":"Create release notes page and rss feed on website","story_type":"feature","url":"https://www.pivotaltracker.com/story/show/176645899"}],"secondary_resources":[],"project":{"kind":"project","id":2172644,"name":"Crunch CI"},"performed_by":{"kind":"person","id":3285583,"name":"David Carr","initials":"dcarr"},"occurred_at":1615250431000,"req_time":"2021-03-09T00:40:36.316Z"}'
```

# Step 2 - deploy as lambda function
Pivotal is not hitting this endpoint, so you can test manually to make sure everything looks
good.

```bash
npm run deploy-dev-remote
```
OR
```bash
tsc
npx serverless deploy
```


# Step 3 - test functions remotely
It's possible the url below will change to something else so verify it against
the output of your deploy command.

### Start a process to watch logs
```bash
npm run log-dev-remote
```
OR
```bash
npx serverless logs -f post -t
```

### Send remote request
This service sends real email so be careful!
```bash
npm run test-dev-remote
```
OR
```bash
curl https://5jnk5key01.execute-api.eu-west-1.amazonaws.com/dev/pivotal -d '{"kind":"story_update_activity","guid":"2172644_128130","project_version":128130,"message":"David Carr accepted this feature","highlight":"accepted","changes":[{"kind":"label","change_type":"update","id":21478684,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":30,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":36,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":1,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":32,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":37,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"has no code"},{"kind":"label","change_type":"update","id":22825522,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":9,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":1,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":12,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"2021-q1 - collaborations - documentation"},{"kind":"story","change_type":"update","id":176645899,"original_values":{"current_state":"delivered","accepted_at":null,"updated_at":1615250427000},"new_values":{"current_state":"accepted","accepted_at":1615250431000,"updated_at":1615250431000},"name":"Create release notes page and rss feed on website","story_type":"feature"}],"primary_resources":[{"kind":"story","id":176645899,"name":"Create release notes page and rss feed on website","story_type":"feature","url":"https://www.pivotaltracker.com/story/show/176645899"}],"secondary_resources":[],"project":{"kind":"project","id":2172644,"name":"Crunch CI"},"performed_by":{"kind":"person","id":3285583,"name":"David Carr","initials":"dcarr"},"occurred_at":1615250431000,"req_time":"2021-03-09T00:40:36.316Z"}'
and
https://5jnk5key01.execute-api.eu-west-1.amazonaws.com/dev/pivotal/recently-accepted-stories
```

You should see the logs register that your request was received.

# Step 4 - deploy to production
Once you are sure it's working on dev, go ahead and deploy it to our production endpoint. Pivotal is already 
configured to hit this endpoint so as soon as you deploy then pivotal is hitting it.

```bash
npm run deploy-prod-remote
```
OR
```bash
npx serverless deploy --stage production
```

# Other

### Pivotal webhook url
The url we configure pivotal tracker to POST to is `https://s9wim1oymd.execute-api.eu-west-1.amazonaws.com/production/pivotal`.

```bash
curl https://f47ajijg3m.execute-api.eu-west-1.amazonaws.com/production/pivotal -d '{"kind":"story_update_activity","guid":"2172644_128130","project_version":128130,"message":"David Carr accepted this feature","highlight":"accepted","changes":[{"kind":"label","change_type":"update","id":21478684,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":30,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":36,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":1,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":32,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":37,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"has no code"},{"kind":"label","change_type":"update","id":22825522,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":9,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":1,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":12,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"2021-q1 - collaborations - documentation"},{"kind":"story","change_type":"update","id":176645899,"original_values":{"current_state":"delivered","accepted_at":null,"updated_at":1615250427000},"new_values":{"current_state":"accepted","accepted_at":1615250431000,"updated_at":1615250431000},"name":"Create release notes page and rss feed on website","story_type":"feature"}],"primary_resources":[{"kind":"story","id":176645899,"name":"Create release notes page and rss feed on website","story_type":"feature","url":"https://www.pivotaltracker.com/story/show/176645899"}],"secondary_resources":[],"project":{"kind":"project","id":2172644,"name":"Crunch CI"},"performed_by":{"kind":"person","id":3285583,"name":"David Carr","initials":"dcarr"},"occurred_at":1615250431000,"req_time":"2021-03-09T00:40:36.316Z"}'
```

### Recently accepted stories url

```
https://f47ajijg3m.execute-api.eu-west-1.amazonaws.com/production/pivotal/recently-accepted-stories
```

### To remove/delete the lambda function from AWS

```bash
npx serverless remove
```

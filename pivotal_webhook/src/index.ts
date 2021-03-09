import {post} from "./handler"
/*
To test this handler, simply pass in via the command line the exact POST body that pivotal would post to the
api endpoint.

{"kind":"story_update_activity","guid":"2172644_128130","project_version":128130,"message":"David Carr accepted this feature","highlight":"accepted","changes":[{"kind":"label","change_type":"update","id":21478684,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":30,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":36,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":1,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":15,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":32,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":37,"started":0,"finished":0,"unstarted":1,"planned":0,"delivered":0,"unscheduled":4,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"has no code"},{"kind":"label","change_type":"update","id":22825522,"original_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":9,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":2,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":1,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"new_values":{"counts":{"number_of_zero_point_stories_by_state":{"accepted":2,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"sum_of_story_estimates_by_state":{"accepted":11,"started":0,"finished":0,"unstarted":0,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"number_of_stories_by_state":{"accepted":12,"started":0,"finished":0,"unstarted":5,"planned":0,"delivered":0,"unscheduled":0,"rejected":0,"kind":"counts_by_story_state"},"kind":"story_counts"}},"name":"2021-q1 - collaborations - documentation"},{"kind":"story","change_type":"update","id":176645899,"original_values":{"current_state":"delivered","accepted_at":null,"updated_at":1615250427000},"new_values":{"current_state":"accepted","accepted_at":1615250431000,"updated_at":1615250431000},"name":"Create release notes page and rss feed on website","story_type":"feature"}],"primary_resources":[{"kind":"story","id":176645899,"name":"Create release notes page and rss feed on website","story_type":"feature","url":"https://www.pivotaltracker.com/story/show/176645899"}],"secondary_resources":[],"project":{"kind":"project","id":2172644,"name":"Crunch CI"},"performed_by":{"kind":"person","id":3285583,"name":"David Carr","initials":"dcarr"},"occurred_at":1615250431000,"req_time":"2021-03-09T00:40:36.316Z"}

*/

const lastArg = process.argv[process.argv.length - 1]

post(
    {
        body: lastArg
    },
    {},
    () => {
    }
)

from copy import deepcopy
#from travel_booking import TravelAPI
from pprint import pprint
from bfcl.eval_checker.multi_turn_eval.func_source_code.posting_api import TwitterAPI


initial_state = {
    "tweet_counter": 10,
    "tweets": {
        "0": {
            "id": 0,
            "username": "john",
            "content": "Just canceled my trip to LA. #TravelUpdate #BusinessTrip",
            "tags": ["#TravelUpdate", "#BusinessTrip"],
            "mentions": [],
        },
        "1": {
            "id": 1,
            "username": "john",
            "content": "Looking forward to new opportunities! #Networking #Business",
            "tags": ["#Networking", "#Business"],
            "mentions": [],
        },
    },
    "username": "john",
    "password": "john1234",
}

api = TwitterAPI()
api._load_scenario(deepcopy(initial_state))

### authenticate
api.authenticate_twitter(username='john',password='john2234')
print("after auth 1")
api.print_everything()
api.authenticate_twitter(username='john',password='john1234')
print("after auth 2")
api.print_everything()

api.revert_authenticate_twitter()
print("== revert auth 1")
api.print_everything()
api.revert_authenticate_twitter()
print("== revert auth 2")
api.print_everything()

### follow
#api.authenticate_twitter(username='john',password='john1234')
#api.follow_user(username_to_follow="kevin")
#print("after follow_user 1")
#api.print_everything()
#
#api.revert_follow_user()
#print("== revert follow_user 1")
#api.print_everything()

### mention
#api.authenticate_twitter(username='john',password='john1234')
#api.mention(tweet_id=1,mentioned_usernames=['@mention1'])
#print("after mention 1")
#api.print_everything()
#api.mention(tweet_id=1,mentioned_usernames=['@mention2'])
#print("after retweet 2")
#api.print_everything()
#
#api.revert_mention()
#print("== revert mention 1")
#api.print_everything()
#api.revert_mention()
#print("== revert mention 2")
#api.print_everything()

### comment
#api.authenticate_twitter(username='john',password='john1234')
#api.comment(tweet_id=1, comment_content='Comment1')
#print("after comment 1")
#api.print_everything()
#api.comment(tweet_id=0, comment_content='Comment2')
#print("after retweet 2")
#api.print_everything()
#
#api.revert_comment()
#print("== revert comment 1")
#api.print_everything()
#api.revert_comment()
#print("== revert comment 2")
#api.print_everything()

### retweet
#api.authenticate_twitter(username='john',password='john1234')
#api.retweet(tweet_id=1)
#print("after retweet 1")
#api.print_everything()
#api.retweet(tweet_id=0)
#print("after retweet 2")
#api.print_everything()
#
#api.revert_retweet()
#print("== revert retweet 1")
#api.print_everything()
#api.revert_retweet()
#print("== revert retweet 2")
#api.print_everything()

### post_tweet
#api.authenticate_twitter(username='john',password='john1234')
#api.post_tweet(content='NEW TWEET BODY',tags=['#TravelUpdate','#BusinessTrip'])
#print("after post tweet 1")
#api.print_everything()
#api.post_tweet(content='Disappointed over my canceled plans.', tags=['#TravelWoes'], mentions=['@CarlinaYates'])
#print("after post tweet 2")
#api.print_everything()
#
#api.revert_post_tweet()
#print("== revert post 1")
#api.print_everything()
#api.revert_post_tweet()
#print("== revert post 2")
#api.print_everything()

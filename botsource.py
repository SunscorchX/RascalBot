import praw

import os
import time


def authenticate():
    print("Authenticating...")
    try:
        # Try to authenticate using heroku vars  
        reddit = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                     client_secret=os.environ['CLIENT_SECRET'],
                     password=os.environ['REDDIT_PASS'],
                     user_agent="RascalBot v0.1",
                     username="RascalBot")
    except:
        # Import praw.ini for local testing (AppData/Roaming)
        reddit = praw.Reddit('RascalBot', user_agent="RascalBot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))

    return reddit


def main():
    reddit = authenticate()
    active_sub = "WoWAnarchy"
    while True:
        run_bot(reddit,active_sub)


def run_bot(reddit,active_sub):
    for new_post in reddit.subreddit(active_sub).new():
        if new_post.num_comments == 0 or not new_post.comments[0].stickied:
            this_comment = new_post.reply("This is an automated reply. Neat")
            this_comment.mod.distinguish(sticky=True)

    print("10 second recharge.")
    time.sleep(10)


if __name__ == '__main__':
    main()

import praw

import os
import time
import pprint

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


def clear_sticky(this_post):
    for c_check in this_post.comments:
        if c_check.stickied:
            print("Removing previously stickied comment (" + c_check.id + ").")
            c_check.mod.remove()
            return

def main():
    reddit = authenticate()
    active_sub = "RascalBotTest"
    
    waiting = 0
    
    post_stream = reddit.subreddit(active_sub).stream.submissions(pause_after=-1, skip_existing=True)
    comment_stream = reddit.subreddit(active_sub).stream.comments(pause_after=-1, skip_existing=True)
    
    while True:
        for post in post_stream:
            if post is None:
                break
            waiting = 0
            print("Analysing new post (" + post.id + ").")
            posts_check(reddit,post)
        for comment in comment_stream:
            if comment is None:
                if waiting == 2:
                    print("Waiting on new content to analyse.")
                waiting += 1
                break
            waiting = 0
            print("Analysing new comment (" + comment.id + ").")
            comments_check(comment)


def posts_check(reddit,new_post):
    #pprint.pprint(vars(new_post))
    if len(new_post.comments) == 0 or not new_post.comments[0].stickied:
        sticky_exists = False
        if new_post.link_flair_text == None:
            new_post.mod.flair(text="True Anarchy")
        elif "Question" in new_post.link_flair_text:
            print("Detected post " + new_post.id + " as new Question.")
            this_comment = new_post.reply("Beep boop. I noticed that you're asking a question!")
            this_comment.mod.distinguish(sticky=True)
            sticky_exists = True
        if not sticky_exists:
            print("Detected post " + new_post.id + " as new Anarchy.")
            this_comment = new_post.reply("This is an automated reply. Neat")
            this_comment.mod.distinguish(sticky=True)


def comments_check(new_comment):
    c_submission = new_comment.submission
    if not hasattr(new_comment, 'removed'):
        print("Correcting missing attribute.")
        setattr(new_comment, 'removed', False)
    if "Question" in c_submission.link_flair_text and not "FAQ Response" in c_submission.link_flair_text and not new_comment.removed:
        faq_response = faq_lookup(new_comment.body)
        if not faq_response == "N/A":
            print("Found command in comment " + new_comment.id + ".")
            clear_sticky(c_submission)
            this_comment = new_comment.submission.reply(faq_response)
            print("Stickying FAQ response (" + this_comment.id + ") and removing command.")
            this_comment.mod.distinguish(sticky=True)
            new_comment.mod.remove()
            print("Altering post flair.")
            c_submission.mod.flair(text="FAQ Response")


def faq_lookup(t):
    choices = {
        '!server' : "You asked about servers!",
        '!class' : "You asked about classes!"
        }
    return choices.get(t, "N/A")


if __name__ == '__main__':
    main()
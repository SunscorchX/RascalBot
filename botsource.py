import praw

import os
import re
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


# Find sticky comment in submission. Remove if remove = true.
def find_sticky(this_post,remove=False):
    this_post.comment_limit = 1
    for c_check in this_post.comments:
        if c_check.stickied:
            if remove:
                print("Removing previously stickied comment (" + c_check.id + ").")
                c_check.mod.remove()
            else:
                print("Located sticky comment (" + c_check.id + ").")
            return c_check
        else:
            suffix = "found."
            if remove:
                suffix = "to remove."
            print("No sticky comment " + suffix)
            return None

def main():
    reddit = authenticate()
    active_sub = "RascalBotTest"
    
    main.mod_list = []
    for mod_sub in reddit.user.me().moderated():
        main.mod_list.append(mod_sub.display_name)
        
    main.faq_root = reddit.subreddit("WoWAnarchy")
    
    waiting = 0
    
    post_stream = reddit.subreddit(active_sub).stream.submissions(pause_after=-1, skip_existing=True)
    comment_stream = reddit.subreddit(active_sub).stream.comments(pause_after=-1, skip_existing=True)
    
    while True:
        for post in post_stream:
            if post is None:
                break
            waiting = 0
            print("Analysing new post (" + post.id + ").")
            posts_check(post)
        for comment in comment_stream:
            if comment is None:
                if waiting == 2:
                    print("Waiting on new content to analyse.")
                waiting += 1
                break
            waiting = 0
            print("Analysing new comment (" + comment.id + ").")
            comments_check(comment)


def posts_check(new_post):
    #pprint.pprint(vars(new_post))
    if find_sticky(new_post) == None:
        sticky_exists = False
        if new_post.link_flair_text == None:
            new_post.mod.flair(text="True Anarchy")
        elif "Question" in new_post.link_flair_text:
            print("Detected post " + new_post.id + " as new Question.")
            if new_post.subreddit.display_name in main.mod_list:
                this_comment = new_post.reply("Beep boop. I noticed that you're asking a question!")
                this_comment.mod.distinguish(sticky=True)
                sticky_exists = True
        if not sticky_exists:
            print("Detected post " + new_post.id + " as new Anarchy.")
            this_comment = new_post.reply("This is an automated reply. Neat")
            this_comment.mod.distinguish(sticky=True)
    else:
        print("Found post with a sticky. Weird.")
        
def error_pm(comment,command):
    print("Sending PM to " + comment.author.name + " for trying to use \"!" + command + "\".")
    comment.author.message("RascalBot Command Error", "It appears you attempted to use the command \"!" + command + "\" in your comment:\n\n"
        + comment.permalink + "\n\nThis is either not a real command, or you used it in an improper context.\n\n"
        "Watch yourself, eh?")


def comments_check(new_comment):
    c_submission = new_comment.submission
    if re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body):
        found_command = re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body).group(1)
        faq_response = faq_lookup(found_command)
        if "Question" in c_submission.link_flair_text and faq_response:
            print("Found FAQ command \"!" + found_command + "\".")
            find_sticky(c_submission,True)
            faq_comment = new_comment.submission.reply(faq_response)
            print("Stickying FAQ response (" + faq_comment.id + ") and removing command.")
            faq_comment.mod.distinguish(sticky=True)
            new_comment.mod.remove()
            print("Setting post flair to \"FAQ Response\".")
            c_submission.mod.flair(text="FAQ Response")
        elif "FAQ Response" in c_submission.link_flair_text and new_comment.is_submitter and found_command == "clearfaq":
            print("Found \"!clearfaq\" command. Resetting flair.")
            find_sticky(c_submission,True)
            new_comment.mod.remove()
            c_submission.mod.flair(text="Question")
        else:
            print("Removing comment with invalid \"!" + found_command + "\" code.")
            new_comment.mod.remove()
            error_pm(new_comment,found_command)


def faq_lookup(c):
    response = None
    commands = ["server", "class"]
    if c in commands:
        wikipage = "faq/" + c
        response = main.faq_root.wiki[wikipage].content_md
    return response


if __name__ == '__main__':
    main()
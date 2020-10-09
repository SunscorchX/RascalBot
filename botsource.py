import praw

import os
import re
import time
import pprint
import random

def authenticate():
    print("Authenticating...")
    try:
        # Try to authenticate using heroku vars  
        reddit = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                     client_secret=os.environ['CLIENT_SECRET'],
                     refresh_token=os.environ['REFRESH_TOKEN'],
                     user_agent="RascalBot v0.1")
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

def classdict_constructor():
    classdict = {
        'Death Knight' : { 'class' : True, 'tank' : True, 'heal' : False, 'mdps' : True, 'rdps' : False},
        'Demon Hunter' : { 'class' : True, 'tank' : True, 'heal' : False, 'mdps' : True, 'rdps' : False},
        'Druid' : { 'class' : True, 'tank' : True, 'heal' : True, 'mdps' : True, 'rdps' : True},
        'Hunter' : { 'class' : True, 'tank' : False, 'heal' : False, 'mdps' : True, 'rdps' : True},
        'Mage' : { 'class' : True, 'tank' : False, 'heal' : False, 'mdps' : False, 'rdps' : True},
        'Monk' : { 'class' : True, 'tank' : True, 'heal' : True, 'mdps' : True, 'rdps' : False},
        'Paladin' : { 'class' : True, 'tank' : True, 'heal' : True, 'mdps' : True, 'rdps' : False},
        'Priest' : { 'class' : True, 'tank' : False, 'heal' : True, 'mdps' : False, 'rdps' : True},
        'Rogue' : { 'class' : True, 'tank' : False, 'heal' : False, 'mdps' : True, 'rdps' : False},
        'Shaman' : { 'class' : True, 'tank' : False, 'heal' : True, 'mdps' : True, 'rdps' : True},
        'Warlock' : { 'class' : True, 'tank' : False, 'heal' : False, 'mdps' : False, 'rdps' : True},
        'Warrior' : { 'class' : True, 'tank' : True, 'heal' : False, 'mdps' : True, 'rdps' : False}
    }
    return classdict


def main():
    reddit = authenticate()
    active_sub = "RascalBotTest"
    
    main.mod_list = []
    for mod_sub in reddit.user.me().moderated():
        main.mod_list.append(mod_sub.display_name)
        
    main.faq_root = reddit.subreddit("WoWAnarchy")
    main.commands = main.faq_root.wiki["faq"].content_md.split(",")
    
    main.classdict = classdict_constructor()
    
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
    if not find_sticky(new_post):
        if new_post.subreddit.display_name == "WoWAnarchy" or new_post.subreddit.display_name == "RascalBotTest":
            if not new_post.link_flair_text:
                print("Detected missing flair. Assigned flair \"True Anarchy\".")
                new_post.mod.flair(text="True Anarchy")
            if not new_post.link_flair_text or not "Question" in new_post.link_flair_text:
                print("Detected post " + new_post.id + " as new Anarchy.")
                this_comment = bot_reply(new_post, "This is an automated reply. Neat\n\n---")
                this_comment.mod.distinguish(sticky=True)
        if not new_post.link_flair_text:
            pass
        elif "Question" in new_post.link_flair_text:
            print("Detected post " + new_post.id + " as new Question.")
            this_comment = bot_reply(new_post, "Beep boop. I noticed that you're asking a question!\n\n---")
            this_comment.mod.distinguish(sticky=True)
            sticky_exists = True
        if "balance" in new_post.title.lower()+new_post.selftext.lower():
            print("Is someone complaining about balance? Respond!")
            bot_reply(new_post,"RascalBot likes this old saying:\n\n> Players are great at finding problems and terrible at finding solutions.\n\n"
                      "Feedback in the form of proposed changes is less useful than your feelings on the current mechanics.\n\n---").mod.distinguish()
    else:
        print("Found post with a sticky. Weird.")


def error_pm(comment,command,eligible):
    print("Sending PM to " + comment.author.name + " for trying to use \"!" + command + "\".")
    extra_line = ""
    if not eligible:
        extra_line = " Additionally, some commands (such as FAQ responses) are restricted to accounts that are over a week old and have more than 50 comment karma."
    comment.author.message("RascalBot Command Error", "It appears you attempted to use the RascalBot command \"!" + command + "\" in [this comment]("
        + comment.permalink + "), resulting in an error.\n\nThis may be because the command is not recognised by RascalBot, or you tried to use a real "
        "command in the wrong place." + extra_line + "\n\nWatch yourself, eh?")


def bot_reply(target,body):
    body += "\n\n^For ^more ^info ^on ^RascalBot, ^check ^RascalBot's [^test ^sub ^wiki](http://reddit.com/r/RascalBotTest/wiki/index)."
    reply = target.reply(body)
    return reply


def comments_check(new_comment):
    c_submission = new_comment.submission
    if re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body) and not new_comment.distinguished:
        found_command = re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body).group(1)
        eligible = False
        if new_comment.subreddit.display_name in main.mod_list or (new_comment.author.comment_karma >= 50 and (time.time() - int(new_comment.author.created_utc) >= 604800)):
            eligible = True
        faq_response = faq_lookup(found_command,new_comment)
        if "Question" in c_submission.link_flair_text and faq_response and eligible:
            print("Found FAQ command \"!" + found_command + "\".")
            find_sticky(c_submission,True)
            faq_comment = bot_reply(new_comment.submission,faq_response)
            print("Stickying FAQ response (" + faq_comment.id + ") and removing command.")
            faq_comment.mod.distinguish(sticky=True)
            new_comment.mod.remove()
            print("Setting post flair to \"FAQ Response\".")
            c_submission.mod.flair(text="FAQ Response")
            return
        elif "FAQ Response" in c_submission.link_flair_text and new_comment.is_submitter and found_command == "clearfaq":
            print("Found \"!clearfaq\" command. Resetting flair.")
            find_sticky(c_submission,True)
            new_comment.mod.remove()
            c_submission.mod.flair(text="Question")
            return
        elif "random" in found_command:
            choices = []
            trim_command = found_command.replace("random","")
            for name,specs in main.classdict.items():
                try:
                    if specs[trim_command]:
                        choices.append(name)
                except KeyError:
                    pass
            if len(choices) > 0:
                decision = random.choice(choices)
                print("Found \"!" + found_command + "\" command. Replying with result (" + decision + ")")
                random_comment = bot_reply(new_comment, "You requested a random " + trim_command + "!\n\n"
                                                   "RascalBot is happy to help! The result of your request is...\n\n"
                                                   "...\n\n...\n\n...\n\n#" + decision + "!\n\nRascalBot hopes this"
                                                   " helps you get on with your life <3\n\n---")
                random_comment.mod.distinguish()
                return
        elif not eligible:
            print("Command author ineligible for use.")
        print("Removing comment with invalid \"!" + found_command + "\" code.")
        new_comment.mod.remove()
        error_pm(new_comment,found_command,eligible)
    else:
        print("Ignoring distinguished comment.")
        return


def faq_lookup(c,comment):
    response = None
    if c in main.commands:
        wikipage = "faq/" + c
        response = "User u/" + comment.author.name + " requested this FAQ response from RascalBot using the \"!" + c + "\" command.\n\n---\n\n"
        response += main.faq_root.wiki[wikipage].content_md
        response += "\n\n---\n\n^If ^this ^comment ^does ^not ^apply ^to ^the ^question, ^OP ^can ^reply ^with ^\"!clearfaq\" ^to ^remove ^it."
    return response


if __name__ == '__main__':
    main()
import praw

import os
import re
import time
import json
import pprint
import random
import psycopg2


def authenticate():
    print("Authenticating...")
    # Try to authenticate using heroku vars  
    reddit = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                     client_secret=os.environ['CLIENT_SECRET'],
                     refresh_token=os.environ['REFRESH_TOKEN'],
                     user_agent="RascalBot v0.1")
    print("Authenticated as {}".format(reddit.user.me()))
    return reddit


# Find sticky comment in submission. Remove if remove = true.
def find_sticky(this_post,remove=False):
    this_post.comment_limit = 1
    for c_check in this_post.comments:
        # Pull first comment from forest and check if it is stickied.
        if c_check.stickied and not c_check.removed:
            if remove:
                # If "remove" boolean true then remove found comment.
                print("Removing previously stickied comment (" + c_check.id + ").")
                c_check.mod.remove()
            else:
                # If not set to remove, just report comment as found. 
                print("Located sticky comment (" + c_check.id + ").")
            # Return found comment.
            return c_check
        else:
            # Play with string for grammatical sense, return None if no sticky
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
    reddit.validate_on_submit = True
    
    print("Importing config settings.")
    # Opening config.json
    with open("config.json") as jsonfile:
        main.cfg = json.load(jsonfile)
    
    print("Opening database connection.")
    # Open database connection
    DATABASE_URL = os.environ['DATABASE_URL']
    main.conn = psycopg2.connect(DATABASE_URL, sslmode='allow')
    # Set connection to autocommit all queries
    main.conn.set_session(autocommit=True)
    
    # Store list of subreddits moderated by bot
    main.mod_list = []
    for mod_sub in reddit.user.me().moderated():
        main.mod_list.append(mod_sub.display_name)
        
    # Store root sub for FAQ Wiki
    main.faq_root = reddit.subreddit("WoWAnarchy")
    main.commands = main.faq_root.wiki["faq"].content_md.split(",")
    
    # Store dictionary object for !random commands
    main.classdict = classdict_constructor()
    
    waiting = 0
    
    # Iterate through new posts and comments one by one
    post_stream = reddit.subreddit(main.cfg["active_sub"]).stream.submissions(pause_after=-1, skip_existing=True)
    flair_stream = reddit.subreddit(main.cfg["active_sub"]).mod.stream.log(action="editflair", pause_after=-1, skip_existing=True)
    report_stream = reddit.subreddit(main.cfg["active_sub"]).mod.stream.reports(pause_after=-1, skip_existing=True)
    comment_stream = reddit.subreddit(main.cfg["active_sub"]).stream.comments(pause_after=-1, skip_existing=True)

    while True:
        try:
            for post in post_stream:
                if post is None:
                    break
                waiting = 0
                print("Analysing new post (" + post.id + ").")
                posts_check(post)
            for flair in flair_stream:
                if flair is None:
                    break
                flair_post = flair.target_fullname.replace("t3_", "")
                post = reddit.submission(flair_post)
                print("Detected flair change. Analysing post " + post.id + ".")
                posts_check(post)
            for report in report_stream:
                if report is None:
                    break
                print("Detected new report (" + report.id + ").")
                report_analysis(report)
            for comment in comment_stream:
                if comment is None:
                    if waiting == 4:
                        print("Waiting on new content to analyse.")
                    waiting += 1
                    break
                waiting = 0
                print("Analysing new comment (" + comment.id + ").")
                comments_check(comment)
        except Exception as err:
            print(err)
    # Close database connection if we ever exit loop
    main.conn.close()

def posts_check(new_post):
    # Check for existing sticky
    if not find_sticky(new_post):
        if not new_post.link_flair_text:
            print("No flair. Let Autobot handle it!")
        # Hide and respond to all posts tagged "Art"
        elif main.cfg["advanced"]["manage_art"] and "Art" in new_post.link_flair_text:
            print("Detected post " + new_post.id + " as new Art submission.")
            this_comment = bot_reply(new_post, "Hello! RascalBot has removed your art post until you link your source.\n\n"
                                     "Remember, the artist must be credited in the **title** too! (Except for tattoo posts.)  \n"
                                     "If you haven't done that, resubmit your post with title credit and don't reply to this comment.\n\n---\n\n"
                                     "If you did give credit in the title, please reply to this comment with one of the following:\n\n"
                                     "* A link to the artist's portfolio, social media, or reddit profile.\n"
                                     "* \"I made this\", if the art is original content.\n"
                                     "* \"Tattoo\", if you don't wish to reveal your location by sharing studio details.\n\n---", True)
            print("Stickying source request (" + this_comment.id + ") and hiding post.")
            new_post.mod.remove()
            print("Saving comment ID to database.")
            cur = main.conn.cursor()
            cur.execute("INSERT INTO bot_comments (id, timestamp, action) VALUES (%s, NOW(), %s)",
                        (this_comment.id, "Source"))
            cur.close()
        # Add generic FAQ response to all posts tagged "Question"
        elif main.cfg["posts"]["reply_questions"] and "Question" in new_post.link_flair_text:
            print("Detected post " + new_post.id + " as new Question.")
            this_comment = bot_reply(new_post, "Beep boop. I noticed that you're asking a question!\n\n---", True)
            sticky_exists = True
        # Add snark to any post talking about balance
        elif main.cfg["posts"]["reply_balance"] and "balance" in new_post.title.lower()+new_post.selftext.lower():
            print("Is someone complaining about balance? Respond!")
            bot_reply(new_post,"RascalBot likes this old saying:\n\n> Players are great at finding problems and terrible at finding solutions.\n\n"
                      "Feedback in the form of proposed changes is less useful than your feelings on the current mechanics.\n\n---")
    else:
        print("Found post with a sticky. Weird.")


def error_pm(comment,command,eligible):
    if not main.cfg["other"]["error_pm"]:
        return
    print("Sending PM to " + comment.author.name + " for trying to use \"!" + command + "\".")
    extra_line = ""
    # Add extra info to PM if user does not meet command requirements
    if not eligible:
        extra_line = " Additionally, some commands (such as FAQ responses) are restricted to accounts that are over a week old and have more than 50 comment karma."
    # Send PM to user who did it wrong
    comment.author.message("RascalBot Command Error", "It appears you attempted to use the RascalBot command \"!" + command + "\" in [this comment]("
        + comment.permalink + "), resulting in an error.\n\nThis may be because the command is not recognised by RascalBot, or you tried to use a real "
        "command in the wrong place." + extra_line + "\n\nWatch yourself, eh?")


def bot_reply(target,body,c_sticky=False):
    # Add generic bot footer to all bot comments, return created comment
    body += "\n\n^For ^more ^info ^on ^RascalBot, ^check ^RascalBot's [^wowmeta ^post](https://www.reddit.com/r/wowmeta/comments/jdtn0i/)^."
    reply = target.reply(body)
    reply.disable_inbox_replies()
    reply.mod.distinguish(sticky=c_sticky)
    return reply


def comments_check(new_comment):
    c_submission = new_comment.submission
    if not c_submission.link_flair_text:
        c_submission.link_flair_text = ""
    # Construct regex for screenshot bullshit
    ss_regex = re.compile(r"""
        (?:^|[\.!\?])(?:[^\.!\?\n]*?                                            # Start capture at new line/sentence, continue for * sentence characters
        (can'?t|know|learn|god|fuck|shit|damn?|next\stime)                      # Try to capture pre-keyword indicators
        )?[^\.!\?\n]*?                                                          # Continue for * sentence characters
        (?:screen\s?shot|print\s?screen)                                        # Match key words "screenshot" or "printscreen"
        (?:[^\.!\?\n]*?                                                         # Continue for * sentence characters
        (can'?t|key|button|god|fuck|shit|damn?|next\stime)                      # Try to match post-keyword indicators
        )?[^\.!\?\n]*?(?:[\.!\?\n]|$)                                           # End capture after * sentence characters followed by sentence end
        """, re.IGNORECASE|re.VERBOSE)
    ss_match = ss_regex.search(new_comment.body)
    ss_flag = False
    if re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body) and not new_comment.distinguished and not new_comment.removed:
        found_command = re.search(r"(?:^|\s)!([a-zA-Z]*\b)", new_comment.body).group(1)
        eligible = False
        if new_comment.subreddit.display_name in main.mod_list or (new_comment.author.comment_karma >= 50 and (time.time() - int(new_comment.author.created_utc) >= 604800)):
            eligible = True
        faq_response = faq_lookup(found_command,new_comment)
        if main.cfg["comments"]["faq_commands"] and "Question" in c_submission.link_flair_text and faq_response and eligible:
            print("Found FAQ command \"!" + found_command + "\".")
            find_sticky(c_submission,True)
            faq_comment = bot_reply(new_comment.submission,faq_response, True)
            print("Stickying FAQ response (" + faq_comment.id + ") and removing command.")
            new_comment.mod.remove()
            print("Setting post flair to \"FAQ Response\".")
            c_submission.mod.flair(text="FAQ Response")
            return
        elif main.cfg["comments"]["clear_faq"] and "FAQ Response" in c_submission.link_flair_text and new_comment.is_submitter and found_command == "clearfaq":
            print("Found \"!clearfaq\" command. Resetting flair.")
            find_sticky(c_submission,True)
            new_comment.mod.remove()
            c_submission.mod.flair(text="Question")
            return
        elif main.cfg["comments"]["random_commands"] and "random" in found_command:
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
                return
        elif not eligible:
            print("Command author ineligible for use.")
        print("Removing comment with invalid \"!" + found_command + "\" code.")
        new_comment.mod.remove()
        error_pm(new_comment,found_command,eligible)
    elif main.cfg["advanced"]["manage_art"] and "Art" in c_submission.link_flair_text and new_comment.is_submitter and c_submission.removed:
        parent_id = re.search(r"t[13]_(.*)", new_comment.parent_id).group(1)
        # Checking database for comment ID
        cur = main.conn.cursor()
        cur.execute("SELECT * FROM bot_comments WHERE id = (%s) AND action = 'Source';", (parent_id,))
        result = cur.fetchone()
        cur.close()
        if not result is None:
            print("Found art source submission. Analysing content.")
            link_info = None
            # Check comment for some sort of link with or without markdown
            link_parse = re.search(r"((?:\[.*\])|(?:https*:\/\/))\(?((?:https*:\/\/)?[^\s\)]*)\)?(?:\s|$)", new_comment.body)
            if not link_parse is None:
                # Use own markdown for bare link
                if "http" in link_parse.group(1):
                    link_info = "[Link to Source](" + link_parse.group(1) + link_parse.group(2) + ")"
                # Use submitter's markdown for formatted link
                elif "[" in link_parse.group(1):
                     link_info = link_parse.group()
            elif "i made this" in new_comment.body.lower():
                link_info = "This art was created by the OP! RascalBot is impressed!"
            elif "tattoo" in new_comment.body.lower():
                link_info = ("RascalBot does not require users to potentially doxx themselves " +
                             "when posting tattoo images! No source required.")
            if not link_info is None:
                print("Detected source information. Updating sticky & database.")
                bot_parent = new_comment.parent()
                bot_parent.edit("Source submitted by " + new_comment.author.name + ":\n\n"
                                          + link_info + "\n\n---"
                                          "\n\n^For ^more ^info ^on ^RascalBot, ^check ^RascalBot's "
                                          "[^wowmeta ^post](https://www.reddit.com/r/wowmeta/comments/jdtn0i/)^.")
                bot_parent.mod.lock()
                c_submission.mod.approve()
                cur = main.conn.cursor()
                cur.execute("UPDATE bot_comments SET (timestamp, action) = (NOW(), %s) WHERE id = %s", ("Review", parent_id))
                cur.close()
            else:
                print("Failed to find source info. Replying to comment.")
                this_comment = bot_reply(new_comment, "RascalBot was unable to detect a link in this message.\n\n"
                                         "If you believe this is a mistake, please send a modmail so the team can fix RascalBot\n\n---")
        else:
            print("The parent is not being monitored for replies right now.")
    elif main.cfg["comments"]["reply_ss"] and ss_match is not None and (ss_match.group(1) is not None or ss_match.group(2) is not None):
        # Check for disqualifying indicators here
        if "because" not in ss_match.group():
            ss_flag = True
            print("Found crappy \"screenshot\" comment. Responding.")
            this_comment = bot_reply(new_comment, "RascalBot wants you to know that "
                                    "telling people to use a screenshot isn't all that helpful.\n\n" 
                                    "Let's just not do that anymore.\n\n---")
    if ss_match is not None and not new_comment.distinguished:
        print("Saving comment to ss_record.")
        cur = main.conn.cursor()
        cur.execute("INSERT INTO ss_record (content, flag) VALUES (%s, %s)",
            (ss_match.group(), ss_flag))
        cur.close

def report_analysis(report):
    if not main.cfg["other"]["old_reports"]:
        return
    content_age = time.time() - report.created_utc
    #limit = 604800
    limit = 15768000
    if content_age >= limit:
        print("Old-ass report found. Automatically approving.")
        report.mod.approve()


def faq_lookup(c,comment):
    response = None
    if c in main.commands:
        wikipage = "faq/" + c
        response = "User u/" + comment.author.name + " requested this FAQ response from RascalBot using the \"!" + c + "\" command.\n\n---\n\n"
        response += main.faq_root.wiki[wikipage].content_md
        response += "\n\n---\n\n^If ^this ^comment ^does ^not ^apply ^to ^the ^question, ^OP ^can ^reply ^with ^\"!clearfaq\" ^to ^remove ^it."
    return response


def codegen():
    print("Authenticating...")
    # Try to authenticate using heroku vars  
    reddit = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                client_secret=os.environ['CLIENT_SECRET'],
                redirect_uri="http://localhost:8080",
                user_agent="RascalBot v0.1")
    #print(reddit.auth.url(["identity edit modflair modlog modposts mysubreddits privatemessages read report submit wikiread"], "...", "permanent"))
    print(reddit.auth.authorize("code"))
    print(reddit.user.me())
    return

if __name__ == '__main__':
    main()
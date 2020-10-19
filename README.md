# RascalBot Feature List:

#### General:
* Currently processes all new:
  * Posts
  * Comments
  * Flair Changes
  * Reports
* Refresh Token Authentication - allows bot account to use 2FA, and not store main credentials anywhere!
* Automatically ignores (approves) any report on a post/comment older than six months.
* Prints exceptions to server log and continues main loop, rather than crashing.
* Distinguishes (sticky optional) and turns off reply notifications to all bot comments.
* Loads config.json on start to determine which modules are active.

#### Basic Post Processing:
* Re-processes any post that has its link flair edited.
* Adds generic pinned comment to all posts flaired as "Question" (**Needs to be properly written!**)
* Makes snarky reply to posts that mention balance.

#### Basic Comment Processing:
* Allows week-old user accounts with 50+ karma to use FAQ commands in replies to "Question" posts.
  * Reflairs any post with a confirmed command to "FAQ Response". Lets people filter FAQ threads.
* Allows the OP of an "FAQ Response" post to clear the sticky and restore the original flair if their question is not answered.
* Looks for "!random" commands and replies appropriately. (**Currently only covers classes/roles**).
* Sends short error message to anyone using commands incorrectly/making up commands via PM.
* Replies to any post detected as being a dick about using print screen with a light admonishment.

# Advanced Processing:
#### Art Post Sourcing:
* Removes new Art posts and adds a sticky comment asking for a source. Records sticky comment ID to database.
* Monitors OP comments in hidden Art threads, compares parent ID to database record.
* Parses links (unformatted and in markdown), and "I made this" to determine source information.
* If source is found, edits sticky, reapproves post, and updates database. Else, replies with error message.
* **Sticky comment templates still need workshopping; no copy is finalised!**

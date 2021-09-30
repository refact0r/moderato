# moderato

an advanced moderation discord bot

active project so expect bugs

## features

- variety of punishments
  - mute - prevent users from sending messages
  - freeze - prevent users from reacting or sending files
  - exile - prevent users from seeing channels
  - ban
  - kick
- timed punishments
- advanced argument parser
  - allows for punishing multiple specific members, all members with a role, or everyone in a server with a single command
- other moderation features like purging messages
- logical error messages

## getting started

invite link: https://discord.com/api/oauth2/authorize?client_id=804104627829211146&permissions=536870911991&scope=bot

type `%help` to see a list of all commands.

type `%help [name of command]` to see info on how to use a specific command

## contributing

1. fork this repository or download it
2. go to <https://discord.com/developers/applications> and create a new application
3. go to the Bot page and copy the token
4. paste the token inside the quotes `token = ""` in the `bot.py` file from this repository
5. run `bot.py`, it should say `bot has connected to discord` in your terminal
6. to invite the bot to a server, go back to discord developer portal and go to the OAuth2 page
7. scroll down to the OAuth2 URL Generator and check the box that says bot inside the scopes box
8. then in the bot permissions box and check permissions that you want the bot to have
9. copy the link in the scopes box, visit it, and complete all the normal stuff for inviting bots
10. hopefully the bot should be online and commands that don't require a database will work

# Next Bus Bot (WIP)

Discord Bot that lets users schedule notifications with bus times from the [NextBus API](https://gist.github.com/grantland/7cf4097dd9cdf0dfed14). The bot uses MongoDB to manage the scheduled notifications.

Great for school or work discords!

The bot works for any bus system that uses NextBus to provide time predictions. You can add the bot to your server [here](https://discordapp.com/oauth2/authorize?client_id=454489707360026626&scope=bot).

You can vote for it on discordbots.org [here](https://discordbots.org/bot/454489707360026626). 

# How to Run

To add the notification feature to a pre-existing bot, you need to connect to a [MongoDB](https://www.mongodb.com/), and add the cog in the ```cogs``` folder to your cogs.
Here's an [example](https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5) of using cogs.

If you want to run the bot with just the notification feature, you can clone or [download](https://github.com/kajchang/next-bus-bot/archive/master.zip) this code. You will also need to connect to a [MongoDB](https://www.mongodb.com/).
Then, create the ```TOKEN``` environment variable with a Discord bot token ([guide](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)) and run ```nextbusbot.py```.

# Commands

The bot currently only takes commands (except for !bus info) in private messages. The bot's prefix is '!bus '.

### !bus start

The bot will give you basic information on itself and its commands.

### !bus add

The bot will give you prompts to configure a notification.

### !bus list

The bot will list all current notifications with corresponding IDs for use when calling /delete.

### !bus delete|d|D -id

The bot will delete the specified notification.

### !bus change|c|C -action -id

The bot will give you prompts to edit the stop and line of the given notification.

To edit time, the action parameter should be time or t.

To edit stop, the action parameter should be stop or s.

### !bus info
The bot will provide the number of servers it is a part of and its invite link.

# TODO

- Ability to set notifications to weekdays only

- Provide alternative (faster) routes

# Next Bus Bot (WIP)

Discord Bot that lets users schedule notifications with bus times from the [NextBus API](https://gist.github.com/grantland/7cf4097dd9cdf0dfed14). Discord Bot uses MongoDB to manage the scheduled notifications.

It works for any bus system that uses NextBus. You can add the bot to your server [here](https://discordapp.com/oauth2/authorize?client_id=454489707360026626&scope=bot). The uptime will be kind of flaky while I run it from my personal computer, but I will migrate it to AWS in the future.

## Commands

The bot currently only takes commands in private messages.

### /start
The bot will give you basic information on the bot

### /add
The bot will give your prompts to configure a notification.

# TODO

- Let users edit and delete notifications

- Ability to set notifications to weekdays only

- Improve readability

- Add some general features

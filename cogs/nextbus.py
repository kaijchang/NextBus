from discord.ext import commands
import discord
import datetime
import time
import asyncio
from pymongo import MongoClient
import json
import aiohttp


class NextBus:
    def __init__(self, bot):

        # Load the timezones for the different bus systems.
        self.time_zones = json.load(open('timezones.json'))

        # Connect to local MongoDB.
        self.client = MongoClient()
        self.db = self.client.next_bus_db

        self.bot = bot
        self.bot.loop.create_task(self.notifier())

        self.in_commands = []

    @commands.command(
        pass_context=True,
        description='The bot will give you basic information on itself and its commands.')
    async def start(self, ctx):
        if not ctx.message.channel.is_private:
            # Tell user to PM bot if called in public channel.
            await self.bot.say("Sorry, I can't you with so many people watching....\nPM me!")

        elif ctx.message.author.id in self.in_commands:
            return

        else:
            # Introduce the bot and supply current bot commands.
            embed = discord.Embed(
                title="Commands",
                type='rich',
                colour=discord.Colour(0x37980a))
            embed.add_field(name='!bus add', value='Make a notification.')
            embed.add_field(name='!bus list',
                            value='List current notifications.')
            embed.add_field(
                name='!bus d <id>',
                value="Delete the notification with the given ID (see all notifications with '!bus list')")
            embed.add_field(name='!bus info',
                            value='Bot statistics and link to add the bot.')
            embed.add_field(
                name='!bus change <time / stop> <id>',
                value="Edit the time or stop of the specified notification (see all notifications with '!bus list')")

            await self.bot.say("Let's get going!", embed=embed)

    @commands.command(pass_context=True, description="Bot Information")
    async def info(self, ctx):
        embed = discord.Embed(
            title="NextBusBot",
            type='rich',
            description="Get Bus Notifications from NextBus!",
            color=0x37980a)

        embed.add_field(name="Server Count", value=len(self.bot.servers))
        embed.add_field(
            name="Invite Me",
            value="[Invite link](https://discordapp.com/oauth2/authorize?client_id=454489707360026626&scope=bot)")

        await self.bot.say(embed=embed)

    @commands.command(
        pass_context=True,
        description="The bot will list all current notifications with corresponding IDs for use when calling '!bus delete' or '!bus change'.")
    async def list(self, ctx):
        if not ctx.message.channel.is_private:
            # Tell user to PM bot if called in public channel.
            await self.bot.say("Sorry, I can't you with so many people watching....\nPM me!")

        elif ctx.message.author.id in self.in_commands:
            return

        else:
            # Find all notifications that the user hsa created.
            user_notifications = [t for t in self.db.posts.find(
                {'user': ctx.message.author.id})]

            if len(user_notifications) > 0:
                # Provide user with matching notifications and ask them to
                # choose one.
                embed = discord.Embed(
                    title="Current Notifcations",
                    type='rich',
                    colour=discord.Colour(0x37980a))

                for t in zip(range(1, len(user_notifications) + 1), user_notifications):
                    # Convert time from UTC to local time.
                    converted_time = t[1]['time1'] + \
                        self.time_zones[t[1]['system']['tag']] * 60

                    # Wrap around midnight.
                    if converted_time < 0:
                        converted_time += 1440

                    formatted_time_1 = str(
                        datetime.time(
                            divmod(
                                converted_time, 60)[0], divmod(
                                converted_time, 60)[1]))

                    # Convert time from UTC to local time.
                    converted_time = t[1]['time2'] + \
                        self.time_zones[t[1]['system']['tag']] * 60

                    # Wrap around midnight.
                    if converted_time < 0:
                        converted_time += 1440

                    formatted_time_2 = str(
                        datetime.time(
                            divmod(
                                converted_time, 60)[0], divmod(
                                converted_time, 60)[1]))

                    embed.add_field(name=t[0], value='{} at {}\n{} at {}'.format(
                        t[1]['stop1']['title'], formatted_time_1, t[1]['stop2']['title'], formatted_time_2), inline=False)

                await self.bot.say(embed=embed)

            else:
                await self.bot.say("No notifications found.\nUse '!bus add' to add a notification.")

    @commands.command(
        pass_context=True,
        aliases=[
            'd',
            'D'],
        description='The bot will delete the specified notification.')
    async def delete(self, ctx, ID: int):
        if not ctx.message.channel.is_private:
            # Tell user to PM bot if called in public channel.
            await self.bot.say("Sorry, I can't you with so many people watching....\nPM me!")

        elif ctx.message.author.id in self.in_commands:
            return

        else:
            # Find all notifications that the user hsa created.
            user_notifications = [t for t in self.db.posts.find(
                {'user': ctx.message.author.id})]

            # Delete the specified notification.
            try:
                notification = user_notifications[ID - 1]

                self.db.posts.remove(notification)

            except IndexError:
                await self.bot.say("Sorry, I couldn't find the specified notification.\nUse '!bus list' to see the IDs of all your current notifications")
                return

            # Tell the user that the operation succeeded.
            await self.bot.say(embed=self.notification_embed('Notification Deleted!', notification))

    @delete.error
    async def delete_handler(self, error, ctx):
        if isinstance(error, commands.BadArgument):
            await self.bot.say("The specified ID isn't a number")

        if isinstance(error, commands.MissingRequiredArgument):
            await self.bot.say("You forgot to include an ID for me to delete.\nUse '!bus list' to view all your notifications.")

    @commands.command(
        pass_context=True,
        description='The bot will prompt you to modify the specified notification.',
        aliases=['c', 'C'])
    async def change(self, ctx, action, ID: int):
        if not ctx.message.channel.is_private:
            # Tell user to PM bot if called in public channel.
            await self.bot.say("Sorry, I can't you with so many people watching....\nPM me!")
            return

        elif ctx.message.author.id in self.in_commands:
            return

        else:
            # Find all notifications that the user has created.
            user_notifications = [t for t in self.db.posts.find(
                {'user': ctx.message.author.id})]

            # Find the specified notification
            try:
                notification = user_notifications[ID - 1]

                await self.bot.say('Notification Found!', embed=self.notification_embed('Notification Info', notification))

            except IndexError:
                await self.bot.say("Sorry, I couldn't find the specified notification.\nUse '!bus list' to see the IDs of all your current notifications")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

            # Don't allow user to use any other commands while in this one.
            self.in_commands.append(ctx.message.author.id)

            if action.lower() in ['time', 't']:
                # The bot asks for a time to notify the user for the first stop.
                embed = discord.Embed(
                    title='When should I notify you for the first (starting) stop?',
                    type='rich',
                    colour=discord.Colour(0x37980a))

                embed.add_field(name='Time Examples',
                                value='16 30, 16:30, 4:30 PM, 4 30 PM')

                await self.bot.say(embed=embed)

                time_choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not time_choice:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                try:
                    time_1 = self.parseUserTime(time_choice.content)

                    # Check if the time, when converted to UTC, needs to wrap back
                    # around midnight.
                    if time_1 - self.time_zones[notification['system']['tag']] * 60 > 1440:
                        # Wrap back around midnight.
                        time_1 = time_1 - \
                            self.time_zones[notification['system']
                                            ['tag']] * 60 - 1440

                    else:
                        time_1 = time_1 - \
                            self.time_zones[notification['system']['tag']] * 60

                except Exception:
                    # Tell user that there is an error.
                    await self.bot.say("I couldn't understand your time format.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                # The bot asks for a time to notify the user for the second stop.
                embed = discord.Embed(
                    title='When should I notify you for the second (destination) stop?',
                    type='rich',
                    colour=discord.Colour(0x37980a))

                embed.add_field(name='Time Examples',
                                value='16 30, 16:30, 4:30 PM, 4 30 PM')

                await self.bot.say(embed=embed)

                time_choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not time_choice:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                try:
                    time_2 = self.parseUserTime(time_choice)

                    # Check if the time, when converted to UTC, needs to wrap back
                    # around midnight.
                    if time_2 - self.time_zones[notification['system']['tag']] * 60 > 1440:
                        # Wrap back around midnight.
                        time_2 = time_2 - \
                            self.time_zones[notification['system']
                                            ['tag']] * 60 - 1440

                    else:
                        time_2 = time_2 - \
                            self.time_zones[notification['system']['tag']] * 60

                except Exception:
                    # Tell user that there is an error.
                    await self.bot.say("I couldn't understand your time format.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                notification['time1'] = time_1
                notification['time2'] = time_2

                self.db.posts.replace_one(
                    {'_id': notification['_id']}, notification)

                await self.bot.say("Notification updated!",
                                   embed=self.notification_embed('Notification Info', notification))

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

            elif action.lower() in ['stop', 's']:
                # The bot asks the user for a route/line.
                await self.bot.say('Which route/ line do you want to update to?')

                line_choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not line_choice:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                # Get all lines for the given bus system from the NextBus API.
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeList&a={}'.format(notification['system']['tag'])) as response:
                        lines = await response.json()

                # Sort out all the matching lines.
                found_lines = [line for line in lines['route']
                               if line_choice.content.upper() in line['tag']]

                if not found_lines:
                    # Tell user that no bus systems were found.
                    await self.bot.say(
                        "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                elif len(found_lines) == 1:
                    line = found_lines[0]

                else:
                    # Provide user with the matching lines and ask them to
                    # choose one.
                    embed = discord.Embed(
                        title='Choose a line by number.',
                        type='rich',
                        colour=discord.Colour(0x37980a))

                    for t in zip(range(1, len(found_lines) + 1),
                                 [d['title'] for d in found_lines]):
                        embed.add_field(name=t[0], value=t[1], inline=False)

                    await self.bot.say('I found {} matching lines(s).'.format(len(found_lines)), embed=embed)

                    choice = await self.bot.wait_for_message(
                        author=ctx.message.author, timeout=300)

                    if not choice:
                        # Tell user when bot.wait_for_message times out.
                        await self.bot.say("Sorry, I didn't pick up a response.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                    try:
                        line = found_lines[int(choice.content) - 1]

                    except IndexError:
                        # Tell the user if they provide an invalid index.
                        await self.bot.say("I don't think that's a valid choice.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                await self.bot.say('You selected {}!'.format(line['title']))

                # The bot asks the user for a stop.
                await self.bot.say('What do you want to change the first stop to?')

                stop_choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not stop_choice:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                # Get all routes for the given bus and line from the NextBus API.
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(notification['system']['tag'], line['tag'])) as response:
                        route_data = await response.json()

                # Separate stop data and directional (in/outbound) data
                stops = route_data['route']['stop']
                direction_data = route_data['route']['direction']

                # Sort out all matching stops.
                found_stops = [
                    stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

                # Sort out all directional data for the matching stops.
                directions = [
                    direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
                        stop['tag'] for stop in direction['stop']]]

                if not found_stops:
                    # Tell user that no matching stops were found.
                    await self.bot.say(
                        "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

                elif len(found_stops) == 1:
                    stop_1 = found_stops[0]

                else:
                    # Provide user with the matching lines and ask them to choose one.
                    embed = discord.Embed(
                        title='Choose a stop by number.',
                        type='rich',
                        colour=discord.Colour(0x37980a))

                    for t in zip(range(1, len(found_stops) + 1),
                                 [d['title'] for d in found_stops], directions):
                        embed.add_field(
                            name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)

                    await self.bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

                    choice = await self.bot.wait_for_message(
                        author=ctx.message.author, timeout=300)

                    if not choice:
                        # Tell user when bot.wait_for_message times out.
                        await self.bot.say("Sorry, I didn't pick up a response.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                    try:
                        stop_1 = found_stops[int(choice.content) - 1]

                    except IndexError:
                        # Tell the user if they provide an invalid index.
                        await self.bot.say("That's not a valid choice.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                await self.bot.say('You selected {}!'.format(stop_1['title']))

                # The bot asks the user for a second stop.
                await self.bot.say('What do you want to change the second stop to?')

                stop_choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not stop_choice:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

                # Get all routes for the given bus and line from the NextBus API.
                async with aiohttp.ClientSession() as session:
                    async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(notification['system']['tag'], line['tag'])) as response:
                        route_data = await response.json()

                # Separate stop data and directional (in/outbound) data
                stops = route_data['route']['stop']
                direction_data = route_data['route']['direction']

                # Sort out all matching stops.
                found_stops = [
                    stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

                # Sort out all directional data for the matching stops.
                directions = [
                    direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
                        stop['tag'] for stop in direction['stop']]]

                if not found_stops:
                    # Tell user that no matching stops were found.
                    await self.bot.say(
                        "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

                elif len(found_stops) == 1:
                    stop_2 = found_stops[0]

                else:
                    # Provide user with the matching lines and ask them to choose one.
                    embed = discord.Embed(
                        title='Choose a stop by number.',
                        type='rich',
                        colour=discord.Colour(0x37980a))

                    for t in zip(range(1, len(found_stops) + 1),
                                 [d['title'] for d in found_stops], directions):
                        embed.add_field(
                            name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)

                    await self.bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

                    choice = await self.bot.wait_for_message(
                        author=ctx.message.author, timeout=300)

                    if not choice:
                        # Tell user when bot.wait_for_message times out.
                        await self.bot.say("Sorry, I didn't pick up a response.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                    try:
                        stop_2 = found_stops[int(choice.content) - 1]

                    except IndexError:
                        # Tell the user if they provide an invalid index.
                        await self.bot.say("That's not a valid choice.")

                        # Allow users to call other commands.
                        self.in_commands.remove(ctx.message.author.id)

                        return

                await self.bot.say('You selected {}!'.format(stop_2['title']))

                notification['stop1'] = stop_1
                notification['stop2'] = stop_2
                notification['line'] = line

                self.db.posts.replace_one(
                    {'_id': notification['_id']}, notification)

                # Provide the user with a summary of their notification.
                await self.bot.say('Notification updated!', embed=self.notification_embed('Notification Info', notification))

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

            else:
                # Tell the user that their supplied action was invalid.
                await self.bot.say("Sorry, couldn't find the part you wanted to edit.\nCheck command usage with '!bus start'.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

    @change.error
    async def change_handler(self, error, ctx):
        if isinstance(error, commands.BadArgument):
            await self.bot.say("The specified ID isn't a number.")

        if isinstance(error, commands.MissingRequiredArgument):
            await self.bot.say("You forgot to include an ID or an action for me to delete.\nUse '!bus list' to view all your notifications or use '!bus start' to get all available commands.")

    @commands.command(
        pass_context=True,
        description='The bot will give you prompts to configure a notification.')
    async def add(self, ctx):
        if not ctx.message.channel.is_private:
            # Tell user to PM bot if called in public channel.
            await self.bot.say("Sorry, I can't you with so many people watching....\nPM me!")
            return

        if ctx.message.author.id in self.in_commands:
            return

        if not [a for a in self.db.posts.find({'user': ctx.message.author.id})]:
            # The bot asks the user for a bus system.
            await self.bot.say("I've got this!\nWhich bus system do you use?")

            # Don't allow user to use any other commands while in this one.
            self.in_commands.append(ctx.message.author.id)

            system_choice = await self.bot.wait_for_message(
                author=ctx.message.author, timeout=300)

            if not system_choice:
                # Tell user when bot.wait_for_message times out.
                await self.bot.say("I didn't pick up a response.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)
                return

            found_busses = []

            # Get all bus systems from the NextBus API.
            async with aiohttp.ClientSession() as session:
                async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=agencyList') as response:
                    bus_list = await response.json()

            for bus in bus_list['agency']:
                # Check to see if any of the bus system's provided identifiers
                # match with user input.
                for attribute in bus:
                    if system_choice.content.lower() in bus[attribute].lower():
                        found_busses.append(bus)
                        break

            if not found_busses:
                # Tell user that no matching bus systems were found.
                await self.bot.say(
                    "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

            elif len(found_busses) == 1:
                bus_system = found_busses[0]

            else:
                # Provide user with the matching bus systems and ask them to choose
                # one.
                embed = discord.Embed(
                    title='Choose a system by number.',
                    type='rich',
                    colour=discord.Colour(0x37980a))

                for t in zip(range(1, len(found_busses) + 1),
                             [d['title'] for d in found_busses]):
                    embed.add_field(name=t[0], value=t[1], inline=False)

                await self.bot.say('I found {} matching bus system(s).'.format(len(found_busses)), embed=embed)

                choice = await self.bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not choice.content:
                    # Tell user when bot.wait_for_message times out.
                    await self.bot.say("Sorry, I didn't pick up a response.")

                try:
                    bus_system = found_busses[int(choice.content) - 1]

                except IndexError:
                    # Tell the user if they provide an invalid index.
                    await self.bot.say("I don't think that's a valid choice.")

                    # Allow users to call other commands.
                    self.in_commands.remove(ctx.message.author.id)

                    return

            await self.bot.say('You selected {}!'.format(bus_system['title']))

        else:
            bus_system = [a for a in self.db.posts.find(
                {'user': ctx.message.author.id})][0]['system']

            await self.bot.say('Automatically selecting {}.'.format(
                bus_system['title']))

        # The bot asks the user for a route/line.
        await self.bot.say('Which route/ line do want to set a notification for?')

        line_choice = await self.bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not line_choice:
            # Tell user when bot.wait_for_message times out.
            await self.bot.say("Sorry, I didn't pick up a response.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        # Get all lines for the given bus system from the NextBus API.
        async with aiohttp.ClientSession() as session:
            async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeList&a={}'.format(bus_system['tag'])) as response:
                lines = await response.json()

        # Sort out all the matching lines.
        found_lines = [line for line in lines['route']
                       if line_choice.content.upper() in line['tag']]

        if not found_lines:
            # Tell user that no bus systems were found.
            await self.bot.say(
                "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        elif len(found_lines) == 1:
            line = found_lines[0]

        else:
            # Provide user with the matching lines and ask them to choose one.
            embed = discord.Embed(
                title='Choose a line by number.',
                type='rich',
                colour=discord.Colour(0x37980a))

            for t in zip(range(1, len(found_lines) + 1),
                         [d['title'] for d in found_lines]):
                embed.add_field(name=t[0], value=t[1], inline=False)

            await self.bot.say('I found {} matching lines(s).'.format(len(found_lines)), embed=embed)

            choice = await self.bot.wait_for_message(
                author=ctx.message.author, timeout=300)

            if not choice:
                # Tell user when bot.wait_for_message times out.
                await self.bot.say("Sorry, I didn't pick up a response.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

            try:
                line = found_lines[int(choice.content) - 1]

            except IndexError:
                # Tell the user if they provide an invalid index.
                await self.bot.say("I don't think that's a valid choice.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

        await self.bot.say('You selected {}!'.format(line['title']))

        # The bot asks the user for a first stop.
        await self.bot.say("What's your first (starting) stop?")

        stop_choice = await self.bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not stop_choice:
            # Tell user when bot.wait_for_message times out.
            await self.bot.say("Sorry, I didn't pick up a response.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        # Get all routes for the given bus and line from the NextBus API.
        async with aiohttp.ClientSession() as session:
            async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(bus_system['tag'], line['tag'])) as response:
                route_data = await response.json()

        # Separate stop data and directional (in/outbound) data
        stops = route_data['route']['stop']
        direction_data = route_data['route']['direction']

        # Sort out all matching stops.
        found_stops = [
            stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

        # Sort out all directional data for the matching stops.
        directions = [
            direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
                stop['tag'] for stop in direction['stop']]]

        if not found_stops:
            # Tell user that no matching stops were found.
            await self.bot.say(
                "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

        elif len(found_stops) == 1:
            stop_1 = found_stops[0]

        else:
            # Provide user with the matching lines and ask them to choose one.
            embed = discord.Embed(
                title='Choose a stop by number.',
                type='rich',
                colour=discord.Colour(0x37980a))

            for t in zip(range(1, len(found_stops) + 1),
                         [d['title'] for d in found_stops], directions):
                embed.add_field(
                    name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)

            await self.bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

            choice = await self.bot.wait_for_message(
                author=ctx.message.author, timeout=300)

            if not choice:
                # Tell user when bot.wait_for_message times out.
                await self.bot.say("Sorry, I didn't pick up a response.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

            try:
                stop_1 = found_stops[int(choice.content) - 1]

            except IndexError:
                # Tell the user if they provide an invalid index.
                await self.bot.say("That's not a valid choice.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

        await self.bot.say('You selected {}!'.format(stop_1['title']))

        # The bot asks the user for a second stop.
        await self.bot.say("What's your second (destination) stop?")

        stop_choice = await self.bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not stop_choice:
            # Tell user when bot.wait_for_message times out.
            await self.bot.say("Sorry, I didn't pick up a response.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        # Get all routes for the given bus and line from the NextBus API.
        async with aiohttp.ClientSession() as session:
            async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(bus_system['tag'], line['tag'])) as response:
                route_data = await response.json()

        # Separate stop data and directional (in/outbound) data
        stops = route_data['route']['stop']
        direction_data = route_data['route']['direction']

        # Sort out all matching stops.
        found_stops = [
            stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

        # Sort out all directional data for the matching stops.
        directions = [
            direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
                stop['tag'] for stop in direction['stop']]]

        if not found_stops:
            # Tell user that no matching stops were found.
            await self.bot.say(
                "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

        elif len(found_stops) == 1:
            stop_2 = found_stops[0]

        else:
            # Provide user with the matching lines and ask them to choose one.
            embed = discord.Embed(
                title='Choose a stop by number.',
                type='rich',
                colour=discord.Colour(0x37980a))

            for t in zip(range(1, len(found_stops) + 1),
                         [d['title'] for d in found_stops], directions):
                embed.add_field(
                    name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)

            await self.bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

            choice = await self.bot.wait_for_message(
                author=ctx.message.author, timeout=300)

            if not choice:
                # Tell user when bot.wait_for_message times out.
                await self.bot.say("Sorry, I didn't pick up a response.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

            try:
                stop_2 = found_stops[int(choice.content) - 1]

            except IndexError:
                # Tell the user if they provide an invalid index.
                await self.bot.say("That's not a valid choice.")

                # Allow users to call other commands.
                self.in_commands.remove(ctx.message.author.id)

                return

        await self.bot.say('You selected {}!'.format(stop_2['title']))

        # The bot asks for a time to notify the user for the first stop.
        embed = discord.Embed(
            title='When should I notify you for the first (starting) stop?',
            type='rich',
            colour=discord.Colour(0x37980a))

        embed.add_field(name='Time Examples',
                        value='16 30, 16:30, 4:30 PM, 4 30 PM')

        await self.bot.say(embed=embed)

        time_choice = await self.bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not time_choice:
            # Tell user when bot.wait_for_message times out.
            await self.bot.say("Sorry, I didn't pick up a response.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        try:
            time_1 = self.parseUserTime(time_choice.content)

            # Check if the time, when converted to UTC, needs to wrap back
            # around midnight.
            if time_1 - self.time_zones[bus_system['tag']] * 60 > 1440:
                # Wrap back around midnight.
                time_1 = time_1 - \
                    self.time_zones[bus_system['tag']] * 60 - 1440

            else:
                time_1 = time_1 - \
                    self.time_zones[bus_system['tag']] * 60

        except Exception:
            # Tell user that there is an error.
            await self.bot.say("I couldn't understand your time format.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        # The bot asks for a time to notify the user for the second stop.
        embed = discord.Embed(
            title='When should I notify you for the second (destination) stop?',
            type='rich',
            colour=discord.Colour(0x37980a))

        embed.add_field(name='Time Examples',
                        value='16 30, 16:30, 4:30 PM, 4 30 PM')

        await self.bot.say(embed=embed)

        time_choice = await self.bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not time_choice:
            # Tell user when bot.wait_for_message times out.
            await self.bot.say("Sorry, I didn't pick up a response.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        try:
            time_2 = parseUserTime(time_choice.content)

            # Check if the time, when converted to UTC, needs to wrap back
            # around midnight.
            if time_2 - self.time_zones[bus_system['tag']] * 60 > 1440:
                # Wrap back around midnight.
                time_2 = time_2 - \
                    self.time_zones[bus_system['tag']] * 60 - 1440

            else:
                time_2 = time_2 - \
                    self.time_zones[bus_system['tag']] * 60

        except Exception:
            # Tell user that there is an error.
            await self.bot.say("I couldn't understand your time format.")

            # Allow users to call other commands.
            self.in_commands.remove(ctx.message.author.id)

            return

        post = {'user': ctx.message.author.id,
                'system': bus_system,
                'line': line,
                'stop1': stop_1,
                'time1': time_1,
                'stop2': stop_2,
                'time2': time_2}

        # Insert notification into database.
        self.db.posts.insert_one(post)

        # Provide the user with a summary of their notification.
        await self.bot.say(
            "Notification set!", embed=self.notification_embed('Notification Info', post))

        # Allow users to call other commands.
        self.in_commands.remove(ctx.message.author.id)

    async def notifier(self):
        while True:
            # Sleep until the beginning of the next minute.
            await asyncio.sleep(60 - time.time() % 60)

            # Get the current (UTC) time.
            now = datetime.datetime.utcnow()

            # Convert the time into minutes.
            now_in_minutes = round(
                (now -
                 now.replace(
                     hour=0,
                     minute=0,
                     second=0,
                     microsecond=0)).total_seconds() /
                60)

            # Find all notifications set for this minute.
            for notification in self.db.posts.find({'time1': now_in_minutes}):
                try:
                    # Get the time_predictions from the NextBus API.
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&a={}&r={}&s={}'.format(notification['system']['tag'], notification['line']['tag'], notification['stop1']['tag'])) as response:
                            time_predictions = await response.json()

                    # Notify the user with the predicted bus times.
                    embed = self.notification_embed(
                        'Nextbus Notification', notification)

                    embed.add_field(name='Bus Times', value='\n\n'.join(["Bus coming in {} Minutes".format(
                        prediction['minutes']) for prediction in time_predictions['predictions']['direction']['prediction']]), inline=False)

                    await self.bot.send_message(discord.utils.get(
                        self.bot.get_all_members(), id=notification['user']), embed=embed)

                except KeyError:
                    # Tell user that there were no predictions.
                    await self.bot.send_message(discord.utils.get(self.bot.get_all_members(), id=notification['user']),
                                                "I couldn't find any predictions, but I found these messages:\n" +
                                                '\n'.join([m['text'] for m in time_predictions['predictions']['message']]))

            # Find all notifications set for this minute.
            for notification in self.db.posts.find({'time1': now_in_minutes}):
                try:
                    # Get the time_predictions from the NextBus API.
                    async with aiohttp.ClientSession() as session:
                        async with session.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&a={}&r={}&s={}'.format(notification['system']['tag'], notification['line']['tag'], notification['stop2']['tag'])) as response:
                            time_predictions = await response.json()

                    # Notify the user with the predicted bus times.
                    embed = self.notification_embed(
                        'Nextbus Notification', notification)

                    embed.add_field(name='Bus Times', value='\n\n'.join(["Bus coming in {} Minutes".format(
                        prediction['minutes']) for prediction in time_predictions['predictions']['direction']['prediction']]), inline=False)

                    await self.bot.send_message(discord.utils.get(
                        self.bot.get_all_members(), id=notification['user']), embed=embed)

                except KeyError:
                    # Tell user that there were no predictions.
                    await self.bot.send_message(discord.utils.get(self.bot.get_all_members(), id=notification['user']),
                                                "I couldn't find any predictions for {}, but I found these messages:\n" +
                                                '\n'.join([m['text'] for m in time_predictions['predictions']['message']]).format(notification['stop2']['title']))

    def notification_embed(self, title, notification):
        embed = discord.Embed(
            title=title,
            type='rich',
            colour=discord.Colour(0x37980a))
        embed.add_field(
            name='Line', value=notification['line']['title'], inline=False)

        # Convert time from UTC to local time.
        converted_time = notification['time1'] + \
            self.time_zones[notification
                            ['system']['tag']] * 60
        # Wrap around midnight.
        if converted_time < 0:
            converted_time += 1440

        embed.add_field(
            name='First Stop', value='{} at {}'.format(notification['stop1']['title'], str(
                datetime.time(
                    divmod(
                        converted_time, 60)[0], divmod(
                        converted_time, 60)[1]))), inline=False)

        # Convert time from UTC to local time.
        converted_time = notification['time2'] + \
            self.time_zones[notification
                            ['system']['tag']] * 60

        # Wrap around midnight.
        if converted_time < 0:
            converted_time += 1440

        embed.add_field(
            name='Second Stop', value='{} at {}'.format(notification['stop2']['title'], str(
                datetime.time(
                    divmod(
                        converted_time, 60)[0], divmod(
                        converted_time, 60)[1]))), inline=False)

        return embed

    def parseUserTime(self, userinput):
        if ':' in userinput:
            if 'PM' in userinput:
                time = int(userinput.replace('PM', '').split(
                    ':')[0]) * 60 + int(userinput.replace('PM', '').split(':')[1]) + 720
            elif 'AM' in userinput:
                time = int(userinput.replace('AM', '').split(
                    ':')[0]) * 60 + int(userinput.replace('AM', '').split(':')[1])
            else:
                time = int(userinput.split(
                    ':')[0]) * 60 + int(userinput.split(':')[1])
        else:
            if 'PM' in userinput:
                time = int(userinput.replace('PM', '').split()[
                    0]) * 60 + int(userinput.replace('PM', '').split()[1]) + 720
            elif 'AM' in userinput:
                time = int(userinput.replace('AM', '').split()[
                    0]) * 60 + int(userinput.replace('AM', '').split()[1])
            else:
                time = int(userinput.split()[
                    0]) * 60 + int(userinput.split()[1])

        return time


def setup(bot):
    bot.add_cog(NextBus(bot))

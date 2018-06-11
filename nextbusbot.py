from discord.ext import commands
import discord
import datetime
import time
import asyncio
from pymongo import MongoClient
import json
import aiohttp


# Connect to local MongoDB.
client = MongoClient()
db = client.next_bus_db

# Create the bot.
bot = commands.Bot(command_prefix='/',
                   description='Get Bus Notifcations from NextBus API')

# Load the timezones for the different bus systems.
time_zones = json.load(open('timezones.json'))


@bot.command(pass_context=True)
async def start(ctx):
    if not ctx.message.channel.is_private:
        # Tell user to PM bot if called in public channel.
        await bot.say("Sorry, I can't you with so many people watching....\nPM me!")
    else:
        # Introduce the bot and supply current bot commands.
        embed = discord.Embed(title="Commands", type='rich', colour=discord.Colour(
            0x37980a))
        embed.set_author(
            name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")
        embed.add_field(name='/add', value='Make a notification.')

        await bot.say("Let's get going!", embed=embed)


@bot.command(pass_context=True)
async def list(ctx):
    if not ctx.message.channel.is_private:
        # Tell user to PM bot if called in public channel.
        await bot.say("Sorry, I can't you with so many people watching....\nPM me!")
    else:
        # Find all notifications that the user hsa created.
        user_notifications = [t for t in db.posts.find(
            {'user': ctx.message.author.id})]

        if len(user_notifications) > 0:
            # Provide user with matching notifications and ask them to choose one.
            embed = discord.Embed(title="Current Notifcations", type='rich', colour=discord.Colour(
                0x37980a))

            embed.set_author(
                name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")

            for t in zip(range(1, len(user_notifications) + 1), user_notifications):
                # Convert time from UTC to local time.
                converted_time = t[1]['time'] + \
                    time_zones[t[1]['system']['tag']] * 60

                # Wrap around midnight.
                if converted_time < 0:
                    converted_time += 1440

                formatted_time = str(datetime.time(divmod(converted_time, 60)[
                                     0], divmod(converted_time, 60)[1]))

                embed.add_field(name=t[0], value='{} at {}'.format(
                    t[1]['stop']['title'], formatted_time), inline=False)

            await bot.say(content=None, embed=embed)

        else:
            await bot.say('No notifications found.\nUse /add to add a notification.')


@bot.command(pass_context=True)
async def add(ctx):
    if not ctx.message.channel.is_private:
        # Tell user to PM bot if called in public channel.
        await bot.say("Sorry, I can't you with so many people watching....\nPM me!")
        return

    # The bot asks the user for a bus system.
    await bot.say("I've got this!\nWhich bus system do you use?")

    system_choice = await bot.wait_for_message(
        author=ctx.message.author, timeout=300)

    if not system_choice:
        # Tell user when bot.wait_for_message times out.
        await bot.say("I didn't pick up a response.")
        return

    found_busses = []

    async with aiohttp.get('http://webservices.nextbus.com/service/publicJSONFeed?command=agencyList') as response:
        bus_list = await response.json()

    for bus in bus_list['agency']:
        # Check to see if any of the bus system's provided identifiers match with user input.
        for attribute in bus:
            if system_choice.content.lower() in bus[attribute].lower():
                found_busses.append(bus)
                break

    if len(found_busses) == 0:
        # Tell user that no matching bus systems were found.
        await bot.say(
            "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")
        return

    elif len(found_busses) == 1:
        bus_system = found_busses[0]

    else:
        # Provide user with the matching bus systems and ask them to choose one.
        embed = discord.Embed(title='Choose a system by number.', type='rich', colour=discord.Colour(
            0x37980a))
        embed.set_author(
            name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")
        for t in zip(range(1, len(found_busses) + 1), [d['title'] for d in found_busses]):
            embed.add_field(name=t[0], value=t[1], inline=False)

        await bot.say('I found {} matching bus system(s).'.format(len(found_busses)), embed=embed)

        choice = await bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not choice.content:
            # Tell user when bot.wait_for_message times out.
            await bot.say("Sorry, I didn't pick up a response.")

        try:
            bus_system = found_busses[int(choice.content) - 1]

        except Exception:
            # Tell the user if they provide an invalid index.
            await bot.say("I don't think that's a valid choice.")
            return

    await bot.say('You selected {}!'.format(bus_system['title']))

    # The bot asks the user for a route/line.
    await bot.say('Which route/ line do you use?')

    line_choice = await bot.wait_for_message(
        author=ctx.message.author, timeout=300)

    if not line_choice:
        # Tell user when bot.wait_for_message times out.
        await bot.say("Sorry, I didn't pick up a response.")
        return

    # Get all lines for the given bus system from the NextBus API.
    async with aiohttp.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeList&a={}'.format(bus_system['tag'])) as response:
        lines = await response.json()

    # Sort out all the matching lines.
    found_lines = [line for line in lines['route']
                   if line_choice.content.upper() in line['tag']]

    if len(found_lines) == 0:
        # Tell user that no bus systems were found.
        await bot.say(
            "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

    elif len(found_lines) == 1:
        line = found_lines[0]

    else:
        # Provide user with the matching lines and ask them to choose one.
        embed = discord.Embed(title='Choose a line by number.', type='rich', colour=discord.Colour(
            0x37980a))

        embed.set_author(
            name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")

        for t in zip(range(1, len(found_lines) + 1), [d['title'] for d in found_lines]):
            embed.add_field(name=t[0], value=t[1], inline=False)

        await bot.say('I found {} matching lines(s).'.format(len(found_lines)), embed=embed)

        choice = await bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not choice:
            # Tell user when bot.wait_for_message times out.
            await bot.say("Sorry, I didn't pick up a response.")
            return

        try:
            line = found_lines[int(choice.content) - 1]

        except Exception:
            # Tell the user if they provide an invalid index.
            await bot.say("I don't think that's a valid choice.")
            return

    await bot.say('You selected {}!'.format(line['title']))

    # The bot asks the user for a stop.
    await bot.say('Which stop do you use?')

    stop_choice = await bot.wait_for_message(
        author=ctx.message.author, timeout=300)

    if not stop_choice:
        # Tell user when bot.wait_for_message times out.
        await bot.say("Sorry, I didn't pick up a response.")
        return

    # Get all routes for the given bus and line from the NextBus API.
    async with aiohttp.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(bus_system['tag'], line['tag'])) as response:
        route_data = await response.json()

    # Separate stop data and directional (in/outbound) data
    stops = route_data['route']['stop']
    direction_data = route_data['route']['direction']

    # Sort out all matching stops.
    found_stops = [
        stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

    # Sort out all directional data for the matching stops.
    directions = [direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
        stop['tag'] for stop in direction['stop']]]

    if len(found_stops) == 0:
        # Tell user that no matching stops were found.
        await bot.say(
            "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

    elif len(found_stops) == 1:
        stop = found_stops[0]

    else:
        # Provide user with the matching lines and ask them to choose one.
        embed = discord.Embed(title='Choose a stop by number.', type='rich', colour=discord.Colour(
            0x37980a))

        embed.set_author(
            name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")

        for t in zip(range(1, len(found_stops) + 1), [d['title'] for d in found_stops], directions):
            embed.add_field(
                name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)

        await bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

        choice = await bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not choice:
            # Tell user when bot.wait_for_message times out.
            await bot.say("Sorry, I didn't pick up a response.")
            return

        try:
            stop = found_stops[int(choice.content) - 1]

        except Exception:
            # Tell the user if they provide an invalid index.
            await bot.say("That's not a valid choice.")
            return

    await bot.say('You selected {}!'.format(stop['title']))

    # The bot asks for a time to notify the user.
    embed = discord.Embed(title='When should I notify you?', type='rich', colour=discord.Colour(
        0x37980a))

    embed.add_field(name='Time Examples',
                    value='16 30 : 4:30 PM\n6 30 : 6:30 AM')

    await bot.say(content=None, embed=embed)

    time_choice = await bot.wait_for_message(
        author=ctx.message.author, timeout=300)

    if not time_choice:
        # Tell user when bot.wait_for_message times out.
        await bot.say("Sorry, I didn't pick up a response.")
        return

    try:
        # Check if the user provides a time that is over the amount of time in a day.
        if int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) < 1440:
            # Check if the time, when converted to UTC, needs to wrap back around midnight.
            if int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) - time_zones[bus_system['tag']] * 60 > 1440:
                # Wrap back around midnight.
                post = {
                    'user': ctx.message.author.id,
                    'system': bus_system,
                    'stop': stop,
                    'line': line,
                    'time': int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) - time_zones[bus_system['tag']] * 60 - 1440
                }

            else:
                post = {
                    'user': ctx.message.author.id,
                    'system': bus_system,
                    'stop': stop,
                    'line': line,
                    'time': int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) - time_zones[bus_system['tag']] * 60
                }
            # Insert notification into database.
            db.posts.insert_one(post)

            # Provide the user with a summary of their notification.
            embed = discord.Embed(title='Notification Info', type='rich', colour=discord.Colour(
                0x37980a))

            embed.set_author(
                name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")

            embed.add_field(name='Bus System',
                value=bus_system['title'], inline=False)
            embed.add_field(
                name='Line', value=line['title'], inline=False)
            embed.add_field(
                name='Stop', value=stop['title'], inline=False)
            embed.add_field(name='Time', value=str(datetime.time(
                int(time_choice.content.split()[0]), int(time_choice.content.split()[1]))), inline=False)

            await bot.say("Notification set!", embed=embed)

        else:
            # Tell user that they provided a time that exceeds the amount of time in a day.
            await bot.say("I don't think I'll be able to contact you at that time.")
            return
    except Exception:
        # Tell user that there is an error.
        await bot.say("Something went wrong. I'll try to fix it soon.")
        return


async def notifier():
    while True:
        # Sleep until the beginning of the next minute.
        await asyncio.sleep(60 - time.time() % 60)

        # Get the current (UTC) time.
        now = datetime.datetime.utcnow()

        # Convert the time into minutes.
        now_in_minutes = round(
            (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)

        # Find all notifications set for this minute.
        for notification in db.posts.find({'time': now_in_minutes}):
            try:
                # Get the time_predictions from the NextBus API.
                async with aiohttp.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&a={}&r={}&s={}'.format(notification['system']['tag'], notification['line']['tag'], notification['stop']['tag'])) as response:
                    time_predictions = await response.json()

                # Notify the user with the predicted bus times.
                embed = discord.Embed(
                    title='Notification', type='rich', colour=discord.Colour(0x37980a))
                embed.set_author(
                    name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")
                embed.add_field(
                    name='Line', value=notification['line']['title'])
                embed.add_field(
                    name='Stop', value=notification['stop']['title'])
                embed.add_field(
                    name='Bus Times', value='\n\n'.join(
                        ["Bus coming in {} Minutes".format(prediction['minutes']) for prediction in time_predictions['predictions']['direction']['prediction']]), inline=False)

                await bot.send_message(discord.utils.get(
                    bot.get_all_members(), id=notification['user']), 'NextBus notification!', embed=embed)

            except KeyError:
                # Tell user that there is an error.
                await bot.send_message(discord.utils.get(bot.get_all_members(), id=notification['user']),
                                       "Something went wrong and I wasn't able to notify you, I'll make sure to fix it soon!")


@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    # Create the notifier task once bot loads.
    bot.loop.create_task(notifier())

# Start the bot.
bot.run('TOKEN')

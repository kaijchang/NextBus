from discord.ext import commands
import discord
import requests
import datetime
import time
import asyncio
from pymongo import MongoClient

client = MongoClient()
db = client.next_bus_db

bot = commands.Bot(command_prefix='/',
                   description='Get Bus Notifcations from NextBus API')

time_zones = {
    'actransit': -7,
    'jhu-apl': -4,
    'art': -4,
    'atlanta-sc': -4,
    'bigbluebus': -7,
    'brockton': -4,
    'camarillo': -4,
    'ccrta': -4,
    'chapel-hill': -4,
    'charm-city': -4,
    'ccny': -4,
    'oxford-ms': -5,
    'west-hollywood': -7,
    'cyride': -5,
    'dc-circulator': -4,
    'dc-streetcar': -4,
    'da': -4,
    'dta': -4,
    'dumbarton': -7,
    'charles-river': -4,
    'ecu': -4,
    'escalon': -7,
    'fast': -7,
    'fairfax': -4,
    'foothill': -7,
    'ft-worth': -5,
    'glendale': -7,
    'south-coast': -7,
    'indianapolis-air': -4,
    'jfk': -4,
    'jtafla': -4,
    'laguardia': -4,
    'lga': -4,
    'lametro': -7,
    'lametro-rail': -7,
    'mbta': -4,
    'mit': -4,
    'moorpark': -7,
    'ewr': -4,
    'nova-se': -4,
    'omnitrans': -7,
    'pvpta': -7,
    'sria': -4,
    'psu': -4,
    'portland-sc': -7,
    'pgc': -4,
    'reno': -7,
    'radford': -4,
    'roosevelt': -4,
    'rutgers-newark': -4,
    'rutgers': -4,
    'sf-muni': -7,
    'seattle-sc': -7,
    'simi-valley': -7,
    'stl': -4,
    'sct': -7,
    'geg': -7,
    'tahoe': -7,
    'thousand-oaks': -7,
    'ttc': -4,
    'unitrans': -7,
    'ucb': -7,
    'umd': -4,
    'vista': -7,
    'wku': -4,
    'winston-salem': -7,
    'york-pa': -4
}


@bot.command(pass_context=True)
async def start(ctx):
    if not ctx.message.channel.is_private:
        await bot.say("Sorry, I can't you with so many people watching....\nPM me!")
    else:
        await bot.say("Hello!\nI can give you bus time notifications!\nLet's get going!\nUse /add to add a make a norification!")


@bot.command(pass_context=True)
async def add(ctx):
    if not ctx.message.channel.is_private:
        await bot.say("Sorry, I can't you with so many people watching....\nPM me!")
        return

    await bot.say("I've got this!\nWhich bus system do you use?")

    system_choice = await bot.wait_for_message(
        author=ctx.message.author, timeout=300)

    if not system_choice:
        await bot.say("I didn't pick up a response.")
        return
    found_busses = []

    for bus in requests.get('http://webservices.nextbus.com/service/publicJSONFeed?command=agencyList').json()['agency']:
        for attribute in bus:
            if system_choice.content.lower() in bus[attribute].lower():
                found_busses.append(bus)
                break

    if len(found_busses) == 0:
        await bot.say(
            "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")
        return

    else:
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
            await bot.say("Sorry, I didn't pick up a response.")
        try:
            bus_system = found_busses[int(choice.content) - 1]
            await bot.say('You selected {}!'.format(bus_system['title']))

        except Exception:
            await bot.say("I don't think that's a valid choice.")
            return

        await bot.say('Which route/ line do you use?')

        line_choice = await bot.wait_for_message(
            author=ctx.message.author, timeout=300)

        if not line_choice:
            await bot.say("Sorry, I didn't pick up a response.")
            return

        lines = requests.get(
            'http://webservices.nextbus.com/service/publicJSONFeed?command=routeList&a={}'.format(bus_system['tag'])).json()['route']

        found_lines = [
            line for line in lines if line_choice.content.upper() in line['tag']]

        if len(found_lines) == 0:
            await bot.say(
                "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

        else:
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
                await bot.say("Sorry, I didn't pick up a response.")
                return
            try:
                line = found_lines[int(choice.content) - 1]
                await bot.say('You selected {}!'.format(line['title']))
            except Exception:
                await bot.say("I don't think that's a valid choice.")
                return

            await bot.say('Which stop do you use?')

            stop_choice = await bot.wait_for_message(
                author=ctx.message.author, timeout=300)

            if not stop_choice:
                await bot.say("Sorry, I didn't pick up a response.")
                return

            route_data = requests.get('http://webservices.nextbus.com/service/publicJSONFeed?command=routeConfig&a={}&r={}&terse'.format(
                bus_system['tag'], line['tag'])).json()

            stops = route_data['route']['stop']
            direction_data = route_data['route']['direction']

            found_stops = [
                stop for stop in stops if stop_choice.content.lower() in stop['title'].lower()]

            directions = [direction['name'] for direction in direction_data for stop in found_stops if stop['tag'] in [
                stop['tag'] for stop in direction['stop']]]

            if len(found_stops) == 0:
                await bot.say(
                    "Oh, this is weird. I couldn't find anything.\nMaybe try using a different keyword.")

            else:
                embed = discord.Embed(title='Choose a stop by number.', type='rich', colour=discord.Colour(
                    0x37980a))
                embed.set_author(
                    name='nextbusbot', icon_url="https://seattlestreetcar.org/wp-content/uploads/2017/08/NextBus-app-icon.png")
                for t in zip(range(1, len(found_stops) + 1), [d['title'] for d in found_stops], directions):
                    embed.add_field(name=t[0], value='{} - {}'.format(t[1], t[2]), inline=False)
                await bot.say('I found {} matching stop(s).'.format(len(found_stops)), embed=embed)

                choice = await bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not choice:
                    await bot.say('Bot timed out and closed the connection.')
                    return
                try:
                    stop = found_stops[int(choice.content) - 1]
                    await bot.say('You selected {}!'.format(stop['title']))
                except Exception:
                    await bot.say("That's not a valid choice.")
                    return

                await bot.say("When should I give you a notification?\n'16 30' = 4:30 PM")
                time_choice = await bot.wait_for_message(
                    author=ctx.message.author, timeout=300)

                if not time_choice:
                    await bot.say('Bot timed out and closed the connection.')
                    return

                if True:
                    if int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) < 1440:
                        post = {
                            'user': ctx.message.author.id,
                            'system': bus_system,
                            'stop': stop,
                            'line': line,
                            'time': int(time_choice.content.split()[0]) * 60 + int(time_choice.content.split()[1]) - time_zones[bus_system['tag']] * 60
                        }
                        db.posts.insert_one(post)
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
                        await bot.say("I don't think I'll be able to contact you at that time.")
                        return
                else:
                    await bot.say("I didn't get that.")
                    return


async def notifier():
    await asyncio.sleep(60 - time.time() % 60)
    while True:
        now = datetime.datetime.utcnow()
        now_in_minutes = round(
            (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)
        for notification in db.posts.find({'time': now_in_minutes}):
            try:
                time_predictions = requests.get('http://webservices.nextbus.com/service/publicJSONFeed?command=predictions&a={}&r={}&s={}'.format(
                    notification['system']['tag'], notification['line']['tag'], notification['stop']['tag'])).json()['predictions']
                msg = "Next Bus Notification!\n\nLine: {}\n\nStop: {} - {}\n\nBus Times:\n\n".format(notification['line']['title'], notification['stop']['title'], time_predictions['direction']['title']) + '\n'.join(
                    ["{} Minutes".format(prediction['minutes']) for prediction in time_predictions['direction']['prediction']])

                await bot.send_message(discord.utils.get(
                    bot.get_all_members(), id=notification['user']), msg)
            except KeyError:
                await bot.send_message(discord.utils.get(bot.get_all_members(), id=notification['user']),
                                       "Something went wrong and I wasn't able to notify you, I'll make sure to fix it soon!")

        await asyncio.sleep(60 - time.time() % 60)


@bot.event
async def on_ready():
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    bot.loop.create_task(notifier())

bot.run('TOKEN')

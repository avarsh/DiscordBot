import discord
from discord.ext import commands, tasks
import random

from datetime import datetime
from zoneinfo import ZoneInfo

description = '''Bot'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    print(bot.guilds)

    if not check_schedule.is_running():
      check_schedule.start()

def add_repeated_to_db(datetime_object, seconds, message, channel_id):
    with open('db', 'r') as f:
        id = len(f.readlines()) + 1

    start_timestamp = int(datetime_object.timestamp())
    with open('db', 'a') as f:
        data = ' '.join([
            str(start_timestamp),
            str(seconds),
            str(channel_id),
            message
        ])

        f.write(data + '\n')

    next_timestamp = start_timestamp
    if int(datetime.now().timestamp()) > start_timestamp:
        next_timestamp = datetime.fromtimestamp(start_timestamp + seconds)

    return id, next_timestamp

@bot.command()
async def schedule(ctx, *args):
    # '?schedule every 3 days starting 15/08/24 22:30 "message here"
    if args[0] == "every":
        try:
            interval = int(args[1])
        except ValueError:
            await ctx.send("Expected number as 2nd argument, got: " + args[1])
            return
        if interval < 1:
            await ctx.send("Interval should be a positive integer.")
            return
        
        unit = args[2].lower()
        acceptable_units = { 'second' : 1, 'hour' : 3600, 'day' : 24 * 60 * 60, 'minute' : 60, 'week' : 7 * 24 * 60 * 60 }
        if unit not in acceptable_units.keys() and unit[:-1] not in acceptable_units.keys():
            await ctx.send("Time unit should be one of " + ", ".join(acceptable_units.keys()))
        
        seconds = 0
        if unit in acceptable_units.keys():
            seconds = acceptable_units[unit]
        elif unit[:-1] in acceptable_units.keys():
            seconds = acceptable_units[unit[:-1]]
        
        seconds = seconds * interval

        datetime_str = args[4] + " " + args[5]
        datetime_object = datetime.strptime(datetime_str, '%d/%m/%y %H:%M')
        datetime_object = datetime_object.replace(tzinfo=ZoneInfo('Europe/London'))

        message = args[6]

        id, next_reminder = add_repeated_to_db(datetime_object, seconds, message, ctx.channel.id)

        next_reminder = next_reminder.strftime("%d/%m/%y %H:%M")
        print(seconds)

        await ctx.send(f'Created scheduled message with ID {id}. Next reminder will be sent on {next_reminder}')

    elif args[0] == "once":
        pass
    else:
        await ctx.send("Schedule command must be followed by 'every' or 'once'. If you're confused ask Aporva.")

@tasks.loop(seconds=60*5)
async def check_schedule():
    curr_time = int(datetime.now().timestamp())
    TOLERANCE = 60 * 5
    with open('db', 'r') as f:
        lines = f.readlines()
        for task in lines:
            task_details = task.split()
            if curr_time > int(task_details[0]) and (curr_time - int(task_details[0])) % int(task_details[1]) < TOLERANCE:
                await bot.get_channel(int(task_details[2])).send(' '.join(task_details[3:]))

with open('token', 'r') as token_file:
    token = token_file.readlines()[0]

bot.run(token)

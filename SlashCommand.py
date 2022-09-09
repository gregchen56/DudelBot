from typing import Literal, Optional
import discord
from discord import app_commands
from discord.app_commands import Choice
from dotenv import load_dotenv
import os
import traceback
import time
from datetime import datetime as dt
import sqlite3
import requests

DB_PATH = './data/db/DudelBotData.db'
DPS_EMOJI = '⚔️'
DPS_ROLE = 'DPS'
SUPPORT_EMOJI = '🩹'
SUPPORT_ROLE = 'Support'
ROLE_DICT = {
    # Emoji key : [role_name, index]
    DPS_EMOJI : [DPS_ROLE, 0],
    SUPPORT_EMOJI : [SUPPORT_ROLE, 1]
}
DEFAULT_IMAGE_URLS = {
    # Event key : [img_path, filename, attachment://filename]
    'argos' : ['./images/Argos.jpg', 'Argos.jpg', 'attachment://Argos.jpg'],
    'valtan' : ['./images/Valtan.jpg', 'Valtan.jpg', 'attachment://Valtan.jpg'],
    'vykas' : ['./images/Vykas2.jpg', 'Vykas2.jpg', 'attachment://Vykas2.jpg']
}
UTC_OFFSETS = {
    'CDT' : '-0500',
    'CST' : '-0600',
    'EDT' : '-0400',
    'EST' : '-0500',
    'MDT' : '-0600',
    'MST' : '-0700',
    'PDT' : '-0700',
    'PHT' : '+0800',
    'PST' : '-0800',
    'UTC/GMT' : '+0000',
}
EVENT_MANAGER_ROLE = 'Officer'

class MyClient(discord.Client):
    def __init__(self, intents):
        super().__init__(intents=intents, activity=discord.Game(name='/help'))
        self.tree = app_commands.CommandTree(self)
        self.guild_channels = {}

    async def setup_hook(self):
        # self.tree.copy_global_to(guild=MY_GUILD)
        # await self.tree.sync(guild=MY_GUILD)
        # self.tree.copy_global_to(guild=FREE_CANDY)
        # await self.tree.sync(guild=FREE_CANDY)
        await self.tree.sync()

# DudelBot needs the 'bot' scope and the following bot permissions:
#   Read Messages/View Channels
#   Send Messages
#   Manage Messages
#   Embed Links
#   Attach Files
#   Read Message History
#   Add Reactions
#   Use Slash Commands
intents = discord.Intents(
    guild_messages=True,
    guild_reactions=True,
    guilds=True,
    members=True,
    messages=True,
    reactions=True,
)
client = MyClient(intents)

def is_event_channel_set(interaction: discord.Interaction) -> bool:
    return interaction.guild_id in client.guild_channels

@client.event
async def on_ready():
    for row in fetch_guild_channel_ids():
        client.guild_channels.update({row[0]: row[1]})
    print(f'Logged in as {client.user} (ID: {client.user.id})!')
    print('-----------------------------------------------------')

@client.event
async def on_raw_reaction_add(payload):
    # The reaction was done by the bot. Do nothing.
    if payload.member.id == client.user.id:
        return

    # Only respond to the desginated DPS and Support emojis.
    if payload.emoji.name != DPS_EMOJI and payload.emoji.name != SUPPORT_EMOJI:
        return

    # Reaction was a DPS or Support emoji, but was not intended for an event signup.
    if (payload.message_id,) not in fetch_event_ids():
        return

    role = ROLE_DICT[payload.emoji.name][0]
    if role == DPS_ROLE:
        signup_limit = get_event_info(payload.message_id)[5]
    elif role == SUPPORT_ROLE:
        signup_limit = get_event_info(payload.message_id)[6]
    signup_count = len(fetch_event_role_signup_info(payload.message_id, role))

    event_message = await get_event_message(payload.channel_id, payload.message_id)
    if signup_limit is not None:
        if signup_limit - 1 < signup_count:
            await event_message.remove_reaction(payload.emoji.name, payload.member)
            await payload.member.send(f'Unable to add your signup because the host has limited signups for the event to {signup_limit} people.')
            return

        field_name = ' '.join([role, payload.emoji.name, '-', f'({signup_count + 1}/{signup_limit})'])

    else:
        field_name = ' '.join([role, payload.emoji.name, '-', f'({signup_count + 1})'])

    embed = event_message.embeds[0]
    insert_event_signup(
        payload.message_id,
        payload.member.display_name,
        payload.member.id,
        role,
        int(dt.now().timestamp())
    )
    result = fetch_event_role_signup_info(event_message.id, role)
    signups = '\n'.join(map(lambda x: x[1], result))

    embed.set_field_at(
        index=ROLE_DICT[payload.emoji.name][1],
        name=field_name,
        value=signups
    )

    await event_message.edit(embed=embed, attachments=[])
    print(f'User ID {payload.user_id} signed up for event ID {payload.message_id} as {ROLE_DICT[payload.emoji.name][0]}')

@client.event
async def on_raw_reaction_remove(payload):
    # The reaction was done by the bot. Do nothing.
    if payload.user_id == client.user.id:
        return
    # Only respond to the desginated DPS and Support emojis.
    if payload.emoji.name != DPS_EMOJI and payload.emoji.name != SUPPORT_EMOJI:
        return
    # Reaction was a DPS or Support emoji, but was not intended for an event signup.
    if (payload.message_id,) not in fetch_event_ids():
        return

    event_message = await get_event_message(payload.channel_id, payload.message_id)
    embed = event_message.embeds[0]

    role = ROLE_DICT[payload.emoji.name][0]
    delete_role_user_from_signups(event_message.id, payload.user_id, role)
    if role == DPS_ROLE:
        signup_limit = get_event_info(payload.message_id)[5]
    elif role == SUPPORT_ROLE:
        signup_limit = get_event_info(payload.message_id)[6]
    result = fetch_event_role_signup_info(event_message.id, role)
    signup_count = len(result)
    if signup_count == 0:
        signups = '\u200b'
    else:
        signups = '\n'.join(map(lambda x: x[1], result))

    if signup_limit is not None:
        field_name = ' '.join([role, payload.emoji.name, '-', f'({signup_count}/{signup_limit})'])

    else:
        field_name = ' '.join([role, payload.emoji.name, '-', f'({signup_count})'])

    embed.set_field_at(
        index=ROLE_DICT[payload.emoji.name][1],
        name=field_name,
        value=signups
    )

    await event_message.edit(embed=embed, attachments=[])
    print(f'User ID {payload.user_id} no longer signed up for event ID {payload.message_id} as {ROLE_DICT[payload.emoji.name][0]}')

# Custom help command
@client.tree.command()
async def help(interaction: discord.Interaction):
    '''How do I use DudelBot?'''
    await interaction.response.defer()

    # Create the embed
    embed = discord.Embed(
        title='DudelBot Commands',
        description='Available parameters and their descriptions are shown when using a command.\n\u200b',
        color=discord.Color.green()
    )
    file = discord.File('./images/Thonk.png', filename='Thonk.png')
    embed.set_thumbnail(url='attachment://Thonk.png')

    # create_event command
    embed.add_field(
        name='/create_event',
        value=f'''Creates an event with you as the host.
                Requires the [{EVENT_MANAGER_ROLE}] role.''',
        inline=False
    )

    # end_event command
    embed.add_field(
        name='/end_event',
        value=f'''End an event that has concluded.
                Requires the [{EVENT_MANAGER_ROLE}] role.''',
        inline=False
    )

    # cancel_event command
    embed.add_field(
        name='/cancel_event',
        value=f'''Cancel an event that you are hosting.
                This will also notify all users who are currently signed up.
                Requires the [{EVENT_MANAGER_ROLE}] role.''',
        inline=False
    )

    # edit_title command
    embed.add_field(
        name='/edit_title',
        value='Edit the title of an event you are hosting.',
        inline=False
    )

    # edit_description command
    embed.add_field(
        name='/edit_description',
        value='Edit the description of an event you are hosting.',
        inline=False
    )

    # edit_time command
    embed.add_field(
        name='/edit_time',
        value='Edit the time of an event you are hosting.',
        inline=False
    )

    # limit_signups command
    embed.add_field(
        name='/limit_signups',
        value=f'''Limit the available DPS or Support signup spots for an event.
                Will remove the latest signups past the limit if applicable.
                Requires the [{EVENT_MANAGER_ROLE}] role.''',
        inline=False
    )

    # remove_signup command
    embed.add_field(
        name='/remove_signup',
        value='Forcefully remove a user\'s signup from an event.',
        inline=False
    )

    # send_signup_reminder command
    embed.add_field(
        name='/send_signup_reminder',
        value='Ping the current signups for an event with a reminder message.',
        inline=False
    )

    # my_signups command
    embed.add_field(
        name='/my_signups',
        value='Sends you a list of the events you are signed up for.',
        inline=False
    )

    # player_signups command
    embed.add_field(
        name='/player_signups',
        value='''Sends you a list of the events a player is signed up for.
                Defaults to the player who used the command.''',
        inline=False
    )

    # help command
    embed.add_field(
        name='/help',
        value='Shows this custom help message',
        inline=False
    )

    # get_channel_id command
    embed.add_field(
        name='/get_channel_id',
        value='Shows the ID of the channel where the command is used.',
        inline=False
    )

    # set_events_channel command
    embed.add_field(
        name='/set_events_channel',
        value='Sets the channel where event messages will be located. Required for some commands.',
        inline=False
    )

    await interaction.followup.send(file=file, embed=embed)

# Get the channel id where the command was used. Useful for the set_events_channel command.
@client.tree.command()
async def get_channel_id(interaction: discord.Interaction):
    await interaction.response.send_message(f'This channel\'s ID is: {interaction.channel_id}')

# Set the channel in the guild where events will live
@client.tree.command()
@discord.app_commands.checks.has_role(EVENT_MANAGER_ROLE)
async def set_events_channel(interaction: discord.Interaction, channel_id: str):
    await interaction.response.defer()
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT channel_id FROM guild_channel_id WHERE guild_id=?", (interaction.guild_id,)).fetchone()

    channel_id = int(channel_id)
    # Channel ID for the current guild has been set before. Update it instead.
    if result:
        cur.execute("UPDATE guild_channel_id SET channel_id=? WHERE guild_id=?", (channel_id, interaction.guild_id))

    # Channel ID for the current guild has never been set. Add it to the database.
    else:
        cur.execute("INSERT INTO guild_channel_id VALUES (?, ?)", (interaction.guild_id, channel_id))

    con.commit()
    con.close()
    client.guild_channels.update({interaction.guild_id: channel_id})
    await interaction.followup.send('Events channel set')

# set_events_channel command error handler
@set_events_channel.error
async def set_events_channel_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        log_message(f'User ID: {interaction.user.id} tried to set the events channel but does not have the [{EVENT_MANAGER_ROLE}] role')
        await interaction.response.send_message(f'[{EVENT_MANAGER_ROLE}] role required to set the events channel.')

    else:
        log_error()
        raise

# Create an event
@client.tree.command()
@discord.app_commands.checks.has_role(EVENT_MANAGER_ROLE)
@app_commands.describe(
    title='The name of the event.',
    day='The day of the event. Expected format: MM/DD/YY.',
    hour='Defaults to server time. Command has an optional timezone parameter.',
    minute='Defaults to server time. Command has an optional timezone parameter.',
    img_url='The url of the image you want on your event.'
)
@app_commands.choices(timezone=[
    Choice(name='CDT - Central Daylight Time', value='CDT'),
    Choice(name='CST - Central Standard Time', value='CST'),
    Choice(name='EDT - Eastern Daylight Time', value='EDT'),
    Choice(name='EST - Eastern Standard Time', value='EST'),
    Choice(name='MDT - Mountain Daylight Time', value='MDT'),
    Choice(name='MST - Mountain Standard Time', value='MST'),
    Choice(name='PDT - Pacific Daylight Time', value='PDT'),
    Choice(name='PHT - Philippine Time', value='PHT'),
    Choice(name='PST - Pacific Standard Time', value='PST'),
    Choice(name='UTC/GMT - Coordinated Universal Time', value='UTC/GMT'),
])
async def create_event(
    interaction: discord.Interaction,
    title: str,
    day: str,
    hour: Literal['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
    minute: Literal['00', '15', '30', '45'],
    am_pm: Literal['am', 'pm'],
    timezone: Optional[Choice[str]],
    img_url: Optional[str]
    ):
    '''Creates an event with you as the host.'''
    await interaction.response.defer()

    # Titles can only be 256 characters long
    if len(title) > 256:
        await interaction.followup.send('Title can only be up to 256 characters long.')
        return

    # Parse the date and time entered by the user
    if timezone:
        utc_offset = UTC_OFFSETS[timezone.value]
    elif time.localtime().tm_isdst:
        utc_offset = UTC_OFFSETS['PDT']
    else:
        utc_offset = UTC_OFFSETS['PST']
    try:
        e_datetime = dt.strptime(' '.join([day, hour, minute, am_pm, utc_offset]), '%m/%d/%y %I %M %p %z')
    except ValueError:
        await interaction.followup.send('Date input was invalid.')
        return

    # Create the embed
    descr = f'''Host: {interaction.user.display_name}\n
            🕙 <t:{int(e_datetime.timestamp())}>\n\u200b'''
    embed = discord.Embed(
        title = title,
        description = descr,
        color = discord.Color.purple()
    )

    # DPS and Support fields
    embed.add_field(
        name = ' '.join([DPS_ROLE, DPS_EMOJI, '-', '(0)']),
        value = '\u200b'
    )
    embed.add_field(
        name = ' '.join([SUPPORT_ROLE, SUPPORT_EMOJI, '-', '(0)']),
        value = '\u200b'
    )

    # Set event image if one was provided.
    file = None
    if img_url:
        try:
            response = requests.get(img_url)
            with open('./images/temp_img.jpg', 'wb') as f:
                f.write(response.content)
            file = discord.File('./images/temp_img.jpg', filename='temp_img.jpg')
            embed.set_image(url='attachment://temp_img.jpg')

        except requests.exceptions.RequestException:
            await interaction.user.send('I couldn\'t find an image at the url you specified for the event. I\'ll be making the event without it.')

    # If no image provided, try to set a local default image
    else:
        for key in DEFAULT_IMAGE_URLS:
            if key in title.lower():
                file = discord.File(DEFAULT_IMAGE_URLS[key][0], filename=DEFAULT_IMAGE_URLS[key][1])
                embed.set_image(url=DEFAULT_IMAGE_URLS[key][2])
                break

    # Send the event in chat.
    if file:
        sent_message = await interaction.followup.send(file=file, embed=embed)
    else:
        sent_message = await interaction.followup.send(embed=embed)
    
    # Set footer to the event's message ID
    embed.set_footer(text = f'Event ID: {sent_message.id}')

    # Edit the message to display the newly added footer
    await interaction.edit_original_response(embed=embed)

    # Store the event details in the database
    insert_event(
        sent_message.id,
        interaction.user.display_name,
        interaction.user.id,
        int(e_datetime.timestamp()),
        title,
        interaction.guild_id
    )

    # Add signup reactions for DPS and Support
    await sent_message.add_reaction(DPS_EMOJI)
    await sent_message.add_reaction(SUPPORT_EMOJI)

# createevent command error handler
@create_event.error
async def create_event_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        log_message(f'User ID: {interaction.user.id} tried to create an event but does not have the [{EVENT_MANAGER_ROLE}] role')
        await interaction.response.send_message(f'[{EVENT_MANAGER_ROLE}] role required to create events.')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
@discord.app_commands.checks.has_role(EVENT_MANAGER_ROLE)
@app_commands.describe(
    event_id='The ID of the event you want to end. Typically found in the footer of the event message.'
)
async def end_event(interaction: discord.Interaction, event_id: str):
    '''End an event that has concluded.'''
    await interaction.response.defer(ephemeral=True)
    event_info = get_event_info(event_id)

    if not event_info:
        await interaction.followup.send('Event does not exist')
        return

    if interaction.user.id != event_info[2]:
        await interaction.followup.send('You cannot end events where you are not the host')
        log_message(f'User {interaction.user.id} tried to end event {event_id} but is not the event host!')
        return

    player_ids = fetch_event_signup_distinct_player_ids(event_id)
    for id in player_ids:
        delete_user_from_signups(event_id, id[0])

    delete_event_by_id(event_id)
    event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
    await event_message.delete()
    await interaction.followup.send('Event ended.')

# end_event command error handler
@end_event.error
async def end_event_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        log_message(f'User ID: {interaction.user.id} tried to end an event but does not have the [{EVENT_MANAGER_ROLE}] role')
        await interaction.response.send_message(f'[{EVENT_MANAGER_ROLE}] role required to end events.')

    elif isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to end an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise


@client.tree.command()
@app_commands.check(is_event_channel_set)
@discord.app_commands.checks.has_role(EVENT_MANAGER_ROLE)
@app_commands.describe(
    event_id='The ID of the event you want to cancel. Typically found in the footer of the event message.'
)
async def cancel_event(interaction: discord.Interaction, event_id: str):
    '''Cancel an event that you are hosting. This will also notify all users who are currently signed up.'''
    await interaction.response.defer(ephemeral=True)
    event_info = get_event_info(event_id)

    if not event_info:
        await interaction.followup.send('Event does not exist')
        return

    if interaction.user.id != event_info[2]:
        await interaction.followup.send('You cannot cancel events where you are not the host')
        log_message(f'User {interaction.user.id} tried to cancel event {event_id} but is not the event host!')
        return

    player_ids = fetch_event_signup_distinct_player_ids(event_id)
    for id in player_ids:
        user = await client.fetch_user(id[0])
        await user.send(f'{event_info[1]} has cancelled the event {event_info[4]} on <t:{event_info[3]}>')
        delete_user_from_signups(event_id, id[0])

    delete_event_by_id(event_id)
    event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
    await event_message.delete()
    await interaction.followup.send('Event cancelled.')

# cancel_event command error handler
@cancel_event.error
async def delete_event_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        log_message(f'User ID: {interaction.user.id} tried to cancel an event but does not have the [{EVENT_MANAGER_ROLE}] role')
        await interaction.response.send_message(f'[{EVENT_MANAGER_ROLE}] role required to cancel events.')

    elif isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to cancel an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
async def edit_title(interaction: discord.Interaction, event_id: str, title: str):
    await interaction.response.defer(ephemeral=True)
    if is_host(interaction.user.id, event_id):
        if len(title) <= 256:
            event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
            embed = event_message.embeds[0]
            embed.title = title
            set_db_event_title(event_id, title)
            await event_message.edit(attachments=[], embed=embed)
            await interaction.followup.send('Done')
        else:
            await interaction.followup.send('Title can only be up to 256 characters long.')

    else:
        await interaction.followup.send('You cannot edit events where you are not the host.')
        log_message(f'User {interaction.user.id} tried to edit title of event {event_id} but is not the host!')

# edit_title command error handler
@edit_title.error
async def edit_title_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to edit title for an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
async def edit_description(interaction: discord.Interaction, event_id: str, description: str):
    await interaction.response.defer(ephemeral=True)
    if is_host(interaction.user.id, event_id):
        if len(description) <= 4096:
            event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
            embed = event_message.embeds[0]
            cur_desc = embed.description.split('\u200b')[0]
            embed.description = '\u200b'.join([cur_desc, '\n', description, '\n\u200b'])
            await event_message.edit(attachments=[], embed=embed)
            await interaction.followup.send('Done')
        else:
            await interaction.followup.send('Description can only be up to 4096 characters long.')

    else:
        await interaction.followup.send('You cannot edit events where you are not the host.')
        log_message(f'User {interaction.user.id} tried to edit description of event {event_id} but is not the host!')

# edit_description command error handler
@edit_description.error
async def edit_description_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to edit description for an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
@app_commands.choices(timezone=[
    Choice(name='CDT - Central Daylight Time', value='CDT'),
    Choice(name='CST - Central Standard Time', value='CST'),
    Choice(name='EDT - Eastern Daylight Time', value='EDT'),
    Choice(name='EST - Eastern Standard Time', value='EST'),
    Choice(name='MDT - Mountain Daylight Time', value='MDT'),
    Choice(name='MST - Mountain Standard Time', value='MST'),
    Choice(name='PDT - Pacific Daylight Time', value='PDT'),
    Choice(name='PHT - Philippine Time', value='PHT'),
    Choice(name='PST - Pacific Standard Time', value='PST'),
    Choice(name='UTC/GMT - Coordinated Universal Time', value='UTC/GMT'),
])
async def edit_time(
    interaction: discord.Interaction, 
    event_id: str, 
    day: str,
    hour: Literal['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
    minute: Literal['00', '15', '30', '45'],
    am_pm: Literal['am', 'pm'],
    timezone: Optional[Choice[str]],
    ):
    await interaction.response.defer(ephemeral=True)
    if is_host(interaction.user.id, event_id):
        # Parse the date and time entered by the user
        if timezone:
            utc_offset = UTC_OFFSETS[timezone.value]
        elif time.localtime().tm_isdst:
            utc_offset = UTC_OFFSETS['PDT']
        else:
            utc_offset = UTC_OFFSETS['PST']
        try:
            e_datetime = dt.strptime(' '.join([day, hour, minute, am_pm, utc_offset]), '%m/%d/%y %I %M %p %z')
        except ValueError:
            await interaction.followup.send('Date input was invalid.')
            return

        event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
        embed = event_message.embeds[0]
        cur_desc = '\u200b'.join(embed.description.split('\u200b')[1:])
        new_time = f'''Host: {interaction.user.display_name}\n
                    🕙 <t:{int(e_datetime.timestamp())}>\n\u200b'''
        embed.description = ''.join([new_time, cur_desc])
        set_db_event_timestamp(event_id, int(e_datetime.timestamp()))
        await event_message.edit(attachments=[], embed=embed)
        await interaction.followup.send('Done')

    else:
        await interaction.followup.send('You cannot edit events where you are not the host.')
        log_message(f'User {interaction.user.id} tried to edit time of event {event_id} but is not the host!')

# edit_time command error handler
@edit_time.error
async def edit_time_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to edit time for an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
@discord.app_commands.checks.has_role(EVENT_MANAGER_ROLE)
@app_commands.describe(
    event_id='The ID of the event you want to limit signups for.',
    dps_limit='The maximum dps signups you want for the event. Use -1 for no limit.',
    support_limit='The maximum support signups you want for the event. Use -1 for no limit.'
)
async def limit_signups(interaction: discord.Interaction, event_id: str, dps_limit: int, support_limit: int):
    '''Limit the available DPS or Support signup spots for an event.'''
    await interaction.response.defer(ephemeral=True)
    event_id = int(event_id)

    # Return on bad inputs
    if (event_id,) not in fetch_event_ids():
        await interaction.followup.send('That event does not exist.')
        return
    if dps_limit < -1:
        await interaction.followup.send('Bad dps_limit input')
        return
    if support_limit < -1:
        await interaction.followup.send('Bad support_limit input')
        return

    # Only allow the event's host to limit their event's signups
    event_info = get_event_info(event_id)
    if interaction.user.id != event_info[2]:
        await interaction.followup.send('You cannot limit signups when you are not the host!')
        log_message(f'User {interaction.user.id} tried to limit signups for event {event_id} but is not the host!')
        return

    role_limits = {DPS_ROLE : dps_limit, SUPPORT_ROLE : support_limit}
    for index, role in enumerate(role_limits):
        # A DPS/Support limit was given.
        if role_limits[role] >= 0:
            event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
            signup_count = len(fetch_event_role_signup_info(event_id, role))
            
            # Check to see if current role signups are higher than the limit.
            # If so, remove the latest signups past the limit
            if signup_count > role_limits[role]:
                removed_members = delete_latest_n_role_signups(event_id, role, signup_count-role_limits[role])
                for row in removed_members:
                    user = client.get_user(row[1])
                    await event_message.remove_reaction(DPS_EMOJI, user)
                    await user.send(f'You have been removed from `{event_info[4]}` on <t:{event_info[3]}> because the host has added signup limits for your role.')

            # Update the event message to display the new signup limits
            embed = event_message.embeds[0]
            embed.set_field_at(
                index=index,
                name=' '.join([embed.fields[index].name.split(' - ')[0], '-', f'({min(signup_count, role_limits[role])}/{role_limits[role]})']),
                value=embed.fields[index].value
            )
            await event_message.edit(embed=embed, attachments=[])

        # User does not want a DPS/Support limit
        elif role_limits[role] == -1:
            role_limits[role] = None

    # Insert the limits into the event database and alert the user.
    insert_event_limits(event_id, role_limits[DPS_ROLE], role_limits[SUPPORT_ROLE])
    await interaction.followup.send(f'Your event now has a DPS limit of [{role_limits[DPS_ROLE]}] and a support limit of [{role_limits[SUPPORT_ROLE]}]. Any additional signups have been removed.')

# limit_signups command error handler
@limit_signups.error
async def limit_signups_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        log_message(f'User ID: {interaction.user.id} tried to limit signups for an event but does not have the [{EVENT_MANAGER_ROLE}] role')
        await interaction.response.send_message(f'[{EVENT_MANAGER_ROLE}] role required to limit event signups.')
        
    elif isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to limit signups for an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
@app_commands.choices(role=[
    Choice(name=DPS_ROLE, value=DPS_EMOJI),
    Choice(name=SUPPORT_ROLE, value=SUPPORT_EMOJI)
])
async def remove_signup(interaction: discord.Interaction, event_id: str, member: discord.Member, role: Optional[Choice[str]]):
    await interaction.response.defer(ephemeral=True)
    if is_host(interaction.user.id, event_id):
        event_message = await get_event_message(client.guild_channels[interaction.guild_id], event_id)
        
        # Only remove the user's DPS or support signup
        if role:
            delete_role_user_from_signups(event_id, member.id, role.name)
            await event_message.remove_reaction(role.value, member)
            await interaction.followup.send(f'Removed {member.display_name} as a {role.name}')

        # Remove all of the user's signups on the event.
        else:
            delete_user_from_signups(event_id, member.id)
            await event_message.remove_reaction(DPS_EMOJI, member)
            await event_message.remove_reaction(SUPPORT_EMOJI, member)
            await interaction.followup.send(f'Removed {member.display_name}')
        
        await member.send(f'The host has manually removed you from the following event.', embed=event_message.embeds[0].copy())

    # Only allow an event's host to remove signups
    else:
        await interaction.followup.send('You cannot remove signups for events where you are not the host.')
        log_message(f'User {interaction.user.id} tried to remove member {member.id} from event {event_id} but is not the host!')

# remove_signup command error handler
@remove_signup.error
async def remove_signup_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to remove signups for an event but the event channel is not set')
        await interaction.response.send_message('Event channel is not set. Please run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
async def send_signup_reminder(interaction: discord.Interaction, event_id: str):
    await interaction.response.defer()
    event_id = int(event_id)

    player_ids = fetch_event_signup_distinct_player_ids(event_id)
    event_info = get_event_info(event_id)
    mentions = ' '.join([f'<@!{id[0]}>' for id in player_ids])
    message = ' '.join([
        f'{interaction.user.display_name} is reminding',
        mentions,
        f'that you are signed up for `{event_info[4]}` <t:{event_info[3]}:R>'])

    await interaction.delete_original_response()
    await interaction.channel.send(message)

@client.tree.command()
@app_commands.check(is_event_channel_set)
async def my_signups(interaction: discord.Interaction):
    '''Sends you a list of the events you are signed up for.'''
    await interaction.response.defer(ephemeral=True)

    event_ids = fetch_distinct_player_signup_events(interaction.user.id, interaction.guild_id)
    p_msgable = client.get_partial_messageable(client.guild_channels[interaction.guild_id])
    embeds = []

    for event in event_ids:
        event_message = await p_msgable.fetch_message(event[0])
        embeds.append(event_message.embeds[0].copy())

    if len(embeds) != 0:
        await interaction.user.send(embeds=embeds)
        await interaction.followup.send('I sent you a DM with all your event signups!')
    else:
        await interaction.followup.send('You are not signed up to any events.')

# my_signups command error handler
@my_signups.error
async def my_signups_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to get their signups but the event channel is not set')
        await interaction.response.send_message(f'Event channel is not set. Please have an [{EVENT_MANAGER_ROLE}] run /set_events_channel')

    else:
        log_error()
        raise

@client.tree.command()
@app_commands.check(is_event_channel_set)
@app_commands.describe(
    member='The player you want to stalk (raid with)'
)
async def player_signups(interaction: discord.Interaction, member: Optional[discord.Member]):
    '''Sends you a list of the events a player is signed up for.'''
    '''Defaults to the player who used the command.'''
    await interaction.response.defer()

    member = member or interaction.user
    event_ids = fetch_distinct_player_signup_events(member.id, interaction.guild_id)
    p_msgable = client.get_partial_messageable(client.guild_channels[interaction.guild_id])
    embeds = []

    for event in event_ids:
        event_message = await p_msgable.fetch_message(event[0])
        embeds.append(event_message.embeds[0].copy())

    if len(embeds) != 0:
        await interaction.user.send(embeds=embeds)
        await interaction.followup.send(f'I sent you a DM with {member.display_name}\'s event signups!')
    else:
        await interaction.followup.send(f'{member.display_name} is not signed up to any events.')

# player_signups command error handler
@player_signups.error
async def player_signups_error_handler(interaction: discord.Interaction, error:app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        log_message(f'User ID: {interaction.user.id} tried to get a player\'s signups but the event channel is not set')
        await interaction.response.send_message(f'Event channel is not set. Please have an [{EVENT_MANAGER_ROLE}] run /set_events_channel')

    else:
        log_error()
        raise

def get_event_info(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM events WHERE event_id=?", (int(event_id),)).fetchone()
    con.close()

    return result

async def get_event_message(channel_id, message_id):
    return await client.get_partial_messageable(int(channel_id)).fetch_message(int(message_id))

def fetch_event_ids():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT event_id FROM events").fetchall()
    con.close()

    return result

def fetch_event_signup_info(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM signups WHERE event_id=?", (int(event_id))).fetchall()
    con.close()
    
    return result

def fetch_event_role_signup_info(event_id, role):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM signups WHERE event_id=? AND role=?", (int(event_id), role)).fetchall()
    con.close()
    
    return result

def fetch_event_signup_distinct_player_ids(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT DISTINCT player_id FROM signups WHERE event_id=?", (int(event_id),)).fetchall()
    con.close()

    return result

def fetch_distinct_player_signup_events(player_id, guild_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute(
        """SELECT * FROM events 
        NATURAL JOIN signups 
        WHERE signups.player_id=? AND events.guild_id=?
        GROUP BY event_id 
        ORDER BY events.unix_timestamp ASC""",
        (int(player_id), int(guild_id))
    ).fetchall()
    con.close()

    return result

def fetch_guild_channel_ids():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM guild_channel_id").fetchall()
    con.close()

    return result

def set_db_event_title(event_id, title):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE events SET title=? WHERE event_id=?", (title, int(event_id)))
    con.commit()
    con.close()

def set_db_event_timestamp(event_id, timestamp):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE events SET unix_timestamp=? WHERE event_id=?", (timestamp, int(event_id)))
    con.commit()
    con.close()
    
def insert_event(event_id, user_name, user_id, unix_timestamp, title, guild_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, NULL, NULL, ?)", 
        (int(event_id), user_name, user_id, unix_timestamp, title, guild_id)
    )
    con.commit()
    con.close()

def insert_event_limits(event_id, dps_limit, support_limit):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """UPDATE events 
        SET dps_limit=?, support_limit=?
        WHERE event_id=?""", 
        (dps_limit, support_limit, event_id)
    )
    con.commit()
    con.close()

def insert_event_signup(event_id, user_name, user_id, role, timestamp):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        'INSERT INTO signups VALUES(?, ?, ?, ?, ?)',
        (int(event_id), user_name, user_id, role, timestamp)
        )
    con.commit()
    con.close()

def delete_event_by_id(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM events WHERE event_id=?",(int(event_id),))
    con.commit()
    con.close()

def delete_user_from_signups(event_id, user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM signups WHERE event_id=? AND player_id=?",
        (int(event_id), user_id)
        )
    con.commit()
    con.close()

def delete_role_user_from_signups(event_id, user_id, role):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM signups WHERE event_id=? AND player_id=? AND role=?",
        (int(event_id), user_id, role)
        )
    con.commit()
    con.close()

def delete_latest_n_role_signups(event_id, role, n):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute(
        """SELECT player_name, player_id, signup_timestamp 
        FROM signups 
        WHERE event_id=? AND role=?
        ORDER BY signup_timestamp DESC 
        LIMIT ?""",
        (event_id, role, n)
    ).fetchall()
    cur.execute(
        """DELETE FROM signups 
        WHERE event_id=? AND role=? 
        AND player_id IN (
            SELECT player_id 
            FROM signups 
            WHERE event_id=? AND role=?
            ORDER BY signup_timestamp DESC 
            LIMIT ?
            )""",
        (event_id, role, event_id, role, n)
    )
    con.commit()
    con.close()

    return result

def is_host(user_id, event_id):
    event_info = get_event_info(event_id)
    return user_id == event_info[2]

def log_error():
    f = open('./logs/exception_log.log', 'a')
    f.write(dt.now().strftime('%b/%d/%y - %I:%M:%S %p'))
    f.write('\n')
    f.write(traceback.format_exc())
    f.write('\n\n')
    f.close()

def log_message(message):
    f = open('./logs/message_log.log', 'a')
    f.write(dt.now().strftime('%b/%d/%y - %I:%M:%S %p'))
    f.write('\n')
    f.write(str(message))
    f.write('\n\n')
    f.close()

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
client.run(token)

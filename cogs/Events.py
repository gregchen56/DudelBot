from multiprocessing import Event
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from typing import Literal, Optional
from dotenv import load_dotenv
import traceback
import time
import datetime
import sqlite3
import aiohttp
import asyncio
import Exceptions
import DatabaseFunctions as dbfunc

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.dps_emoji = '⚔️'
        self.dps_role = 'DPS'
        self.support_emoji = '🩹'
        self.support_role = 'Support'
        self.role_dict = {
            # Emoji key : [role_name, index]
            self.dps_emoji : [self.dps_role, 0],
            self.support_emoji : [self.support_role, 1]
        }
        self.default_image_urls = {
            # Event key : img_path
            'argos' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1025962949954768916/Argos.jpg', './images/Argos.jpg'],
            'brel' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1030203916635344906/Brelshaza.png','./images/Brelshaza.png'],
            'clown' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1025962950651035728/KakulSaydon.jpg', './images/KakulSaydon.jpg'],
            'kakul' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1025962950651035728/KakulSaydon.jpg', './images/KakulSaydon.jpg'],
            'valtan' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1025962950994960455/Valtan.jpg', './images/Valtan.jpg'],
            'vykas' : ['https://cdn.discordapp.com/attachments/1025962764788830238/1025962951317930054/Vykas2.jpg', './images/Vykas2.jpg']
        }
        self.utc_offets = {
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
        self.lock = asyncio.Lock()

        # Add checks
        self.end_event.add_check(self.is_event_channel_set)
        self.cancel_event.add_check(self.is_event_channel_set)
        self.edit_title.add_check(self.is_event_channel_set)
        self.edit_description.add_check(self.is_event_channel_set)
        self.edit_time.add_check(self.is_event_channel_set)
        self.limit_signups.add_check(self.is_event_channel_set)
        self.remove_signup.add_check(self.is_event_channel_set)
        self.my_signups.add_check(self.is_event_channel_set)
        self.player_signups.add_check(self.is_event_channel_set)
    
    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event, user):
        scheduled_event_ids = dbfunc.fetch_scheduled_event_ids()
        if (event.id,) in scheduled_event_ids:
            event_link = event.description.split('\n')[-1]
            embed = discord.Embed(
                color=discord.Color.purple(),
                title="**Thanks for interesting in a DudelBot event!**",
                description=(
                    "Interest in the Discord scheduled event does not sign you up for the event.\n"
                    f"Please [Click Here]({event_link}) to confirm your registration for {event.name}."
                )
            )
            await user.send(embed=embed)

    # Custom help command
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
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
            value='''Creates an event with you as the host.
                    Requires the [Manage Events] permission.''',
            inline=False
        )

        # end_event command
        embed.add_field(
            name='/end_event',
            value='''End an event that has concluded.
                    Requires the [Manage Events] permission.''',
            inline=False
        )

        # cancel_event command
        embed.add_field(
            name='/cancel_event',
            value='''Cancel an event that you are hosting.
                    This will also notify all users who are currently signed up.
                    Requires the [Manage Events] permission.''',
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
            value='''Limit the available DPS or Support signup spots for an event.
                    Will remove the latest signups past the limit if applicable.
                    Requires the [Manage Events] permission.''',
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
    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    async def get_channel_id(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'This channel\'s ID is: {interaction.channel_id}')

    # Set the channel in the guild where events will live
    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.checks.has_permissions(manage_events=True)
    async def set_events_channel(self, interaction: discord.Interaction, channel_id: str):
        await interaction.response.defer()
        con = sqlite3.connect(self.bot.db_path)
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
        self.bot.guild_channels.update({interaction.guild_id: channel_id})
        await interaction.followup.send('Events channel set')

    # Create an event
    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.checks.has_permissions(manage_events=True)
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
            self,
            interaction: discord.Interaction,
            title: str,
            day: str,
            hour: Literal['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
            minute: Literal['00', '15', '30', '45'],
            am_pm: Literal['am', 'pm'],
            timezone: Optional[Choice[str]],
            image: Optional[discord.Attachment],
            img_url: Optional[str]
            ):
        '''Creates an event with you as the host.'''
        await interaction.response.defer()

        # Titles can only be 256 characters long
        if len(title) > 256:
            await interaction.followup.send('Title can only be up to 256 characters long.')
            return

        # Check to see if user input both an image and an image_url
        if image and img_url:
            await interaction.followup.send('Please specify either an image upload or an image url, not both.')
            return

        # Parse the date and time entered by the user
        if timezone:
            utc_offset = self.utc_offets[timezone.value]
        elif time.localtime().tm_isdst:
            utc_offset = self.utc_offets['PDT']
        else:
            utc_offset = self.utc_offets['PST']
        try:
            e_datetime = datetime.datetime.strptime(' '.join([day, hour, minute, am_pm, utc_offset]), '%m/%d/%y %I %M %p %z')
        except ValueError:
            await interaction.followup.send('Date input was invalid. Expected format MM/DD/YY')
            self.bot.log_error()
            return

        # Create the embed
        descr = f'''Host: <@{interaction.user.id}>\n
                🕙 {discord.utils.format_dt(e_datetime, style='f')}\n\u200b'''
        embed = discord.Embed(
            title = title,
            description = descr,
            color = discord.Color.purple()
        )

        # DPS and Support fields
        embed.add_field(
            name = ' '.join([self.dps_role, self.dps_emoji, '-', '(0)']),
            value = '\u200b'
        )
        embed.add_field(
            name = ' '.join([self.support_role, self.support_emoji, '-', '(0)']),
            value = '\u200b'
        )

        # Check if img_url is a valid link to an image
        img_decided = False

        if image:
            embed.set_image(url=image.url)
            image_bytes = await image.read()
            img_decided = True

        elif img_url:
            try:
                image_formats = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url, timeout=10) as response:
                        if response.headers['content-type'] in image_formats:
                            embed.set_image(url=img_url)
                            content = await response.content.read()
                            image_bytes = bytearray(content)
                            img_decided = True

                        else:
                            await interaction.user.send("The img_link you passed was not a direct link to an image. If you would like to retry, delete the event and create another using a direct image link (typically ending in .png or .jpg)")
                            
            except asyncio.exceptions.TimeoutError:
                await interaction.user.send("Couldn't reach img_url - using default image instead.")

        # If no image provided, search for a default image based on the event title.
        if not img_decided:
            for key in self.default_image_urls:
                if key in title.lower():
                    embed.set_image(url=self.default_image_urls[key][0])
                    with open(self.default_image_urls[key][1], 'rb') as file:
                        image_bytes = bytearray(file.read())
                    img_decided = True
                    break
            
        # If no image was set based on the event title, use the constant default image.
        if not img_decided:
            embed.set_image(url='https://cdn.discordapp.com/attachments/1025962764788830238/1025962950198042704/DudelBot.png')
            with open('./images/DudelBot.png', 'rb') as file:
                image_bytes = bytearray(file.read())

        # Send the event in chat.
        sent_message = await interaction.followup.send(
            embed=embed,
            view=EventView(self)
        )

        # Set footer to the event's message ID
        embed.set_footer(text = f'Event ID: {sent_message.id}')

        # Edit the message to display the footer
        await interaction.edit_original_response(embed=embed)

        description = (
            f"**Host:** <@{interaction.user.id}>"
            f"        🕙 {discord.utils.format_dt(e_datetime, style='R')}"
            "\n\u200b\n"
            f"**Sign up here:**\n{sent_message.jump_url}"
        )

        # Create the scheduled event if the event 
        # start time is in the future
        tdelta = e_datetime - discord.utils.utcnow()
        if tdelta.days >= 0:
            scheduled_event = await interaction.guild.create_scheduled_event(
                name=title,
                description=description,
                start_time=e_datetime,
                end_time=e_datetime + datetime.timedelta(hours=1),
                location=f"<#{self.bot.guild_channels[interaction.guild_id]}>",
                image=image_bytes
            )
        
            # Store the event details in the database
            # with scheduled_event id
            dbfunc.insert_event(
                sent_message.id,
                interaction.user.display_name,
                interaction.user.id,
                int(e_datetime.timestamp()),
                title,
                interaction.guild_id,
                scheduled_event.id
            )
        
        else:
            # Store the event details in the database
            # with no scheduled_event id
            dbfunc.insert_event(
                sent_message.id,
                interaction.user.display_name,
                interaction.user.id,
                int(e_datetime.timestamp()),
                title,
                interaction.guild_id,
                None
            )

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.checks.has_permissions(manage_events=True)
    @app_commands.describe(
        event_id='The ID of the event you want to end. Typically found in the footer of the event message.'
    )
    async def end_event(self, interaction: discord.Interaction, event_id: str):
        '''End an event that has concluded.'''
        await interaction.response.defer(ephemeral=True)
        event_info = dbfunc.get_event_info(event_id)

        if not event_info:
            await interaction.followup.send('Event does not exist')
            return

        if interaction.user.id != event_info[2]:
            await interaction.followup.send('You cannot end events where you are not the host')
            self.log_message(f'User {interaction.user.id} tried to end event {event_id} but is not the event host!')
            return

        player_ids = dbfunc.fetch_event_signup_distinct_player_ids(event_id)
        for id in player_ids:
            dbfunc.delete_user_from_signups(event_id, id[0])

        dbfunc.delete_event_by_id(event_id)
        event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
        await event_message.delete()
        scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
        if scheduled_event:
            await scheduled_event.delete()

        await interaction.followup.send('Event ended.')
    
    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.checks.has_permissions(manage_events=True)
    @app_commands.describe(
        event_id='The ID of the event you want to cancel. Typically found in the footer of the event message.'
    )
    async def cancel_event(self, interaction: discord.Interaction, event_id: str):
        '''Cancel an event that you are hosting. This will also notify all users who are currently signed up.'''
        await interaction.response.defer(ephemeral=True)
        event_info = dbfunc.get_event_info(event_id)

        if not event_info:
            await interaction.followup.send('Event does not exist')
            return

        if interaction.user.id != event_info[2]:
            await interaction.followup.send('You cannot cancel events where you are not the host')
            self.log_message(f'User {interaction.user.id} tried to cancel event {event_id} but is not the event host!')
            return

        player_ids = dbfunc.fetch_event_signup_distinct_player_ids(event_id)
        for id in player_ids:
            user = await self.bot.fetch_user(id[0])
            await user.send(f'{event_info[1]} has cancelled the event {event_info[4]} on <t:{event_info[3]}>')
            dbfunc.delete_user_from_signups(event_id, id[0])

        dbfunc.delete_event_by_id(event_id)
        event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
        await event_message.delete()
        scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
        if scheduled_event:
            await scheduled_event.cancel()

        await interaction.followup.send('Event cancelled.')

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    async def edit_title(self, interaction: discord.Interaction, event_id: str, title: str):
        await interaction.response.defer(ephemeral=True)
        if self.is_host(interaction.user.id, event_id):
            if len(title) <= 256:
                event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
                embed = event_message.embeds[0]
                embed.title = title
                dbfunc.set_db_event_title(event_id, title)
                await event_message.edit(embed=embed)
                event_info = dbfunc.get_event_info(event_id)
                scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
                if scheduled_event:
                    await scheduled_event.edit(
                        name=title,
                        description=scheduled_event.description,
                        start_time=scheduled_event.start_time,
                        end_time=scheduled_event.end_time,
                        location=scheduled_event.location
                    )

                await interaction.followup.send('Done')
            else:
                await interaction.followup.send('Title can only be up to 256 characters long.')

        else:
            await interaction.followup.send('You cannot edit events where you are not the host.')
            self.log_message(f'User {interaction.user.id} tried to edit title of event {event_id} but is not the host!')

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    async def edit_description(self, interaction: discord.Interaction, event_id: str, description: str):
        await interaction.response.defer(ephemeral=True)
        if self.is_host(interaction.user.id, event_id):
            if len(description) <= 4096:
                event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
                embed = event_message.embeds[0]
                cur_desc = embed.description.split('\u200b')[0]
                embed.description = '\u200b'.join([cur_desc, '\n', description, '\n\u200b'])
                await event_message.edit(embed=embed)
                await interaction.followup.send('Done')
            else:
                await interaction.followup.send('Description can only be up to 4096 characters long.')

        else:
            await interaction.followup.send('You cannot edit events where you are not the host.')
            self.log_message(f'User {interaction.user.id} tried to edit description of event {event_id} but is not the host!')

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.describe(
        image="A local image you want to upload as the event's display image.",
        img_url="A direct link to an image that you want to set as the event's dislay image."
    )
    async def edit_image(self, interaction: discord.Interaction, event_id: str, image: Optional[discord.Attachment], img_url: Optional[str]):
        """Define a new image or image url for an event. USE EITHER image OR img_url."""
        await interaction.response.defer(ephemeral=True)

        # Check to see if user input both an image and an image_url
        if image and img_url:
            await interaction.followup.send('Please specify either an image upload or an image url, not both.')
            return

        # Check to see if user used the command without specify either an image or an image_url:
        if not (image or img_url):
            await interaction.followup.send('Please specify either an image upload or an image url.')
            return

        event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)

        if image:
            event_message.embeds[0].set_image(url=image.url)
            image_bytes = await image.read()

        elif img_url:
            try:
                image_formats = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
                async with aiohttp.ClientSession() as session:
                    async with session.get(img_url, timeout=10) as response:
                        if response.headers['content-type'] in image_formats:
                            event_message.embeds[0].set_image(url=img_url)
                            content = await response.content.read()
                            image_bytes = bytearray(content)

                        else:
                            await interaction.user.send((
                                "The img_link you passed was not a direct link to an image. "
                                "If you would like to retry, delete the event and create another "
                                "using a direct image link (typically ending in .png or .jpg)"
                            ))
                            
            except asyncio.exceptions.TimeoutError:
                await interaction.user.send("Couldn't reach img_url.")
                return

        await event_message.edit(embed=event_message.embeds[0])
        event_info = dbfunc.get_event_info(event_id)
        scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
        await scheduled_event.edit(
            name=scheduled_event.name,
            description=scheduled_event.description,
            start_time=scheduled_event.start_time,
            end_time=scheduled_event.end_time,
            image=image_bytes,
            location=scheduled_event.location
        )

        await interaction.followup.send("Done")

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
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
        self,
        interaction: discord.Interaction, 
        event_id: str, 
        day: str,
        hour: Literal['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
        minute: Literal['00', '15', '30', '45'],
        am_pm: Literal['am', 'pm'],
        timezone: Optional[Choice[str]],
        ):
        await interaction.response.defer(ephemeral=True)
        if self.is_host(interaction.user.id, event_id):
            # Parse the date and time entered by the user
            if timezone:
                utc_offset = self.utc_offets[timezone.value]
            elif time.localtime().tm_isdst:
                utc_offset = self.utc_offets['PDT']
            else:
                utc_offset = self.utc_offets['PST']
            try:
                e_datetime = datetime.datetime.strptime(' '.join([day, hour, minute, am_pm, utc_offset]), '%m/%d/%y %I %M %p %z')
            except ValueError:
                await interaction.followup.send('Date input was invalid.')
                return

            event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
            embed = event_message.embeds[0]
            cur_desc = '\u200b'.join(embed.description.split('\u200b')[1:])
            new_time = f'''Host: {interaction.user.display_name}\n
                        🕙 {discord.utils.format_dt(e_datetime, style='f')}\n\u200b'''
            embed.description = ''.join([new_time, cur_desc])
            dbfunc.set_db_event_timestamp(event_id, int(e_datetime.timestamp()))
            await event_message.edit(embed=embed)

            event_info = dbfunc.get_event_info(event_id)
            scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
            tdelta = e_datetime - discord.utils.utcnow()
            if scheduled_event and tdelta.days >= 0:
                description = (
                    f"**Host:** <@{event_info[2]}>"
                    f"        🕙 {discord.utils.format_dt(e_datetime, style='R')}"
                    "\n\u200b\n"
                    f"**Sign up here:**\n{event_message.jump_url}"
                )
                await scheduled_event.edit(
                    name=scheduled_event.name,
                    description=description,
                    start_time=e_datetime,
                    end_time=e_datetime + datetime.timedelta(hours=1),
                    location=scheduled_event.location
                )
            await interaction.followup.send('Done')

        else:
            await interaction.followup.send('You cannot edit events where you are not the host.')
            self.log_message(f'User {interaction.user.id} tried to edit time of event {event_id} but is not the host!')

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    @app_commands.checks.has_permissions(manage_events=True)
    @app_commands.describe(
        event_id='The ID of the event you want to limit signups for.',
        dps_limit='The maximum dps signups you want for the event. Use -1 for no limit.',
        support_limit='The maximum support signups you want for the event. Use -1 for no limit.'
    )
    async def limit_signups(self, interaction: discord.Interaction, event_id: str, dps_limit: int, support_limit: int):
        '''Limit the available DPS or Support signup spots for an event.'''
        await interaction.response.defer(ephemeral=True)
        event_id = int(event_id)

        # Return on bad inputs
        if (event_id,) not in dbfunc.fetch_event_ids():
            return await interaction.followup.send("That event does not exist.")
        if dps_limit < -1:
            return await interaction.followup.send("Bad dps_limit input")
        if support_limit < -1:
            return await interaction.followup.send("Bad support_limit input")

        # Only allow the event's host to limit their event's signups
        event_info = dbfunc.get_event_info(event_id)
        if interaction.user.id != event_info[2]:
            await interaction.followup.send('You cannot limit signups when you are not the host!')
            self.log_message(f'User {interaction.user.id} tried to limit signups for event {event_id} but is not the host!')
            return
        
        role_limits = {self.dps_role : [dps_limit, self.dps_emoji], self.support_role : [support_limit, self.support_emoji]}
        removed_members = []
        for role in role_limits:
            signup_count = len(dbfunc.fetch_event_role_signup_info(event_id, role))

            # User does not want a DPS/Support limit
            if role_limits[role][0] == -1:
                role_limits[role][0] = None

            # User specified a DPS/Support limit
            else:
                # Check to see if current role signups are higher than the limit.
                # Remove excess signups.
                if signup_count > role_limits[role][0]:
                    removed_members.append((dbfunc.delete_latest_n_role_signups(event_id, role, signup_count-role_limits[role][0]), role))

        # removed_members is a list of up to 2 tuples. Each tuple
        # is in the form of ([], str). The list in the first index is a list of tuples.
        # Alert users that they have been removed from the event.
        for tuple in removed_members:
            for item in tuple[0]:
                user = self.bot.get_user(item[1])
                await user.send(f'You have been removed from `{event_info[4]}` on <t:{event_info[3]}> because the host has added signup limits for your role.')

        # Insert the limits into the event database
        dbfunc.insert_event_limits(event_id, role_limits[self.dps_role][0], role_limits[self.support_role][0])
        
        # Update the event message to display the new signup limits
        event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)
        await self.update_event_signups(event_message)

        # Alert the user.
        await interaction.followup.send(f'Your event now has a DPS limit of [{role_limits[self.dps_role][0]}] and a support limit of [{role_limits[self.support_role][0]}]. Any additional signups have been removed.')

    @app_commands.command()
    @app_commands.default_permissions(manage_events=True)
    async def remove_signup(self, interaction: discord.Interaction, event_id: str, member: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if self.is_host(interaction.user.id, event_id):
            event_message = await self.get_event_message(self.bot.guild_channels[interaction.guild_id], event_id)

            # Remove all of the user's signups on the event.
            dbfunc.delete_user_from_signups(event_id, member.id)
            await self.update_event_signups(event_message)
            await interaction.followup.send(f'Removed {member.display_name}')
            
            await member.send(f'The host has manually removed you from the following event.', embed=event_message.embeds[0].copy())

        # Only allow an event's host to remove signups
        else:
            await interaction.followup.send('You cannot remove signups for events where you are not the host.')
            self.log_message(f'User {interaction.user.id} tried to remove member {member.id} from event {event_id} but is not the host!')

    @app_commands.command()
    @app_commands.checks.bot_has_permissions(send_messages=True)
    async def send_signup_reminder(self, interaction: discord.Interaction, event_id: str):
        await interaction.response.defer()
        event_id = int(event_id)

        player_ids = dbfunc.fetch_event_signup_distinct_player_ids(event_id)
        event_info = dbfunc.get_event_info(event_id)
        mentions = ' '.join([f'<@{id[0]}>' for id in player_ids])
        message = ' '.join([
            f'{interaction.user.display_name} is reminding',
            mentions,
            f'that you are signed up for `{event_info[4]}` <t:{event_info[3]}:R>'])

        await interaction.delete_original_response()
        await interaction.channel.send(message)

    @app_commands.command()
    async def my_signups(self, interaction: discord.Interaction):
        '''Sends you a list of the events you are signed up for.'''
        await interaction.response.defer(ephemeral=True)

        event_ids = dbfunc.fetch_distinct_player_signup_events(interaction.user.id, interaction.guild_id)
        p_msgable = self.bot.get_partial_messageable(self.bot.guild_channels[interaction.guild_id])
        embeds = []

        for event in event_ids:
            event_message = await p_msgable.fetch_message(event[0])
            embeds.append(event_message.embeds[0].copy())

        if len(embeds) != 0:
            await interaction.user.send(embeds=embeds)
            await interaction.followup.send('I sent you a DM with all your event signups!')
        else:
            await interaction.followup.send('You are not signed up to any events.')

    @app_commands.command()
    @app_commands.describe(
        member='The player you want to stalk (raid with)'
    )
    async def player_signups(self, interaction: discord.Interaction, member: Optional[discord.Member]):
        '''Sends you a list of the events a player is signed up for.'''
        '''Defaults to the player who used the command.'''
        await interaction.response.defer()

        member = member or interaction.user
        event_ids = dbfunc.fetch_distinct_player_signup_events(member.id, interaction.guild_id)
        p_msgable = self.bot.get_partial_messageable(self.bot.guild_channels[interaction.guild_id])
        embeds = []

        for event in event_ids:
            event_message = await p_msgable.fetch_message(event[0])
            embeds.append(event_message.embeds[0].copy())

        if len(embeds) != 0:
            await interaction.user.send(embeds=embeds)
            await interaction.followup.send(f'I sent you a DM with {member.display_name}\'s event signups!')
        else:
            await interaction.followup.send(f'{member.display_name} is not signed up to any events.')

    async def get_event_message(self, channel_id, message_id):
        return await self.bot.get_partial_messageable(int(channel_id)).fetch_message(int(message_id))

    # Custom check to see if a channel has been designated as the channel for events
    def is_event_channel_set(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id not in self.bot.guild_channels:
            raise Exceptions.EventChannelNotSet
        
        else:
            return True

    # Check to see if user is host of event
    def is_host(self, user_id, event_id):
        event_info = dbfunc.get_event_info(event_id)
        return user_id == event_info[2]

    def log_error(self):
        f = open('./logs/exception_log.log', 'a')
        f.write(datetime.datetime.now().strftime('%b/%d/%y - %I:%M:%S %p'))
        f.write('\n')
        f.write(traceback.format_exc())
        f.write('\n\n')
        f.close()

    def log_message(self, message):
        f = open('./logs/message_log.log', 'a')
        f.write(datetime.datetime.now().strftime('%b/%d/%y - %I:%M:%S %p'))
        f.write('\n')
        f.write(str(message))
        f.write('\n\n')
        f.close()

    async def update_event_signups(self, event_message: discord.Message):
        async with self.lock:
            embed = event_message.embeds[0]

            signups = dbfunc.fetch_event_signup_info(event_message.id)
            dps_ids = [row[2] for row in signups if row[3] == self.dps_role]
            support_ids = [row[2] for row in signups if row[3] == self.support_role]

            # Set DPS field
            signup_limit = dbfunc.get_event_info(event_message.id)[5]
            if signup_limit is not None:
                field_name = " ".join([self.dps_role, self.dps_emoji, "-", f"({len(dps_ids)}/{signup_limit})"])
            else:
                field_name = " ".join([self.dps_role, self.dps_emoji, "-", f"({len(dps_ids)})"])
            if len(dps_ids) == 0:
                signups = '\u200b'
            else:
                signups = '\n'.join(map(lambda x: f'<@{x}>', dps_ids))
            embed.set_field_at(
                index=0,
                name=field_name,
                value=signups
            )

            # Set Support field
            signup_limit = dbfunc.get_event_info(event_message.id)[6]
            if signup_limit is not None:
                field_name = " ".join([self.support_role, self.support_emoji, "-", f"({len(support_ids)}/{signup_limit})"])
            else:
                field_name = " ".join([self.support_role, self.support_emoji, "-", f"({len(support_ids)})"])
            if len(support_ids) == 0:
                signups = '\u200b'
            else:
                signups = '\n'.join(map(lambda x: f'<@{x}>', support_ids))
            embed.set_field_at(
                index=1,
                name=field_name,
                value=signups
            )

            await event_message.edit(embed=embed)

class EventView(discord.ui.View):
    def __init__(self, events: Events):
        self.events = events
        self.lock = asyncio.Lock()
        super().__init__(timeout=None)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⚔️", label="DPS", custom_id="DPS_Btn")
    async def dps_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if dbfunc.is_signed_up_role(interaction.message.id, interaction.user.id, self.events.dps_role):
            await interaction.followup.send(
                f"You are already signed up as a {self.events.dps_role}",
                ephemeral=True
            )

        else:
            await self.add_signup(interaction, self.events.dps_role)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="🩹", label="Support", custom_id="Supp_Btn")
    async def support_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if dbfunc.is_signed_up_role(interaction.message.id, interaction.user.id, self.events.support_role):
            await interaction.followup.send(
                f"You are already signed up as a {self.events.support_role}",
                ephemeral=True
            )

        else:
            await self.add_signup(interaction, self.events.support_role)

    @discord.ui.button(style=discord.ButtonStyle.secondary, label="Withdraw", custom_id="Withdraw_Btn")
    async def withdraw_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        dbfunc.delete_user_from_signups(interaction.message.id, interaction.user.id)
        await self.events.update_event_signups(interaction.message)
        print(f"User ID {interaction.user.id} no longer signed up for event ID {interaction.message.id}")

    @discord.ui.button(style=discord.ButtonStyle.danger, label="End Event", custom_id="End_Btn")
    async def end_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_perms = interaction.channel.permissions_for(interaction.user)
        if user_perms.manage_events == True:
            # Using an ephemeral message instead of sending a public
            # message, then deleting it afterwards prevents a white
            # "unread" message notification from showing up for the
            # text channel
            await interaction.response.send_message(
                content=(
                    f"Are you sure you want to end event: ``{interaction.message.embeds[0].title}``?\n"
                    "Confirmation will timeout in 1 minute to prevent unwanted event deletions"
                ),
                view=EndEventConfirmationView(interaction),
                ephemeral=True
            )
        
        else:
            await interaction.response.send_message(
                "You must have the manage_events permission to end events.",
                ephemeral=True
            )

    async def add_signup(self, interaction: discord.Interaction, role):
        event_message = interaction.message
        event_id = event_message.id
        if role == self.events.dps_role:
            signup_limit = dbfunc.get_event_info(event_id)[5]
            role_emoji = self.events.dps_emoji
        elif role == self.events.support_role:
            signup_limit = dbfunc.get_event_info(event_id)[6]
            role_emoji = self.events.support_emoji

        # TODO confirm if this is correct
        async with self.lock:
            signup_count = len(dbfunc.fetch_event_role_signup_info(event_id, role))
            if signup_limit is not None:
                if signup_limit - 1 < signup_count:
                    return await interaction.user.send(f"Unable to add your signup because the host has limited signups for the event to {signup_limit} people.")

                field_name = " ".join([role, role_emoji, "-", f'({signup_count + 1}/{signup_limit})'])

            else:
                field_name = " ".join([role, role_emoji, "-", f'({signup_count + 1})'])

            embed = event_message.embeds[0]
            dbfunc.insert_event_signup(
                event_id,
                interaction.user.display_name,
                interaction.user.id,
                role,
                int(datetime.datetime.now().timestamp())
            )
            result = dbfunc.fetch_event_role_signup_info(event_id, role)
            signups = "\n".join(map(lambda x: f"<@{x[2]}>", result))

            embed.set_field_at(
                index=self.events.role_dict[role_emoji][1],
                name=field_name,
                value=signups
            )

            await event_message.edit(embed=embed)

        print(f"User ID {interaction.user.id} signed up for event ID {event_id} as {role}")

class EndEventConfirmationView(discord.ui.View):
    def __init__(self, orig_msg):
        self.orig_msg = orig_msg
        super().__init__(timeout=60)

    async def disable_buttons(self):
        # Disable the buttons
        for button in self.children:
            button.disabled = True
        
        await self.orig_msg.edit_original_response(view=self)

    async def on_timeout(self):
        await self.disable_buttons()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        '''End an event that has concluded.'''
        await interaction.response.defer()
        await self.disable_buttons()

        event_id = self.orig_msg.message.id
        event_info = dbfunc.get_event_info(event_id)

        if not event_info:
            return await interaction.followup.send('Event does not exist.')

        player_ids = dbfunc.fetch_event_signup_distinct_player_ids(event_id)
        for id in player_ids:
            dbfunc.delete_user_from_signups(event_id, id[0])

        dbfunc.delete_event_by_id(event_id)
        event_message = await discord.utils.get(interaction.channel.history(), id=event_id)
        await event_message.delete()
        scheduled_event = interaction.guild.get_scheduled_event(event_info[9])
        if scheduled_event:
            await scheduled_event.delete()

        # explicitly stop listening to interaction events. on_timeout will not be called.
        self.stop()
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.disable_buttons()
        # explicitly stop listening to interaction events. on_timeout will not be called.
        self.stop()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))

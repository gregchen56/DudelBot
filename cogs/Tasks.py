import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import datetime

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.events = self.bot.get_cog('Events')
        self.event_done_checker.start()

    def cog_unload(self):
        print('Tasks unloaded')
        self.event_done_checker.cancel()

    @tasks.loop(hours=1.0)
    async def event_done_checker(self):
        'Check to see if an event has been done for over 8 hours'
        if self.events is not None:
            result = self.events.fetch_events()
            now = int(discord.utils.utcnow().timestamp())
            for row in result:
                # Ask the user if they want to end their event if it has been 8 hours
                if row[8] != 'True' and row[8] != 'Pending' and row[3] + 28800 <= now:
                    event_message = await self.events.get_event_message(self.bot.guild_channels[row[7]], row[0])
                    user = self.bot.get_user(row[2])
                    view = EventDoneView(row[0])
                    view.events = self.events
                    view.message = await user.send(
                        f'The following event started <t:{row[3]}:R>. Would you like to end the event?\nIf you do not respond <t:{now + 57600}:R>, the event will be deleted.',
                        embed=event_message.embeds[0],
                        view=view
                    )
                    self.events.set_no_auto_delete(row[0], 'Pending')

    @event_done_checker.before_loop
    async def before_event_done_checker(self):
        # Wait until the bot is ready
        await self.bot.wait_until_ready()

        # Wait until the next hour to start the task.
        # Allows the task to run every hour, on the hour.
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.now()
        next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
        await asyncio.sleep((next_hour - now).seconds)

class EventDoneView(discord.ui.View):
    def __init__(self, event_id):
        self.event_id = event_id
        # Give the user 16 hours to respond
        super().__init__(timeout=57600.0)

    async def disable_buttons(self):
        # Disable the buttons
        for button in self.children:
            button.disabled = True
        
        await self.message.edit(view=self)

    async def end_event(self):
        event_info = self.events.get_event_info(self.event_id)
        player_ids = self.events.fetch_event_signup_distinct_player_ids(self.event_id)
        for id in player_ids:
            self.events.delete_user_from_signups(self.event_id, id[0])

        self.events.delete_event_by_id(self.event_id)
        channel_id = self.events.get_guild_channel_id(event_info[7])
        event_message = await self.events.get_event_message(channel_id[0], self.event_id)
        await event_message.delete()
        self.events.delete_os_event_image(self.event_id)

    async def on_timeout(self):
        await self.end_event()
        await self.disable_buttons()

    @discord.ui.button(style= discord.ButtonStyle.green, label='Yes')
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await self.end_event()
        await self.disable_buttons()
        self.stop() # explicitly stop listening to interaction events. on_timeout will not be called.
        await interaction.followup.send('Event ended.')

    @discord.ui.button(style= discord.ButtonStyle.red, label='No')
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.events.set_no_auto_delete(self.event_id, 'True')
        await self.disable_buttons()
        self.stop() # explicitly stop listening to interaction events. on_timeout will not be called.
        await interaction.response.send_message('Okay. I won\'t delete this event')
        
        event_info = self.events.get_event_info(self.event_id)
        channel_id = self.events.get_guild_channel_id(event_info[7])
        event_message = await self.events.get_event_message(channel_id[0], self.event_id)
        embed = event_message.embeds[0]
        embed.set_footer(text = f'Event ID: {self.event_id} - DO NOT DELETE')
        await event_message.edit(embed=embed, attachments=[])

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tasks(bot))
import discord
from discord.ext import commands
from discord import app_commands
from os import listdir, getenv
from dotenv import load_dotenv
from datetime import datetime as dt
import traceback
import Exceptions
import cogs.Events
import DatabaseFunctions as dbfunc

class MyBot(commands.Bot):
    def __init__(self, intents):
        super().__init__(command_prefix='/', intents=intents, help_command=None)
        self.db_path = './data/db/DudelBotData.db'
        self.guild_channels = {}

    async def setup_hook(self):
        await self.init_cogs()
        self.events = self.get_cog('Events')
        self.add_view(cogs.Events.EventView(self.events))
        await self.tree.sync()

    async def on_ready(self):
        for row in dbfunc.fetch_guild_channel_ids():
            self.guild_channels.update({row[0]: row[1]})
        print(f'Logged in as {self.user} (ID: {self.user.id})!')
        print('-----------------------------------------------------')

    async def init_cogs(self):
        for filename in self.fetch_cog_filenames():
            await self.load_extension(f'cogs.{filename}')

    def fetch_cog_filenames(self):
        return [f[:-3] for f in listdir('./cogs') if f.endswith('.py')]

    def log_error(self):
        f = open('./logs/exception_log.log', 'a')
        f.write(dt.now().strftime('%b/%d/%y - %I:%M:%S %p'))
        f.write('\n')
        f.write(traceback.format_exc())
        f.write('\n\n')
        f.close()

    def log_message(self, message):
        f = open('./logs/message_log.log', 'a')
        f.write(dt.now().strftime('%b/%d/%y - %I:%M:%S %p'))
        f.write('\n')
        f.write(str(message))
        f.write('\n\n')
        f.close()

# DudelBot needs the 'bot' scope and the following bot permissions:
#   Read Messages/View Channels
#   Manage Events
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
    guild_scheduled_events=True,
    guilds=True,
    members=True,
    message_content=True,
    messages=True,
    reactions=True,
)
load_dotenv()
token = getenv('DISCORD_TOKEN')
dev_id = int(getenv('DEV_ID'))
dev_guild = discord.Object(int(getenv('DEV_GUILD')))
bot = MyBot(intents=intents)

def is_dev(interaction: discord.Interaction):
        if interaction.user.id != dev_id:
            raise Exceptions.UserNotDev()
        else:
            return True

# Sync
@bot.tree.command()
@app_commands.check(is_dev)
async def sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await bot.tree.sync()
    await interaction.followup.send('Synced. Commands can take up to an hour to show up. Please be patient if you do not see your commands right away.')

# Guild Sync
@bot.tree.command(name='guildsync')
@app_commands.check(is_dev)
async def guild_sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    bot.tree.copy_global_to(guild=interaction.guild)
    await bot.tree.sync(guild=interaction.guild)
    await interaction.followup.send('Synced.')

# Load Cog
@bot.tree.command(name='loadcog', guild=dev_guild)
@app_commands.check(is_dev)
async def load_cog(interaction: discord.Interaction, cog_name: str):
    await interaction.response.defer(ephemeral=True)
    await bot.load_extension(f'cogs.{cog_name}')
    await interaction.followup.send(f'Loaded cog: {cog_name}')

# Unload cog
@bot.tree.command(name='unloadcog', guild=dev_guild)
@app_commands.check(is_dev)
async def unload_cog(interaction: discord.Interaction, cog_name: str):
    await interaction.response.defer(ephemeral=True)
    await bot.unload_extension(f'cogs.{cog_name}')
    await interaction.followup.send(f'Unloaded cog: {cog_name}')

# Reload cog
@bot.tree.command(name='reloadcog', guild=dev_guild)
@app_commands.check(is_dev)
async def reload_cog(interaction: discord.Interaction, cog_name: str):
    await interaction.response.defer(ephemeral=True)
    await bot.reload_extension(f'cogs.{cog_name}')
    await interaction.followup.send(f'Reloaded cog: {cog_name}')

# Display available extensions
@bot.tree.command(guild=dev_guild)
@app_commands.check(is_dev)
async def extensions(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    cog_filenames = bot.fetch_cog_filenames()
    file_string = '\n'.join(cog_filenames)
    if file_string == '':
        await interaction.followup.send('No available extensions')
    else:
        # >>> followed by a space to create a multi-line block quote
        await interaction.followup.send(f'The following extensions are available:\n>>> {file_string}')

# Display loaded extensions
@bot.tree.command(name='loadedextensions', guild=dev_guild)
@app_commands.check(is_dev)
async def loaded_extensions(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    cog_names = '\n'.join(bot.extensions)
    if cog_names == '':
        await interaction.followup.send('No extensions are loaded')
    else:
        # >>> followed by a space to create a multi-line block quote
        await interaction.followup.send(f'The following extensions are loaded:\n>>> {cog_names}')

# Print a bunch of new lines to clear the terminal
@bot.tree.command(name='clear', guild=dev_guild)
@app_commands.check(is_dev)
async def clear(interaction: discord.Interaction):
    print("\n\n\n\n\n\n\n\n\n\n")
    await interaction.response.send_message("Done", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    # await interaction.response.defer()
    if isinstance(error, Exceptions.UserNotDev):
        await interaction.response.send_message('You are not a dev.')

    elif isinstance(error, app_commands.MissingPermissions):
        missing_perms = '\n'.join(error.missing_permissions)
        bot.log_message(f'User ID: {interaction.user.id} ran the {interaction.command.name} command but is missing these permissions:{error.missing_permissions}')
        await interaction.response.send_message(f'You are missing the following permissions:\n>>> {missing_perms}', ephemeral=True)

    elif isinstance(error, app_commands.BotMissingPermissions):
        missing_perms = '\n'.join(error.missing_permissions)
        bot.log_message(f'User ID: {interaction.user.id} ran the {interaction.command.name} command but DudelBot is missing these permissions:{error.missing_permissions}')
        await interaction.response.send_message(f'DudelBot is missing the following permissions:\n>>> {missing_perms}', ephemeral=True)

    elif isinstance(error, Exceptions.EventChannelNotSet):
        bot.log_message(f'User ID: {interaction.user.id} ran the {interaction.command.name} command but the event channel is not set.')
        await interaction.response.send_message('Event channel is not set. Please have someone with the [Manage Events] permission run the /set_events_channel command', ephemeral=True)

    else:
        await interaction.response.send_message('Something went wrong :(. Doodle would appreciate if you let him know about this.', ephemeral=True)
        bot.log_error()
        # Reraising the error causes this method to run again
        # raise error

bot.run(token)


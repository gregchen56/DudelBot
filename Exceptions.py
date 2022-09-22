import discord

class UserNotDev(discord.app_commands.CheckFailure):
    def __init__(self, *args: object):
        super().__init__(*args)

class EventChannelNotSet(discord.app_commands.CheckFailure):
    def __init__(self, *args: object):
        super().__init__(*args)
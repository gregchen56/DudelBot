# DudelBot
A Discord bot for hosting events in the massively multiplayer online role-playing game (MMORPG),
[Lost Ark](https://www.playlostark.com/en-us).

## Overview
DudelBot aims to allow for the easy creation and management of events in regards to Lost Ark. Event hosters
can create events with a single command and can modify most parameters of any created events. Support for 
default raids in the game are implemented and intuitive UI components are included for both host and attendee
usability.

This project uses the latest development branch of [discord.py](https://github.com/Rapptz/discord.py/tree/v2.0.0)
as its Discord API wrapper and is written in Python.

## Setup
### Prerequisites
1. A Discord [account](https://discord.com/register)
2. A Discord [server](https://support.discord.com/hc/en-us/articles/204849977-How-do-I-create-a-server-) where your Discord account has the "Manage Server" permission

### Steps
1. Click this link to start inviting DudelBot to your Discord server: [Invite DudelBot](https://discord.com/api/oauth2/authorize?client_id=1008997047426363472&permissions=10737544192&scope=bot)
2. In the "ADD TO SERVER" dropdown, select the server you would like to invite DudelBot to, then click "Continue"
3. Ensure all permissions are checked, then click "Authorize"
4. Choose a text channel in your server where you want DudelBot to create and check for events. Run the /set_events_channel command in the chosen text channel.
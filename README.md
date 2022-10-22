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

## Table of Contents
* [Features](#features)
* [Setup](#setup)
    * [Prerequisites](#prerequisites)
    * [Steps](#steps)
* [How to Use DudelBot](#how-to-use-dudelbot)

## Features
* Event creation, deletion, and cancellation
* UI buttons for attendee sign up and withdraws
* Custom image support through image link or file upload
* Default image support for the following in-game raids: Argos, Brelshaza, Kakul-Saydon, Valtan, and Vykas
* Modification of event title, description, date, time, and image
* Event attendee signup limits
* Automatic deletion of expired events
* Attendee signup removals
* Remind attendees about an event by mentioning/pinging event attendees
* Lists events that a user is sign up for
* Creates Discord scheduled events for increased visibility towards DudelBot events
* Custom help command
* Permission checks for event creation and modification commands

## Setup
### Prerequisites
1. A Discord [account](https://discord.com/register)
2. A Discord [server](https://support.discord.com/hc/en-us/articles/204849977-How-do-I-create-a-server-) where your Discord account has the "Manage Server" permission

### Steps
1. Click this link to start inviting DudelBot to your Discord server: [Invite DudelBot](https://discord.com/api/oauth2/authorize?client_id=1008997047426363472&permissions=10737544192&scope=bot)
2. In the "ADD TO SERVER" dropdown, select the server you would like to invite DudelBot to, then click "Continue"
3. Ensure all permissions are checked, then click "Authorize"
4. Choose a text channel in your server where you want DudelBot to create and check for events. Run the /set_events_channel command in the chosen text channel.

## How to Use DudelBot
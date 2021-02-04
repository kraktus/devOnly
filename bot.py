#!/usr/local/bin/python3
#coding: utf-8

# Author: Kraktus

# Licence: GNU AGPLv3

"""
Assign a dev role to members joining the server with invite that redirect to a dev channel
"""

import asyncio
import discord
import logging
import logging.handlers
import os
import sys

from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

#############
# Constants #
#############

load_dotenv()
bot_dir = Path(__file__).parent.absolute()

if __debug__:
    DEV_CHANNEL = int(os.getenv("DEV_CHANNEL_DEBUG"))
    DEV_ROLE = int(os.getenv("DEV_ROLE_DEBUG"))
    TOKEN = os.getenv("TOKEN_DEBUG")
    LOG_NAME = bot_dir / "discord_debug.log"
else:
    DEV_CHANNEL = int(os.getenv("DEV_CHANNEL"))
    DEV_ROLE = int(os.getenv("DEV_ROLE"))
    TOKEN = os.getenv("TOKEN")
    LOG_NAME = bot_dir / "discord.log"

########
# Logs #
########

log = logging.getLogger("DevOnly")
log.setLevel(logging.DEBUG)

logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)

format_string = "%(asctime)s | %(levelname)-8s | %(message)s"

# 5242880 bytes = 5 Mo
handler = logging.handlers.RotatingFileHandler(LOG_NAME, maxBytes=5242880, backupCount=1, encoding="utf8")
handler.setFormatter(logging.Formatter(format_string))
handler.setLevel(logging.DEBUG)
log.addHandler(handler)

handler_2 = logging.StreamHandler(sys.stdout)
handler_2.setFormatter(logging.Formatter(format_string))
if __debug__:
    handler_2.setLevel(logging.DEBUG)
else:
    handler_2.setLevel(logging.INFO)
log.addHandler(handler_2)

###########
# Classes #
###########

@dataclass
class InvitesInfo:
    """Number of people invited in the dev_channel, and in total"""
    dev_channel: int
    total: int

class DevOnlyBot(discord.Client):

    async def on_ready(self) -> None:
        log.debug(f"Logged in as {self.user.name}, {self.user.id}, debug mode : {__debug__}")
        self.guild = self.get_channel(DEV_CHANNEL).guild
        self.current_invites = await self.get_invites()

    async def on_member_join(self, member: discord.Member) -> None:
        log.debug(f"{member} joined")
        if await self.is_invited_in_dev_channel():
            log.debug(f"role dev fetched: {self.guild.get_role(DEV_ROLE)}")
            await member.add_roles(self.guild.get_role(DEV_ROLE))
            log.info(f"Dev role added to {member}")
        self.current_invites = await self.get_invites() # update invites

    async def get_invites(self) -> InvitesInfo:
        invites = await self.guild.invites()
        info = InvitesInfo(
            dev_channel=sum((i.uses for i in invites if i.channel.id == DEV_CHANNEL)),
            total=sum((i.uses for i in invites)),
            )
        log.debug(f"invites: {info}")
        return info

    async def is_invited_in_dev_channel(self) -> bool:
        new_invites = await self.get_invites()
        log.debug(f"{new_invites.total - self.current_invites.total} members joined while fetching invites,"
            f" {new_invites.dev_channel - self.current_invites.dev_channel} looking for dev channel")
        return new_invites.dev_channel - self.current_invites.dev_channel == new_invites.total - self.current_invites.total

########
# Main #
########

if __name__ == "__main__":
    print('#'*80)
    bot = DevOnlyBot(intents=discord.Intents.all())
    bot.run(TOKEN)
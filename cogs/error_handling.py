import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import asyncio
import sys

from cooldowns import CallableOnCooldown

import datetime
import traceback
from difflib import get_close_matches


class ErrorHandling(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		bot.event(self.on_application_command_error)

	# @commands.Cog.listener()
	async def on_application_command_error(self, interaction:Interaction, error):
		embed = nextcord.Embed(title=f"{self.bot.user.name} | ERROR", color=0xFF0000)
		error = getattr(error, 'original', error)

		if "missing permissions" in str(error).lower() or "send message" in str(error).lower() or "missing access" in str(error).lower():
			return

		elif isinstance(error, commands.CommandOnCooldown) or isinstance(error, CallableOnCooldown):
			a = datetime.timedelta(seconds=error.retry_after)
			cooldown = str(a).split(".")[0]
			embed.description = f"{str(interaction.application_command.qualified_name).title()} is on cooldown. Please retry again in {cooldown}"

		elif isinstance(error, commands.CheckFailure):
			try:
				await interaction.send(f"{error}")
			except Exception:
				pass
			return

		elif isinstance(error, commands.BadArgument):
			embed.description = f"{error}"

		else:
			err = str(error)
			err = err.split(':', 2)[-1]
			
			if err == "forbiddenError":
				await interaction.send("Your Discord settings does not allow me to DM you. Please change them and try again.")
				return

			if err == "timeoutError":
				await interaction.send(f"Did not respond in time; timeout.")
				return

			exc = ''.join(traceback.format_exception(type(error), error, error.__traceback__, chain=False))
			exc = exc.split("kwargs)", 1)[1]

			if "MySQL server" in exc:
				embed.description = "We're having difficulties connecting to the database... Apologies for the inconvenience... Please try again later!"
			
			ch = self.bot.get_channel(790282020009148446)
			if len(exc) > 1999:
				await ch.send(f"{exc[:1999]}")
				if len(exc) > 3998:
					await ch.send(f"{exc[1999:3998]}")
					if len(exc) > 5997:
						await ch.send(f"{exc[3998:5997]}")
						await ch.send(f"{exc[5997:]}")
					else:
						await ch.send(f"{exc[3998:]}")
				else:
					await ch.send(f"{exc[1999:]}")
			else:
				await ch.send(f"{exc}")

			try:
				await ch.send(f"Further info\n{interaction.application_command.qualified_name} ")
			except Exception as e:
				await ch.send(f"error with further infooooo: {e}")
			


			embed.set_thumbnail(url=interaction.user.avatar)
			embed.set_footer(text=interaction.user)


		try:
			await interaction.send(embed=embed)
			return 
		except Exception as e:
			pass
			
			
		# if interaction.application_command is not None and not isinstance(error, commands.CommandOnCooldown) and not isinstance(error, CallableOnCooldown):
		# 	interaction.application_command.reset_cooldown(interaction)

def setup(bot):
	bot.add_cog(ErrorHandling(bot))

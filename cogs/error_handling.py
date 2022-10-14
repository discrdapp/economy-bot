import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import asyncio
import sys

import datetime
import traceback
from difflib import get_close_matches


class ErrorHandling(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_command_error(self, interaction:Interaction, error):
		embed = nextcord.Embed(title=f"{self.bot.user.name} | ERROR", color=0xFF0000)
		error = getattr(error, 'original', error)

		if "missing permissions" in str(error).lower() or "send message" in str(error).lower():
			return

		elif isinstance(error, commands.CommandNotFound):
			if "Discord" in interaction.guild.name or "Discords.com" in interaction.guild.name:
				return
			lst = [	"background", "bal", "balance", "bank", "blackjack", "bg",
					"coinflip", "claim", "colorguesser", "credits", "crash", "crate", "earn", "free", "freemoney", 
					"level", "monthly", "position", "profile", "rewards", "roulette", "rps", 
					"shop", "slot", "slots", "stats", "top", "vote", "weekly"]
		#	embed.description = "Command not found!"
			cmd = interaction.message.content.split()[0][1:]
			try:
				closest = get_close_matches(cmd.lower(), lst)[0]
			except IndexError:
				embed.description = f"`{cmd.lower()}` is not a known command."
			else:
				embed.description = f"`{cmd.lower()}` is not a command, did you mean `{closest}`?"

		elif isinstance(error, commands.MissingRequiredArgument):
			if interaction.command is None:
				return
			try:	
				await interaction.invoke(self.bot.get_command(f'help {interaction.command.name}'))
				interaction.command.reset_cooldown(interaction)
				return
			except:
				err = str(error.param)
				err = err.replace("_", " ")
				err = str(err.split(":")[0])

				firstChar = err[0]
				if firstChar.lower() in "aeiou" and err != "user":
					a_an = "an"
				else:
					a_an = "a"

				if err == 'amntbet':
					err = 'amount to bet'
				elif err == 'sideBet':
					err = 'side to vote for (heads or tails)'
				embed.description = f"Please specify {a_an} {err} for this command to work."

		elif isinstance(error, commands.TooManyArguments):
			embed.description = "You have tried using this command with too many arguments."

		elif isinstance(error, commands.CheckFailure):
			try:
				await interaction.response.send_message(f"{error}")
			except Exception:
				pass
			return

		elif isinstance(error, commands.CommandOnCooldown):
			a = datetime.timedelta(seconds=error.retry_after)
			cooldown = str(a).split(".")[0]
			embed.description = f"{str(interaction.command).title()} is on cooldown. Please retry again in {cooldown}"

		elif isinstance(error, commands.BadArgument):
			embed.description = f"{error}"

		else:
			err = str(error)
			err = err.split(':', 2)[-1]
			
			if err == "forbiddenError":
				await interaction.response.send_message("Your Discord settings does not allow me to DM you. Please change them and try again.")
				return

			if err == "timeoutError":
				await interaction.response.send_message("Did not respond in time; timeout.")
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
			await ch.send(f"Error.\nCommand message: {interaction.message.content}\nUser: {interaction.user.id}")

			# await ch.send(embed=e)
			# await interaction.response.send_message(f"{error}  {interaction.command.qualified_name}")

		embed.set_thumbnail(url=interaction.user.avatar)
		embed.set_footer(text=interaction.user)

		try:
			await interaction.response.send_message(embed=embed)
		except Exception as e:
			pass
			
			
		if interaction.command is not None and not isinstance(error, commands.CommandOnCooldown):
			interaction.command.reset_cooldown(interaction)

def setup(bot):
	bot.add_cog(ErrorHandling(bot))

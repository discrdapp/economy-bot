import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import random

class CG(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"


	@nextcord.slash_command(description="Play Color Guesser!")
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, use_external_emojis=True)
	async def colorguesser(self, interaction:Interaction, amntbet: int):

		await interaction.send("This command is disabled.")
		return
		
		users = list()
		usersToRemove = list()
		userBets = dict()
		colorList = ["green", "red", "blue", "yellow"]

		await interaction.send(f"This is meant to be a multiplayer game.\nFor all those who want to join in and bet {amntbet} coins, type JOIN\n{interaction.user.mention}, type START when everyone has joined in.")

		def is_me(m):
			if m.channel.id != interaction.channel.id or (m.content.lower() != "join" and m.content.lower() != "start"):
				return False
			if m.author not in users:
				users.append(m.author)
			return m.channel.id == interaction.channel.id and m.content.lower() == "start" and m.author.id == interaction.user.id

		try:
			await self.bot.wait_for('message', check=is_me, timeout=45)
		except:
			await interaction.send("Timeout error, continuing...")

		# take out credits and create list of users who don't have enough credits (or have not typed .start)
		msg = ""
		for user in users:
			if not await self.bot.get_cog("Economy").accCheck(user):
				await self.bot.get_cog("Economy").start(interaction, user)
			if not await self.bot.get_cog("Economy").subtractBet(user, amntbet):
				usersToRemove.append(user)
				msg += f"{user.mention}\n"
		
		# remove all users in user list that is in usersToRemove list
		if usersToRemove:
			for user in usersToRemove:
				users.remove(user)
			msg += f"You do not have {amntbet} or more credits. You have been removed from this game."

			await interaction.send(msg)

		await interaction.send("I will now collect the color you bet for. Please wait your turn before responding to me.")

		colors = ""
		for x in colorList:
			if colorList[-1] != x:
				colors += f"{x}, "
			else:
				colors += f"{x}"

		usersToRemove.clear()

		# get all of users bets
		errors = ""
		for user in users:
			def is_me_color(m):
				return m.channel.id == interaction.channel.id and m.content in colorList and m.author.id == user.id

			msg = await interaction.send(f"{user.mention}, pick a color from the list:\n{colors}")
			try:
				colorPicked = await self.bot.wait_for('message', check=is_me_color, timeout=45)
				userBets[user] = colorPicked
				await colorPicked.delete()
			except:
				await msg.edit(message="Timeout error... user refunded and removed from game...")
				await self.bot.get_cog("Economy").addWinnings(user.id, amntbet)
				usersToRemove.append(user)

		color = random.choice(colorList)
		winners = []

		for user in userBets.keys():
			if userBets[user].content == color:
				winners.append(user)

		timesAmnt = len(colorList)
		congrats = ""
		for winner in winners:
			await self.bot.get_cog("Economy").addWinnings(winner.id, amntbet * timesAmnt)
			if len(winners) == 1: # if only one person
				congrats = winner.mention
			else: # if more than one person
				if winners[-1] != winner: # if not last person in list
					congrats += f"{winner.mention}, "
				else: # if last person in list
					congrats += f"and {winner.mention}"

		msg = f"The color was {color}\n"
		if winners:
			msg += f"Congratulations to {congrats}, since there are {timesAmnt} colors, you win {timesAmnt}x ({timesAmnt * amntbet}{self.coin}) your bet!"
		else:
			msg += "Unfortunately, no one picked that color. Try again next time!"

		await interaction.send(f"{msg}")




def setup(bot):
	bot.add_cog(CG(bot))
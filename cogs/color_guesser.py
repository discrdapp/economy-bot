import discord
from discord.ext import commands

import asyncio
import random

class CG(commands.Cog):
	def __init__(self, bot):
		self.bot = bot


	@commands.command(description="Play Color Guesser!", aliases=['cg', 'colorguess', 'guesscolor', 'guessercolor'], pass_context=True)
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, use_external_emojis=True)
	async def colorguesser(self, ctx, amntBet: int):
		users = list()
		usersToRemove = list()
		userBets = dict()
		colorList = ["green", "red", "blue", "yellow"]

		await ctx.send(f"This is meant to be a multiplayer game.\nFor all those who want to join in and bet {amntBet} coins, type JOIN\n{ctx.author.mention}, type START when everyone has joined in.")

		def is_me(m):
			if m.channel.id != ctx.channel.id or (m.content != "JOIN" and m.content != "START"):
				return False
			if m.author not in users:
				users.append(m.author)
			return m.channel.id == ctx.channel.id and m.content == "START" and m.author.id == ctx.author.id

		try:
			await self.bot.wait_for('message', check=is_me, timeout=45)
		except:
			await ctx.send("Timeout error, continuing...")

		# take out credits and create list of users who don't have enough credits (or have not typed .start)
		msg = ""
		for user in users:
			if not await self.bot.get_cog("Economy").subtractBet(user, amntBet):
				usersToRemove.append(user)
				msg += f"{user.mention}\n"
		
		# remove all users in user list that is in usersToRemove list
		if usersToRemove:
			for user in usersToRemove:
				users.remove(user)
			msg += f"You have not typed .start OR you do not have {amntBet} or more credits. You have been removed from this game."

			await ctx.send(msg)

		await ctx.send("I will now collect the color you bet for. Please wait your turn before responding to me.")

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
				return m.channel.id == ctx.channel.id and m.content in colorList and m.author.id == user.id

			msg = await ctx.send(f"{user.mention}, pick a color from the list:\n{colors}")
			try:
				colorPicked = await self.bot.wait_for('message', check=is_me_color, timeout=45)
				userBets[user] = colorPicked
				await colorPicked.delete()
			except:
				await msg.edit(message="Timeout error... user refunded and removed from game...")
				await self.bot.get_cog("Economy").addWinnings(user.id, amntBet)
				usersToRemove.append(user)

		color = random.choice(colorList)
		winners = []

		for user in userBets.keys():
			if userBets[user].content == color:
				winners.append(user)

		timesAmnt = len(colorList)
		congrats = ""
		for winner in winners:
			await self.bot.get_cog("Economy").addWinnings(winner.id, amntBet * timesAmnt)
			if winners[-1] != winner:
				congrats += f"{winner.mention}, "
			else:
				congrats += f"and {winner.mention}"

		msg = f"The color was {color}\n"
		if winners:
			msg += f"Congratulations to {congrats}, since there are {timesAmnt} colors, you win {timesAmnt}x ({timesAmnt * amntBet}) your bet!"
		else:
			msg += "Unfortunately, no one picked that color. Try again next time!"

		await ctx.send(f"{msg}")




def setup(bot):
	bot.add_cog(CG(bot))
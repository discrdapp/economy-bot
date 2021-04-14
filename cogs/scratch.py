import discord
from discord.ext import commands
import asyncio

from random import randint
from math import ceil

class Scratch(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"


	@commands.command(description="Play BlackJack!", aliases=['scratchoff', 'lottery'], pass_context=True)
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@commands.cooldown(1, 5, commands.BucketType.user)	
	async def scratch(self, ctx, amntBet: int):
		winningNumber = randint(9,91)
		n = []
		for _ in range(0, 9):
			n.append(randint(winningNumber-2, winningNumber+2))
		spots = {"W1": winningNumber, "A1": n[0], "A2": n[1], "A3": n[2], "B1": n[3], "B2": n[4], "B3": n[5], "C1": n[6], "C2": n[7], "C3": n[8]}
		
		msg = ''
		msg += "Winning number: W1\n"
		msg += "A1\tA2\tA3\n"
		msg += "B1\tB2\tB3\n"
		msg += "C1\tC2\tC3\n"

		msgSent = await ctx.send(msg)

		count = 0

		while count < 10:
			def is_me(m):
				if m.author.id == ctx.author.id and m.content.upper() in spots.keys():
					return True
			try:
				scratchOff = await self.bot.wait_for('message', check=is_me, timeout=45)
			except asyncio.TimeoutError:
				raise Exception("timeoutError")

			count += 1
			content = scratchOff.content.upper()

			msg = msg.replace(content, str(spots[content]))
			await msgSent.edit(content=msg)

			del spots[content]

		profit = 0
		for num in n:
			if winningNumber == num:
				profit += amntBet

		await ctx.send(f"You won {profit}{self.coin}")


def setup(bot):
	bot.add_cog(Scratch(bot))
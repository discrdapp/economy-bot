import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
import asyncio

from random import randint

class Scratch(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"


	@nextcord.slash_command(description="Play Scratch!", guild_ids=[585226670361804827])
	@commands.bot_has_guild_permissions(send_messages=True, manage_messages=True, embed_links=True, use_external_emojis=True, attach_files=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)
	async def scratch(self, interaction:Interaction, amntbet, skip:str=""):
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")

		winningNumber = randint(9,91)
		n = []
		for _ in range(0, 9):
			n.append(randint(winningNumber-5, winningNumber+5))
		spots = {"W1": winningNumber, "A1": n[0], "A2": n[1], "A3": n[2], "B1": n[3], "B2": n[4], "B3": n[5], "C1": n[6], "C2": n[7], "C3": n[8]}
		
		if skip == "":
			msg = ''
			msg += "Winning number: W1\n"
			msg += "A1\tA2\tA3\n"
			msg += "B1\tB2\tB3\n"
			msg += "C1\tC2\tC3\n"

			msgSent = await interaction.send(msg)

			count = 0

			while count < 10:
				def is_me(m):
					if m.author.id == interaction.user.id and m.content.upper() in spots.keys():
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

		if skip == "skip":
			msg = ''
			msg += f"Winning number: {winningNumber}\n"
			msg += f"{n[0]}\t{n[1]}\t{n[2]}\n"
			msg += f"{n[3]}\t{n[4]}\t{n[5]}\n"
			msg += f"{n[6]}\t{n[7]}\t{n[8]}\n"

			msgSent = await interaction.send(msg)

		profit = 0
		for num in n:
			if winningNumber == num:
				profit += amntbet

		await interaction.send(f"You won {profit}{self.coin}")

		if profit != 0:
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, amntbet + profit)


def setup(bot):
	bot.add_cog(Scratch(bot))
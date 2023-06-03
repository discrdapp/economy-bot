import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, asyncio, random

from db import DB

class Coinflip(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command()
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, attach_files=True, use_external_emojis=True)
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author)	
	async def coinflip(self, interaction:Interaction, amntbet, sidebet = nextcord.SlashOption(
																required=True,
																name="side", 
																choices=("heads", "tails")), 
														user: nextcord.Member=None):
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)

		if user:
			def is_me(m):
				return m.channel.id == interaction.channel.id and m.author.id == user.id and m.content == "accept"

			msg = await interaction.send(f"{user.mention}, type: `accept`")
			try:
				await self.bot.wait_for('message', check=is_me, timeout=45)
			except:
				# await msg.edit(content=f"Timed out...")
				raise Exception("timeoutError")
				return

			if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
				raise Exception("tooPoor")

			if not await self.bot.get_cog("Economy").subtractBet(user, amntbet):
				await interaction.send(f"{user.mention} has either not typed /start yet or does not have enough money for this.")
				return

			side = random.choice(["Heads", "Tails"]).lower() # computer picks result

			file = None
			if side == "Heads":
				file = nextcord.File("./images/coinheads.png", filename="image.png")
			else:
				file = nextcord.File("./images/cointails.png", filename="image.png")
			if sidebet == side: # if author bets on correct side
				winner = interaction.user
			else: # else, user bet on correct side
				winner = user
			embed = nextcord.Embed(color=0x23f518)
			embed.set_thumbnail(url="attachment://image.png")
			embed.add_field(name=f"{self.bot.user.name} | Coinflip", value=f"The coin landed on {side}\n_ _{winner.mention} wins!", inline=False)

			await interaction.send(file=file, embed=embed)
			await self.bot.get_cog("Economy").addWinnings(winner.id, amntbet*2)

			return








		###################
		## SINGLE PLAYER ##
		###################

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")


		side = random.choice(["Heads", "Tails"]).lower()
		
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)

		embed = nextcord.Embed(color=0x23f518)
		
		if sidebet == side:
			moneyToAdd = int(amntbet * 2)
			profitInt = moneyToAdd - amntbet
			file = nextcord.File("./images/coinwon.png", filename="image.png")

		else:
			moneyToAdd = 0
			profitInt = moneyToAdd - amntbet
			file = nextcord.File("./images/coinlost.png", filename="image.png")
			embed.color = nextcord.Color(0xff2020)
			
		embed.set_thumbnail(url="attachment://image.png")
		embed.add_field(name=f"{self.bot.user.name} | Coinflip", value=f"The coin landed on {side}\n_ _",inline=False)
		giveZeroIfNeg = max(0, profitInt) # will give 0 if profitInt is negative. 
																		# we don't want it subtracting anything, only adding
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd + (giveZeroIfNeg * (multiplier - 1)))
		
		
		embed = await DB.addProfitAndBalFields(self, interaction, profitInt, embed)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed = await DB.calculateXP(self, interaction, balance - profitInt, amntbet, embed)

		await interaction.send(file=file, embed=embed)

		await self.bot.get_cog("Totals").addTotals(interaction, amntbet, moneyToAdd, 4)
		await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "CF", profitInt)

def setup(bot):
	bot.add_cog(Coinflip(bot))
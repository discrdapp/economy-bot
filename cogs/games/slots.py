import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, asyncio, random

from db import DB

class Slots(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command(description="Pay to play the slots!")
	@cooldowns.cooldown(1, 9, bucket=cooldowns.SlashBucket.author)
	@commands.bot_has_guild_permissions(send_messages=True, use_external_emojis=True)
	async def slots(self, interaction:Interaction, amntbet):
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Slots")
			embed.set_thumbnail(url=interaction.user.avatar)
			embed.add_field(name="ERROR", value="You do not have enough to do that.")

			embed.set_footer(text=interaction.user)

			await interaction.send(embed=embed)
			return

		emojis = "🍎🍋🍇🍓🍒🍊"

		a = random.choice(emojis)
		b = random.choice(emojis)
		c = random.choice(emojis)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}' Casino | Slots", type="rich")

		embed.add_field(name="----------------------------\n| 🎰  [  ]  [  ]  [  ]  🎰 |\n----------------------------", value="_ _")
		botMsg = await interaction.send(embed=embed)
		await asyncio.sleep(1.5)

		embed.set_field_at(0, name=f"------------------------------\n| 🎰  {a}  [  ]  [  ]  🎰 |\n------------------------------", value="_ _")
		await botMsg.edit(embed=embed)
		await asyncio.sleep(1.5)

		embed.set_field_at(0, name=f"-------------------------------\n| 🎰  {a}  {b}  [  ]  🎰 |\n-------------------------------", value="_ _")
		await botMsg.edit(embed=embed)
		await asyncio.sleep(1.5)

		embed.set_field_at(0, name=f"--------------------------------\n| 🎰  {a}  {b}  {c}  🎰 |\n--------------------------------", value="_ _")
		await botMsg.edit(embed=embed)

		#slotmachine = f"**[ {a} {b} {c} ]\n{interaction.user.name}**,"
		embed.color = nextcord.Color(0x23f518)
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user)
		if (a == b == c): # if all match
			moneyToAdd = int(amntbet * 2)
			profitInt = moneyToAdd - amntbet
			result = "YOU WON"
			profit = f"**{profitInt:,}** (**+{int(profitInt * (multiplier - 1)):,}**)"


		elif (a == b) or (a == c) or (b == c): # if two match
			moneyToAdd = int(amntbet * 1.5) # you win 150% your bet
			profitInt = moneyToAdd - amntbet
			result = "YOU WON"
			profit = f"**{profitInt:,}** (**+{int(profitInt * (multiplier - 1)):,}**)"


		else: # if no match
			moneyToAdd = 0
			profitInt = moneyToAdd - amntbet
			result = "YOU LOST"
			profit = f"**{profitInt:,}**"

			embed.color = nextcord.Color(0xff2020)

		giveZeroIfNeg = max(0, profitInt) # will give 0 if profitInt is negative. 
																			# we don't want it subtracting anything, only adding
																			
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd + (giveZeroIfNeg * (multiplier - 1)))
		embed.add_field(name=f"**--- {result} ---**", value="_ _", inline=False)
		embed = await DB.addProfitAndBalFields(self, interaction, profit, embed)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
		priorBal = balance - profitInt + (giveZeroIfNeg * (multiplier - 1))
		embed = await DB.calculateXP(self, interaction, priorBal, amntbet, embed)

		await botMsg.edit(embed=embed)
		await self.bot.get_cog("Totals").addTotals(interaction, amntbet, moneyToAdd, 0)

		await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "Slt", profitInt)


def setup(bot):
	bot.add_cog(Slots(bot))
import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns, asyncio, random

from db import DB

class Slots(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"

	@nextcord.slash_command(description="Pay to play the slots!")
	@cooldowns.cooldown(1, 9, bucket=cooldowns.SlashBucket.author, cooldown_id='slots')
	@commands.bot_has_guild_permissions(send_messages=True, use_external_emojis=True)
	async def slots(self, interaction:Interaction, amntbet):
		amntbet = await self.bot.get_cog("Economy").GetBetAmount(interaction, amntbet)

		if amntbet < 100:
			raise Exception("minBet 100")

		priorBal = await self.bot.get_cog("Economy").getBalance(interaction.user)

		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Slots")

		if not await self.bot.get_cog("Economy").subtractBet(interaction.user, amntbet):
			raise Exception("tooPoor")

		emojis = "🍎🍋🍇🍓🍒"

		a = random.choice(emojis)
		b = random.choice(emojis)
		c = random.choice(emojis)


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

		if (a == b == c) or ((a == b) or (a == c) or (b == c)):
			if (a == b == c): # if all match
				moneyToAdd = int(amntbet * 2)
			if (a == b) or (a == c) or (b == c): # if two match
				moneyToAdd = int(amntbet * 1.5) # you win 150% your bet
			
			result = "YOU WON"

		else: # if no match
			moneyToAdd = 0
			result = "YOU LOST"

			embed.color = nextcord.Color(0xff2020)

		gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, moneyToAdd, giveMultiplier=True, activityName="Slots", amntBet=amntbet)

		profitInt = moneyToAdd - amntbet

		embed.add_field(name=f"**--- {result} ---**", value="_ _", inline=False)

		embed = await DB.addProfitAndBalFields(self, interaction, profitInt, embed)
		embed = await DB.calculateXP(self, interaction, priorBal, amntbet, embed, gameID)

		await botMsg.edit(embed=embed)

		self.bot.get_cog("Totals").addTotals(interaction, amntbet, profitInt, "Slots")
		await self.bot.get_cog("Quests").AddQuestProgress(interaction, interaction.user, "Slt", profitInt)


def setup(bot):
	bot.add_cog(Slots(bot))
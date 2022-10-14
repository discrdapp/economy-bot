import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

from random import randint

import json

class Miner(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.dirtValue = 5
		self.stoneValue = 10
		self.coalValue = 20
		self.ironValue = 35
		self.goldValue = 40
		self.blocks = ["dirt", "stone", "coal", "iron", "gold"]
		self.coin = "<:coins:585233801320333313>"


	@nextcord.slash_command()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	async def miner(self, interaction:Interaction):
		pass

	# @miner.subcommand()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	# async def info(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Gameplay", value="`mine`, `sell`, `upgrade`", inline=False)
	# 	embed.add_field(name = "Usage", value="**.miner mine**", inline=False)
	# 	embed.set_footer(text=f"Profile: {interaction.user.name}")
	# 	await interaction.response.send_message(embed=embed)

	@miner.subcommand()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def mine(self, interaction:Interaction):

		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)

		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			inv = [32, 0, 0, 0, 0, 0]

		spaceUsed = 0
		for item in inv[1:]:
			spaceUsed += item
		# spaceLeft left is inventory size - the count
		spaceLeft = inv[0] - spaceUsed

		if spaceLeft <= 0:
			await interaction.response.send_message("You need to sell your blocks before you can mine some more.\nType `.miner sell`")
			return

		block = randint(0, 4)
		if block == 0: amnt = randint(16, 20)
		elif block == 1: amnt = randint(12, 16)
		elif block == 2: amnt = randint(8, 12)
		elif block == 3: amnt = randint(4, 8)
		elif block == 4: amnt = randint(1, 4)

		await interaction.response.send_message(f"Mined {amnt} {self.blocks[block]}!")

		if amnt < spaceLeft: 
			inv[block+1] += amnt
		else: 
			inv[block+1] += spaceLeft
			await interaction.followup.send("Your backpack is now full!")

		invFile[f"{interaction.user.id}"] = inv
		with open(r"miner.json", 'w') as f:
			json.dump(invFile, f, indent=4)

	@miner.subcommand()
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def sell(self, interaction:Interaction):
		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)
		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			await interaction.response.send_message("You haven't mined yet. Type `miner mine` to start")
			return

		dirtMoney = inv[1] * self.dirtValue
		stoneMoney = inv[2] * self.stoneValue
		coalMoney = inv[3] * self.coalValue
		ironMoney = inv[4] * self.ironValue
		goldMoney = inv[5] * self.goldValue

		totalMoney = dirtMoney + stoneMoney + coalMoney + ironMoney + goldMoney

		sellMsg = ""
		if inv[1]: sellMsg += f"Sold {inv[1]} dirt for {dirtMoney}{self.coin}\n"
		if inv[2]: sellMsg += f"Sold {inv[2]} stone for {stoneMoney}{self.coin}\n"
		if inv[3]: sellMsg += f"Sold {inv[3]} coal for {coalMoney}{self.coin}\n"
		if inv[4]: sellMsg += f"Sold {inv[4]} iron for {ironMoney}{self.coin}\n"
		if inv[5]: sellMsg += f"Sold {inv[5]} gold for {goldMoney}{self.coin}\n"
		
		if sellMsg:
			multiplier = self.bot.get_cog("Economy").getMultiplier(interaction.user)
			await self.bot.get_cog("Economy").addWinnings(interaction.user.id, totalMoney * multiplier)
			sellMsg += f"Total profit: {totalMoney} (+{int(totalMoney * (1 - multiplier))}){self.coin}"
			await interaction.response.send_message(sellMsg)
		else:
			await interaction.response.send_message("Your inventory is empty.")

		invFile[f"{interaction.user.id}"] = [32, 0, 0, 0, 0, 0]
		with open(r"miner.json", 'w') as f:
			json.dump(invFile, f, indent=4)


	@miner.subcommand()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def backpack(self, interaction:Interaction, what:str=None):
		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)

		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			await interaction.response.send_message("You haven't mined yet. Type `miner mine` to start")
			return

		msg = ""
		count = 0
		for i in inv:
			msg += f"{i} {self.blocks[count]}\n"
		await interaction.response.send_message(msg)

	@miner.subcommand()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def upgrade(self, interaction:Interaction, what:str=None):
		if not what:
			embed = nextcord.Embed(color=1768431)
			embed.add_field(name = "Pickaxe", value="Level 0 -> Level 1", inline=False)
			embed.add_field(name = "Inventory Size", value="32 -> 64", inline=False)
			embed.add_field(name = "Usage", value="**.miner upgrade <pickaxe/inventory>**", inline=False)
			embed.set_footer(text=f"User: {interaction.user.name}")
			await interaction.response.send_message(embed=embed)
			return

		await interaction.response.send_message("Work in Progress")



def setup(bot):
	bot.add_cog(Miner(bot))
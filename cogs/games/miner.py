import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
from random import randint

import json

from db import DB

# class BlockList():
# 	blocks = [
# 		{"name": "dirt", "value": 5, "emoji": emojiss.grass},
# 		{"name": "cobblestone", "value": 10, "emoji": emojiss.cobblestone},
# 		{"name": "coal", "value": 20, "emoji": emojiss.coal},
# 		{"name": "iron", "value": 35, "emoji": emojiss.iron},
# 		{"name": "gold", "value": 40, "emoji": emojiss.gold},
# 		{"name": "diamond", "value": 50, "emoji": emojiss.diamond}
# 	]

def GetBlocks():
	itemNameList = DB.fetchAll('SELECT * FROM MinerBlocks;')
	return itemNameList


class Miner(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.coin = "<:coins:585233801320333313>"
		self.blocks = GetBlocks()

	def getBackpackSize(self, interaction, file):
		try:	
			backpackLevel = file[f"{interaction.user.id}"]
			return backpackLevel * 32
		except:
			return 32

	@nextcord.slash_command()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	async def miner(self, interaction:Interaction):
		pass

	@miner.subcommand()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def mine(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431)
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Pickaxe"):
			embed.description = "You need a pickaxe to mine.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return
		if interaction.user.id != 547475078082985990:
			embed.description = "We're currently working on MINER 2.0. Please check back later!"
			return

		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)

		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			# 32 is the inventory size
			inv = [1, 1, 0, 0, 0, 0, 0, 0]

		spaceUsed = 0
		for item in inv[2:]:
			spaceUsed += item
		# spaceLeft left is inventory size - the count
		spaceLeft = self.getBackpackSize(interaction, inv) - spaceUsed

		if spaceLeft <= 0:
			embed.description = "You need to sell your blocks before you can mine some more.\nType `/miner sell`"
			await interaction.send(embed=embed, ephemeral=True)
			return

		# 0: dirt, 1: cobblestone, 2: coal, 3: iron, 4: gold
		unlockedCount = -1
		for block in self.blocks:
			if inv[1] >= block[4]:
				unlockedCount += 1
		block = randint(0, unlockedCount)

		if block == 0: amnt = randint(20, 24)
		elif block == 1: amnt = randint(16, 20)
		elif block == 2: amnt = randint(12, 16)
		elif block == 3: amnt = randint(8, 12)
		elif block == 4: amnt = randint(4, 8)
		elif block == 5: amnt = randint(1, 4)

		if amnt < spaceLeft: 
			# if inventory has space for all the blocks
			await interaction.send(f"Mined {amnt} {self.blocks[block][3]}!")
			inv[block+2] += amnt
		else: 
			# if inventory doesn't have space for all the blocks, fill it up
			await interaction.send(f"Mined {spaceLeft} {self.blocks[block][3]}!")
			inv[block+2] += spaceLeft
			await interaction.send("Your backpack is now full!", ephemeral=True)

		invFile[f"{interaction.user.id}"] = inv
		with open(r"miner.json", 'w') as f:
			json.dump(invFile, f, indent=4)

	@miner.subcommand()
	@cooldowns.cooldown(1, 10, bucket=cooldowns.SlashBucket.author)
	async def sell(self, interaction:Interaction):
		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)
		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			await interaction.send("You haven't mined yet. Type `/miner mine` to start", ephemeral=True)
			return

		if not inv[2] and not inv[2] and not inv[3] and not inv[4] and not inv[5]:
			await interaction.send("Your inventory is empty.", ephemeral=True)
			return

		count = -1
		totalMoney = 0
		sellMsg = ""
		for item in inv[2:]:
			count += 1
			if item == 0:
				continue
			sellMsg += f"Sold {item} {self.blocks[count][3]} for {item * self.blocks[count][2]}{self.coin}\n"
			totalMoney += item * self.blocks[count][2]
		
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, totalMoney * multiplier)
		sellMsg += f"Total earned: {totalMoney} (+{int(totalMoney * (1 - multiplier))}){self.coin}"
		await interaction.send(sellMsg)

		for x in range(2, len(inv)):
			inv[x] = 0
		invFile[f"{interaction.user.id}"] = inv

		with open(r"miner.json", 'w') as f:
			json.dump(invFile, f, indent=4)


	@miner.subcommand()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def backpack(self, interaction:Interaction):
		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)

		embed = nextcord.Embed(color=1768431)
		try:
			inv = invFile[f"{interaction.user.id}"]
		except:
			embed.description = "You haven't mined yet. Type `/miner mine` to start"
			await interaction.send(embed=embed, ephemeral=True)
			return
		
		embed.description = f"Backpack ({sum(inv[2:])}/{inv[0]*32}):\n"
		count = 0
		for num in inv[2:]:	
			if inv[1] >= self.blocks[count][4]: 
				embed.add_field(name="_ _", value=f"\t{num} {self.blocks[count][3]}\n")
			
			count += 1
		
		embed.set_footer(text="Upgrade your backpack to increase its size\nUpgrade your pickaxe to unlock more blocks")
		await interaction.send(embed=embed)

	@miner.subcommand()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def upgrade(self, interaction:Interaction, userchoice = nextcord.SlashOption(required=True,name="item", choices=("pickaxe", "backpack"))):
		embed = nextcord.Embed(color=1768431)
		# embed.add_field(name = "Pickaxe", value="Level 0  ➡️  Level 1", inline=False)
		# embed.add_field(name = "Backpack Size", value="32  ➡️  64", inline=False)
		# embed.add_field(name = "Usage", value="**/miner upgrade <pickaxe/backpack>**", inline=False)
		# embed.set_footer(text=f"User: {interaction.user.name}")
		# await interaction.send(embed=embed)
		with open(r"miner.json", 'r') as f:
			invFile = json.load(f)

		if userchoice == "pickaxe":
			invFile[f"{interaction.user.id}"][1] += 1
			lvl = invFile[f"{interaction.user.id}"][1]
			embed.add_field(name = "⛏️ Pickaxe Level", value=f"`{lvl-1} -> {lvl}`", inline=False)
			# await interaction.send(embed=embed, ephemeral=True)

			msg = ""
			for block in self.blocks:
				if lvl == block[4]:
					msg += f"{block[3]}\t"
			if msg:
				embed.add_field(name = "Unlocked Blocks", value=msg, inline=False)
			await interaction.send(embed=embed, ephemeral=True)

		elif userchoice == "backpack":
			invFile[f"{interaction.user.id}"][0] += 1
			lvl = invFile[f"{interaction.user.id}"][0]
			size = lvl * 32
			embed.add_field(name = "Backpack Level", value=f"`{lvl-1} -> {lvl}`", inline=False)
			embed.add_field(name = "Size", value=f"`{size-32} -> {size}`", inline=False)
		
			await interaction.send(embed=embed, ephemeral=True)

		with open(r"miner.json", 'w') as f:
			json.dump(invFile, f, indent=4)
	
	@miner.subcommand()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def level(self, interaction:Interaction, userchoice = nextcord.SlashOption(required=True,name="item", choices=("pickaxe", "backpack"))):
		if userchoice == "pickaxe":
			with open(r"miner.json", 'r') as f:
				invFile = json.load(f)

			lvl = invFile[f"{interaction.user.id}"][1]
		elif userchoice == "backpack":
			with open(r"miner.json", 'r') as f:
				invFile = json.load(f)

			lvl = invFile[f"{interaction.user.id}"][0]
		
		await interaction.send(f"{userchoice.title()} Level {lvl}", ephemeral=True)

def setup(bot):
	bot.add_cog(Miner(bot))
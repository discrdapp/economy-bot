import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns
from random import randint

import config, emojis
from db import DB

def GetBlocks():
	itemNameList = DB.fetchAll('SELECT * FROM MinerBlocks;')
	return itemNameList
def GetHighestLevelBlock():
	highestLevelBlock = DB.fetchOne('SELECT RequiresPickaxeLevel FROM MinerBlocks ORDER BY RequiresPickaxeLevel DESC LIMIT 1')[0]

	return highestLevelBlock


class Miner(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.blocks = GetBlocks()
		self.highestLevelBlock = GetHighestLevelBlock()

	def getInventory(self, userId, whatToGet=None):
		if whatToGet:
			inv = DB.fetchOne(f"SELECT {whatToGet} FROM MinerInventory WHERE DiscordID = ?;", [userId])

			if not inv:
				DB.insert('INSERT INTO MinerInventory(DiscordID) VALUES (?);', [userId])
				inv = DB.fetchOne(f"SELECT {whatToGet} FROM MinerInventory WHERE DiscordID = ?;", [userId])
			
			return inv[0]
		else:
			inv = DB.fetchOne("SELECT * FROM MinerInventory WHERE DiscordID = ?;", [userId])

			if not inv:
				DB.insert('INSERT INTO MinerInventory(DiscordID) VALUES (?);', [userId])
				inv = DB.fetchOne("SELECT * FROM MinerInventory WHERE DiscordID = ?;", [userId])

			return inv

	def getBackpackSize(self, interaction:Interaction):
		return DB.fetchOne('SELECT BackpackLevel FROM MinerInventory WHERE DiscordID = ?;', [interaction.user.id])[0]*32

	cooldowns.define_shared_cooldown(1, 1, cooldowns.SlashBucket.author, cooldown_id="miner")

	@nextcord.slash_command()
	@cooldowns.shared_cooldown("miner")
	async def miner(self, interaction:Interaction):
		pass

	@miner.subcommand()
	@cooldowns.shared_cooldown("miner")
	async def mine(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431)
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Pickaxe"):
			embed.description = "You need a pickaxe to mine.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return

		inv = self.getInventory(interaction.user.id)


		spaceUsed = 0
		for item in inv[3:]:
			spaceUsed += item
		# spaceLeft left is inventory size - the count
		spaceLeft = self.getBackpackSize(interaction) - spaceUsed

		if spaceLeft <= 0:
			embed.description = "Your backpack is full! You will need to sell your blocks before you can Mine some more."
			embed.set_footer(text="Use /miner sell to clear up some space!")
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
			embed.description = f"Mined {amnt} {self.blocks[block][3]}!"
			await interaction.send(embed=embed)
			# inv[block+2] += amnt
			amntToSetTo = inv[block+3] + amnt
		else: 
			# if inventory doesn't have space for all the blocks, fill it up
			embed.description = f"Mined {spaceLeft} {self.blocks[block][3]}!"
			# inv[block+2] += spaceLeft
			amntToSetTo = inv[block+3] + spaceLeft
			embed.set_footer(text="Your backpack is now full!")
			await interaction.send(embed=embed)

		blockName = self.blocks[block][1]
		DB.update(f"UPDATE MinerInventory SET {blockName} = ? WHERE DiscordID = ?;", [amntToSetTo, interaction.user.id])

	@miner.subcommand()
	@cooldowns.shared_cooldown("miner")
	async def sell(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431)
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Pickaxe"):
			embed.description = "You need a Pickaxe to use the Mine commands.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return
		inv = self.getInventory(interaction.user.id)

		count = -1
		totalMoney = 0
		sellMsg = ""
		for item in inv[3:]:
			count += 1
			if item == 0:
				continue
			sellMsg += f"Sold {item} {self.blocks[count][3]} for {(item * self.blocks[count][2]):,}{emojis.coin}\n"
			totalMoney += item * self.blocks[count][2]
		
		if totalMoney == 0:
			embed.description = "You have no blocks to sell! Use `/miner mine` to mine some blocks"
			await interaction.send(embed=embed)
			return
		
		multiplier = self.bot.get_cog("Multipliers").getMultiplier(interaction.user.id)
		gameID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, totalMoney, giveMultiplier=True, activityName="Miner", amntBet=0)
		sellMsg += f"Total earned: {totalMoney:,} (+{int(totalMoney * (multiplier - 1)):,}){emojis.coin}"

		embed.description = sellMsg
		embed.set_footer(text=f"\nGameID: {gameID}")
		await interaction.send(embed=embed)

		DB.update(f"UPDATE MinerInventory SET Dirt = 0, Cobblestone = 0, Coal = 0, Iron = 0, Gold = 0, Emerald = 0, Diamond = 0 WHERE DiscordID = ?;", [interaction.user.id])



	@miner.subcommand()
	@cooldowns.shared_cooldown("miner")
	async def backpack(self, interaction:Interaction):
		inv = self.getInventory(interaction.user.id)
		
		embed = nextcord.Embed(color=1768431)
		embed.description = f"**Backpack ({sum(inv[3:])}/{self.getBackpackSize(interaction)}):**\n"
		count = 0
		for num in inv[3:]:	
			if inv[2] >= self.blocks[count][4]: 
				embed.add_field(name="_ _", value=f"\t{num} {self.blocks[count][3]}\n")
			
			count += 1
		
		embed.set_footer(text="/upgrade your backpack to increase its size\n/upgrade your pickaxe to unlock more blocks")
		await interaction.send(embed=embed)

	@miner.subcommand()
	@cooldowns.shared_cooldown("miner")
	async def upgrade(self, interaction:Interaction, userchoice = nextcord.SlashOption(required=True,name="item", choices=("pickaxe", "backpack"))):
		embed = nextcord.Embed(color=1768431)

		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Pickaxe"):
			embed.description = "You need a Pickaxe to use the Mine commands.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return

		if interaction.user.id != config.botOwnerDiscordID:
			embed.description = "Upgrading is disabled while we work on a permanent solution for it..."
			await interaction.send(embed=embed)
			return

		if userchoice == "pickaxe":
			lvl = self.getInventory(interaction.user.id, "PickaxeLevel")

			if lvl == self.highestLevelBlock:
				embed.description = "You're already at the highest level!"
				await interaction.send(embed=embed)
				return

			DB.update("UPDATE MinerInventory SET PickaxeLevel = PickaxeLevel + 1 WHERE DiscordID = ?;", [interaction.user.id])
			embed.add_field(name = "⛏️ Pickaxe Level", value=f"`{lvl} -> {lvl+1}`", inline=False)
			# await interaction.send(embed=embed, ephemeral=True)

			msg = ""
			for block in self.blocks:
				if (lvl+1) == block[4]:
					msg += f"{block[3]}\t"
			if msg:
				embed.add_field(name = "Unlocked Blocks", value=msg, inline=False)
			await interaction.send(embed=embed, ephemeral=True)

		elif userchoice == "backpack":
			lvl = self.getInventory(interaction.user.id, "BackpackLevel")
			if lvl == 3:
				embed.description = "Your backpack is already at the highest level!"
				await interaction.send(embed=embed)
				return
			DB.update("UPDATE MinerInventory SET BackpackLevel = BackpackLevel + 1 WHERE DiscordID = ?;", [interaction.user.id])
			size = (lvl+1) * 32
			embed.add_field(name = "Backpack Level", value=f"`{lvl} -> {lvl+1}`", inline=False)
			embed.add_field(name = "Size", value=f"`{size-32} -> {size}`", inline=False)

			await interaction.send(embed=embed, ephemeral=True)

	@miner.subcommand()
	@cooldowns.shared_cooldown("miner")
	async def level(self, interaction:Interaction, userchoice = nextcord.SlashOption(required=True,name="item", choices=("pickaxe", "backpack"))):
		embed = nextcord.Embed(color=1768431)
		if not self.bot.get_cog("Inventory").checkInventoryFor(interaction.user, "Pickaxe"):
			embed.description = "You need a Pickaxe to use the Mine commands.\nYou can buy one from the /shop"
			await interaction.send(embed=embed)
			return
		if userchoice == "pickaxe":
			lvl = self.getInventory(interaction.user.id, "PickaxeLevel")
		elif userchoice == "backpack":
			lvl = self.getInventory(interaction.user.id, "BackpackLevel")
		
		await interaction.send(f"{userchoice.title()} Level {lvl}", ephemeral=True)

def setup(bot):
	bot.add_cog(Miner(bot))
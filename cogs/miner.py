import discord
from discord.ext import commands

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


	@commands.group()
	# @commands.cooldown(1, 3, commands.BucketType.user)
	async def miner(self, ctx):
		if not ctx.invoked_subcommand:
			embed = discord.Embed(color=1768431)
			embed.add_field(name = "Gameplay", value="`mine`, `sell`, `upgrade`", inline=False)
			embed.add_field(name = "Usage", value="**.miner mine**", inline=False)
			embed.set_footer(text=f"Profile: {ctx.author.name}")
			await ctx.send(embed=embed)

	@miner.command()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def mine(self, ctx):

		with open(r"inventory.json", 'r') as f:
			invFile = json.load(f)

		try:
			inv = invFile[f"{ctx.author.id}"]
		except:
			inv = [32, 0, 0, 0, 0, 0]

		space = 0
		# for block in inventory
		for x in inv[1:]:
			# count # of blocks
			space += x 
		# space left is inventory size - the count
		space = inv[0] - space

		if space <= 0:
			await ctx.send("You need to sell your blocks before you can mine some more.\nType `.miner sell`")
			return

		block = randint(0, 4)
		if block == 0: amnt = randint(16, 20)
		elif block == 1: amnt = randint(12, 16)
		elif block == 2: amnt = randint(8, 12)
		elif block == 3: amnt = randint(4, 8)
		elif block == 4: amnt = randint(1, 4)

		await ctx.send(f"Mined {amnt} {self.blocks[block]}!")

		if amnt < space: 
			inv[block+1] += amnt
		else: 
			inv[block+1] += space
			await ctx.send("Your backpack is now full!")

		invFile[f"{ctx.author.id}"] = inv
		with open(r"inventory.json", 'w') as f:
			json.dump(invFile, f, indent=4)

	@miner.command()
	@commands.cooldown(1, 10, commands.BucketType.user)
	async def sell(self, ctx):
		with open(r"inventory.json", 'r') as f:
			invFile = json.load(f)
		try:
			inv = invFile[f"{ctx.author.id}"]
		except:
			await ctx.send("You haven't mined yet. Type `miner mine` to start")

		sellMsg = ""

		if inv[1]: sellMsg += f"Sold {inv[1]} dirt for {inv[1]*self.dirtValue} {self.coin}"
		if inv[2]: sellMsg += f"Sold {inv[2]} stone for {inv[2]*self.stoneValue} {self.coin}"
		if inv[3]: sellMsg += f"Sold {inv[3]} coal for {inv[3]*self.coalValue} {self.coin}"
		if inv[4]: sellMsg += f"Sold {inv[4]} iron for {inv[4]*self.ironValue} {self.coin}"
		if inv[5]: sellMsg += f"Sold {inv[5]} gold for {inv[5]*self.goldValue} {self.coin}"
		
		if sellMsg:
			await ctx.send(sellMsg)
		else:
			await ctx.send("Your inventory is empty.")

		invFile[f"{ctx.author.id}"] = [32, 0, 0, 0, 0, 0]
		with open(r"inventory.json", 'w') as f:
			json.dump(invFile, f, indent=4)


	@miner.command()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def backpack(self, ctx, what:str=None):
		with open(r"inventory.json", 'r') as f:
			invFile = json.load(f)

		try:
			inv = invFile[f"{ctx.author.id}"]
		except:
			await ctx.send("You haven't mined yet. Type `miner mine` to start")

		msg = ""
		count = 0
		for i in inv:
			msg += f"{i} {self.blocks[count]}\n"
		await ctx.send(msg)

	@miner.command()
	@commands.cooldown(1, 3, commands.BucketType.user)
	async def upgrade(self, ctx, what:str=None):
		if not what:
			embed = discord.Embed(color=1768431)
			embed.add_field(name = "Pickaxe", value="Level 0 -> Level 1", inline=False)
			embed.add_field(name = "Inventory Size", value="32 -> 64", inline=False)
			embed.add_field(name = "Usage", value="**.miner upgrade <pickaxe/inventory>**", inline=False)
			embed.set_footer(text=f"User: {ctx.author.name}")
			await ctx.send(embed=embed)
			return

		await ctx.send("Work in Progress")



def setup(bot):
	bot.add_cog(Miner(bot))
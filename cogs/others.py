import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
from discord.utils import find

import json

class Others(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		ch = self.bot.get_channel(790282431860047882)
		await ch.send(f"Added to {guild.name}")
		general = find(lambda x: 'general' in x.name.lower(), guild.text_channels)
		if general and general.permissions_for(guild.me).send_messages:
			await general.send(f'Hello {guild.name}, and thanks for adding me!\nType `.help` for my commands.\nEveryone will need to type `.start` in order to register!')
		else:
			try:
				await guild.owner.send('Error: I either do not have permissions to send messages or there is not a `general` channel for me to send my welcome message.')
			except:
				pass

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		ch = self.bot.get_channel(790282431860047882)
		await ch.send(f"Removed from {guild.name}")


	# @commands.Cog.listener()
	# async def on_member_remove(self, member):
	# 	if member.guild.id != 585226670361804827:
	# 		return
	# 	ch = self.bot.get_channel(791002207138742292)
	# 	await ch.send(f"*{member.name} has left*")


	@commands.command()
	@has_permissions(administrator=True)
	@commands.bot_has_guild_permissions(send_messages=True)
	async def prefix(self, ctx, *, newprefix):
		with open(r"prefix.json", 'r') as f:
			config = json.load(f)

		config[f"{ctx.guild.id}"] = newprefix

		with open(r"prefix.json", 'w') as f:
			json.dump(config, f, indent=4)

		await self.bot.change_presence(activity=discord.Game(name=f"Do {newprefix}help for help!"))
		embed = discord.Embed(title=f"{self.bot.user.name}: ADMIN", color=0xdfe324, description=f"Successfully changed prefix to **{newprefix}**")	
		await ctx.send(embed=embed)

	async def get_prefix(self, ctx):
		with open(r"prefix.json", 'r') as f:
			prefix = json.load(f)

		try:
			return prefix[f"{ctx.guild.id}"]
		except:
			return "."

	@commands.command()
	async def claim(self, ctx):
		if ctx.guild.id != 585226670361804827:
			return
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.send("Hello! Please type .start to create your wallet. :smiley:")
			return
		userId = str(ctx.author.id)
		with open("claimed.txt", "r") as claimedFile:
			for line in claimedFile:
				if userId in line:
					await ctx.send("You have already claimed your reward!")
					return
		with open("claimed.txt", 'a') as claimedFile:
			claimedFile.write(f"{userId}\n") 
		await self.bot.get_cog("Economy").addWinnings(ctx.author.id, 7500)

		bal = await self.bot.get_cog("Economy").getBalance(ctx.author)
		await ctx.send(f"Successfully claimed reward! New balance is {bal}")


	@commands.group(invoke_without_command=True, case_insensitive=True)
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	async def help(self, ctx):
		prefix = await self.get_prefix(ctx)

		embed = discord.Embed(color=1768431, title="Thanks for taking an interest in me!")
		embed.set_footer(text="And that's all for now folks!")
		embed.add_field(name = ":game_die: Game commands", 
						 value="`roulette`, `crash`, `blackjack`, " 
							 + "`slots`, `coinflip`, `rps`, `colorguesser`")

		embed.add_field(name = ":gear: Other commands",
					   value = "`credits`, `top`, `position`, `shop`, `stats`, "
							 + "`profile`, `level`, `freemoney`, `rewards`, `crate`", inline=False)

		# embed.add_field(name = ":grey_exclamation: Miscellaneous",
		# 				value = f"\n[Join official server](https://discord.gg/ggUksVN) and use `.claim` for free 7,500{self.coin}")
						# value = "\n[Support](https://www.paypal.me/AutopilotJustin) gambling bot's development or [join support server](https://discord.gg/ggUksVN).")
		embed.add_field(name = "_ _",
						value = f"Your prefix is **{prefix}**\n\n***\*\*NEW\*\**** [Join official server](https://discord.gg/ggUksVN) and use `.claim` for free 7,500{self.coin}", inline=False)
		await ctx.send(embed=embed)

	@help.command()
	async def bank(self, ctx):
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Store your credits in the bank", inline=False)
		embed.add_field(name = "Usage", value="**.bank <deposit/withdraw> amount**", inline=False)
		embed.set_footer(text=f"User: {ctx.author.name}")
		await ctx.send(embed=embed)

	# @help.command()
	# async def roulette(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description=f"Predict the characteristics that the number \nUsage: {prefix}roulette")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def crash(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description=f"Play reaction-based roulette. No extra parameters necessary.\nUsage: {prefix}crash <betAmount>")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def blackjack(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description=f"Play blackjack! Get your cards to 21 (without going over!) or beat the dealer to win!\nUsage: {prefix}blackjack <betAmount>")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def slots(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description=f"Buy something from the shop! Type +shop for more details.\nUsage: {prefix}slots <betAmount>")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def coinflip(self, ctx):
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description=f"Send money to someone else in the server.\nUsage: `+send <user> <amount>`\nUsage: {prefix}coinflip <sideBet> <betAmount>\nExample: {prefix}coinflip heads 100")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def credits(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Show the users with the most money in the server! You can also type `+lb`")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def top(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Show the users with the most money in the server!")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def shop(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Try to commit a crime to earn some money.\nUsage: `+crime`")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def stats(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Risk some of your money to win some money.\nUsage: `+gamble <amount>`")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def profile(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Risk some of your money and play the slot machine.\nUsage: `+slots <amount>`")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def level(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Claim your daily reward!")
	# 	await ctx.send(embed=embed)

	# @help.command()
	# async def freemoney(self, ctx):
	# 	prefix = await self.get_prefix(ctx)
	# 	embed = discord.Embed(title=f"{self.bot.user.name} Help: {ctx.command.name}", color=0xdfe324, 
	# 		description="Claim your daily reward!")
	# 	await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Others(bot))
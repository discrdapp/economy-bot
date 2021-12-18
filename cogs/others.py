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
		embed = discord.Embed(color=1768431, title=f"{self.bot.user.name}")
		ch = self.bot.get_channel(790282431860047882)
		await ch.send(f"Added to {guild.name}")
		general = find(lambda x: 'general' in x.name.lower(), guild.text_channels)
		if general and not general.permissions_for(guild.me).send_messages:
			general = None
		if not general: general = find(lambda x: 'chat' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'chit' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'lobby' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'talk' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'commands' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'cmd' in x.name.lower(), guild.text_channels)
		if not general: general = find(lambda x: 'bot' in x.name.lower(), guild.text_channels)

		if general and general.permissions_for(guild.me).send_messages and general.permissions_for(guild.me).embed_links:
			embed.add_field(name="Greetings!", value="Type .help to see a list of my commands."
				+ "\n[Click here](https://discord.gg/ggUksVN) to join the support server.")
			await general.send(embed=embed)

	# @commands.command()
	# async def yeet(self, ctx):
	# 	embed = discord.Embed(color=1768431, title=f"{self.bot.user.name}")
	# 	embed.add_field(name="Greetings!", value="Error: I either do not have permissions to send messages or there is not a general " + 
	# 			"channel for me to send my welcome message, but hello and thanks for adding me!\nType .help in the server for my commands.")
	
	# 	owner = ctx.guild.get_member(ctx.guild.owner_id)
	# 	await ctx.send(f"Owner is: {owner}")
	# 	await owner.send(embed=embed)

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

	@commands.command(aliases=['policy', 'tos', 'termsofservice', 'privacypolicy', 'policyprivacy'])
	async def privacy(self, ctx):
		msg = "This bot only keeps track of your Discord ID once you type the `.start` command."
		msg += f"\nThis is used to associate your Discord account to everything in your `{ctx.prefix}profile`, `{ctx.prefix}totals`, and `{ctx.prefix}xp`."
		msg += "\nThis data is stored on a secured Database server."
		msg += "\n\nDiscord IDs are publically available for anyone to retrieve by turning on Discord's Developer Mode."
		msg += "\n\nServer-wise, if you use our `.prefix` command, we will store your Server ID with your preferred prefix. This data is stored in a file on a secured server."
		msg += "\n\nNo one gets access to this data. The only one who has access to it is PyCord#3494. But again, no personal data is stored."
		msg += f"\n\nIf you have any concerns or want your data removed, feel free to contact PyCord#3494 or join the support server in the `{ctx.prefix}help` menu."
		await ctx.send(msg)

	@commands.command()
	@has_permissions(administrator=True)
	@commands.bot_has_guild_permissions(send_messages=True)
	async def prefix(self, ctx, *, newprefix):
		with open(r"prefix.json", 'r') as f:
			config = json.load(f)

		config[f"{ctx.guild.id}"] = newprefix

		with open(r"prefix.json", 'w') as f:
			json.dump(config, f, indent=4)

		embed = discord.Embed(title=f"{self.bot.user.name}: ADMIN", color=0xdfe324, description=f"Successfully changed prefix to **{newprefix}**")	
		await ctx.send(embed=embed)

	@commands.command()
	async def claim(self, ctx):
		if ctx.guild.id != 585226670361804827:
			return
		if not await self.bot.get_cog("Economy").accCheck(ctx.author):
			await ctx.invoke(self.bot.get_command('start'))
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
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def help(self, ctx):
		prefix = ctx.prefix

		embed = discord.Embed(color=1768431, title="Thanks for taking an interest in me!")
		embed.set_footer(text="And that's all for now folks!")
		embed.add_field(name = ":game_die: Game Commands", 
						 value="`roulette`, `crash`, `blackjack`, " 
							 + "`slots`, `coinflip`, `rps`, `colorguesser`, `lottery`, `rob`")

		embed.add_field(name = ":gear: Other Commands",
					   value = "`credits`, `top`, `position`, `shop`, `stats`, `bank`, `claim`, `vote`, "
							 + "`profile`, `level`, `rewards`, `crate`", inline=False)

		embed.add_field(name = ":money_with_wings: Earn Money",
					   value = "`work`, `daily`, `weekly`, `monthly`, `search`, and more coming soon...", inline=False)

		embed.add_field(name=":grey_question: ***NEW***  Quests", value=f"`quests` <-- IN BETA! REPORT ANY BUGS.")

		# embed.add_field(name = ":grey_exclamation: Miscellaneous",
		# 				value = f"\n[Join official server](https://discord.gg/ggUksVN) and use `.claim` for free 7,500{self.coin}")
						# value = "\n[Support](https://www.paypal.me/AutopilotJustin) gambling bot's development or [join support server](https://discord.gg/ggUksVN).")
		embed.add_field(name = "_ _",
						value = f"Your prefix is **{prefix}**\n\n***\*\*NEW\*\**** [Join official server](https://discord.gg/ggUksVN) and use `.claim` for free 7,500{self.coin}\nAdd this bot to your server - [Click Here](https://discord.com/api/oauth2/authorize?client_id=585235000459264005&permissions=387136&scope=bot)", inline=False)
		await ctx.send(embed=embed)

	@help.command()
	async def bank(self, ctx):
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Store your credits in the bank", inline=False)
		embed.add_field(name = "Usage", value="**.bank <deposit/withdraw> <amount>**\n**.bank balance**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def roulette(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Bet on the characteristics that the number will land on", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}roulette**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def crash(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Withdraw your funds before the stock market crashes!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}crash <bet>**", inline=False)
		embed.add_field(name = "Chances", value=f"1.0x is 30%\n1.2x is 20%\n1.4x - 1.6x is 30%\n1.6x - 2.4x is 10%\n2.4x - 10.0x is 10%", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command(aliases=['bj'])
	async def blackjack(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Get your cards to 21 (without going over!) or beat the dealer to win!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}blackjack <bet>**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command(aliases=['cg'])
	async def colorguesser(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Play with friends. Everyone votes for a color the bot will pick.", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}colorguesser <bet>**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def slots(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Play the slots and try to get the same fruit!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}slots <bet>**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def rps(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Beat the computer in a classic game of Rock-Paper-Scissors", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}rps <rock/paper/scissors> <bet>**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command(aliases=["cf"])
	async def coinflip(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Bet the side the coin will land on", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}coinflip <heads/tails> <bet>**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def credits(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Look at your balance", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}credits**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def top(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Show the users with the most money in the server!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}top**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def shop(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Buy something at the shop!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}shop**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def stats(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Check the statistics of the games you've played", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}stats**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def profile(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="View your profile", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}profile**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def level(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Look at your level and your XP", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}level**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)

	@help.command()
	async def freemoney(self, ctx):
		prefix = ctx.prefix
		embed = discord.Embed(color=1768431)
		embed.add_field(name = "Help", value="Look at all the ways to get free money!", inline=False)
		embed.add_field(name = "Usage", value=f"**{prefix}freemoney**", inline=False)
		embed.set_footer(text=f"User: {ctx.author}")
		await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(Others(bot))
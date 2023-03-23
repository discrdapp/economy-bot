import nextcord
from nextcord.ext import commands 
from nextcord import Interaction
from nextcord import FFmpegPCMAudio 
from nextcord import Member 
from nextcord.ext.commands import has_permissions, MissingPermissions

import cooldowns
from typing import Optional

import json

class Others(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.coin = "<:coins:585233801320333313>"

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}")
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
			embed.add_field(name="Greetings!", value="Type /help to see a list of my commands."
				+ "\n[Click here](https://discord.gg/ggUksVN) to join the support server.")
			await general.send(embed=embed)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		ch = self.bot.get_channel(790282431860047882)
		await ch.send(f"Removed from {guild.name}")

	@nextcord.slash_command()
	async def privacy(self, interaction:Interaction):
		msg = "This bot only keeps track of your Discord ID once you type the `/start` command."
		msg += f"\nThis is used to associate your Discord account to everything in your `/profile`, `/totals`, and `/xp`."
		msg += "\nThis data is stored on a secured Database server."
		msg += "\n\nDiscord IDs are publically available for anyone to retrieve by turning on Discord's Developer Mode."
		msg += "\n\nThis data is stored in a file on a secured server."
		msg += "\n\nNo one gets access to this data. The only one who has access to it is PyCord#3494. But again, no personal data is stored."
		msg += f"\n\nIf you have any concerns or want your data removed, feel free to contact PyCord#3494 or join the support server in the `/help` menu."
		await interaction.send(msg)

	@nextcord.slash_command()
	async def claim(self, interaction:Interaction):
		if interaction.guild.id != 585226670361804827:
			return
		if not await self.bot.get_cog("Economy").accCheck(interaction.user):
			await self.bot.get_cog("Economy").StartPlaying(interaction, interaction.user)
		userId = str(interaction.user.id)
		with open("claimed.txt", "r") as claimedFile:
			for line in claimedFile:
				if userId in line:
					await interaction.send("You have already claimed your reward!")
					return
		with open("claimed.txt", 'a') as claimedFile:
			claimedFile.write(f"{userId}\n") 
		await self.bot.get_cog("Economy").addWinnings(interaction.user.id, 7500)

		bal = await self.bot.get_cog("Economy").getBalance(interaction.user)
		await interaction.send(f"Successfully claimed reward! New balance is {bal}")


	@nextcord.slash_command()
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author)
	async def help(self, interaction:Interaction, option:Optional[str] = nextcord.SlashOption(required=False,
												name="choice", 
												choices=("bank", "roulette", "crash", "blackjack", "colorguesser", 
													"slots", "rockpaperscissors", "coinflip", "credits", "shop", 
													"stats", "profile", "level", "freemoney"))):

		if not option:
			embed = nextcord.Embed(color=1768431, title="Thanks for taking an interest in me!")
			embed.set_footer(text="And that's all for now folks!")

			embed.add_field(name = "BOT HAS SWITCHED TO SLASH COMMANDS", value="All commands will start with slash (/). Some commands are a WIP.", inline=False)
			
			embed.add_field(name = ":game_die: Game Commands", 
							 value="`roulette`, `crash`, `blackjack`, " 
								 + "`slots`, `coinflip`, `rps`, `colorguesser`, `rob`", inline = False)

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
							value = f"[Join official server](https://discord.gg/ggUksVN) and use `.claim` for free 7,500{self.coin}\nAdd this bot to your server - [Click Here](https://discord.com/api/oauth2/authorize?client_id=585235000459264005&permissions=387136&scope=bot)", inline=False)
			await interaction.send(embed=embed)
			return

		embed = nextcord.Embed(color=1768431)

		if option == "bank":
			helpMsg = "Store your credits in the bank"
			usageMsg = "**/bank <deposit/withdraw> <amount>**\n**/bank balance**"
		elif option == "roulette":
			helpMsg = "Bet on the characteristics that the number will land on"
			usageMsg = "**/roulette**"
		elif option == "crash":
			helpMsg = "Withdraw your funds before the stock market crashes!"
			usageMsg = "**/crash <bet>**"
		elif option == "blackjack":
			helpMsg = "Get your cards to 21 (without going over!) or beat the dealer to win!"
			usageMsg = "**/blackjack <bet>**"
		elif option == "colorguesser":
			helpMsg = "Play with friends. Everyone votes for a color the bot will pick."
			usageMsg = "**/colorguesser <bet>**"
		elif option == "slots":
			helpMsg = "Play the slots and try to get the same fruit!"
			usageMsg = "**/slots <bet>**"
		elif option == "rockpaperscissors":
			helpMsg = "Beat the computer in a classic game of Rock-Paper-Scissors"
			usageMsg = "**/rps <rock/paper/scissors> <bet>**"
		elif option == "coinflip":
			helpMsg = "Bet the side the coin will land on"
			usageMsg = "**/coinflip <heads/tails> <bet>**"
		elif option == "credits":
			helpMsg = "Look at your balance"
			usageMsg = "**/credits**"
		elif option == "top":
			helpMsg = "Show the users with the most money in the server!"
			usageMsg = "**/top**"
		elif option == "shop":
			helpMsg = "Buy something at the shop!"
			usageMsg = "**/shop**"
		elif option == "stats":
			helpMsg = "Check the statistics of the games you've played"
			usageMsg = "**/stats**"
		elif option == "profile":
			helpMsg = "View your profile"
			usageMsg = "**/profile**"
		elif option == "level":
			helpMsg = "Look at your level and your XP"
			usageMsg = "**/level**"
		elif option == "freemoney":
			helpMsg = "Look at all the ways to get free money!"
			usageMsg = "**/freemoney**"
		

		embed.add_field(name = "Help", value=f"{helpMsg}", inline=False)
		embed.add_field(name = "Usage", value=f"{usageMsg}", inline=False)

		if option == "crash":
			embed.add_field(name = "Chances", value=f"1.0x is 30%\n1.2x is 20%\n1.4x - 1.6x is 30%\n1.6x - 2.4x is 10%\n2.4x - 10.0x is 10%", inline=False)


		embed.set_footer(text=f"User: {interaction.user}")
		await interaction.send(embed=embed)

	# @help.subcommand()
	# async def bank(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Store your credits in the bank", inline=False)
	# 	embed.add_field(name = "Usage", value="**.bank <deposit/withdraw> <amount>**\n**.bank balance**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def roulette(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Bet on the characteristics that the number will land on", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/roulette**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def crash(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Withdraw your funds before the stock market crashes!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/crash <bet>**", inline=False)
	# 	embed.add_field(name = "Chances", value=f"1.0x is 30%\n1.2x is 20%\n1.4x - 1.6x is 30%\n1.6x - 2.4x is 10%\n2.4x - 10.0x is 10%", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def blackjack(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Get your cards to 21 (without going over!) or beat the dealer to win!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/blackjack <bet>**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def colorguesser(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Play with friends. Everyone votes for a color the bot will pick.", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/colorguesser <bet>**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def slots(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Play the slots and try to get the same fruit!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/slots <bet>**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def rps(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Beat the computer in a classic game of Rock-Paper-Scissors", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/rps <rock/paper/scissors> <bet>**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def coinflip(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Bet the side the coin will land on", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/coinflip <heads/tails> <bet>**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def credits(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Look at your balance", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/credits**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def top(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Show the users with the most money in the server!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/top**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def shop(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Buy something at the shop!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/shop**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def stats(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Check the statistics of the games you've played", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/stats**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def profile(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="View your profile", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/profile**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def level(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Look at your level and your XP", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/level**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)

	# @help.subcommand()
	# async def freemoney(self, interaction:Interaction):
	# 	embed = nextcord.Embed(color=1768431)
	# 	embed.add_field(name = "Help", value="Look at all the ways to get free money!", inline=False)
	# 	embed.add_field(name = "Usage", value=f"**/freemoney**", inline=False)
	# 	embed.set_footer(text=f"User: {interaction.user}")
	# 	await interaction.send(embed=embed)


def setup(bot):
	bot.add_cog(Others(bot))
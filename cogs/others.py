import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import cooldowns

from random import randint
from PIL import Image
import config, emojis

class Others(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot

	@commands.Cog.listener()
	async def on_guild_join(self, guild):
		ch = self.bot.get_channel(config.channelToNotifyOfServerAddingBot)
		await ch.send(f"Added to {guild.name}")

		channels = guild.text_channels

		general = next((x for x in channels if 'general' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'chat' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'chit' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'lobby' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'talk' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'commands' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'cmd' in x.name.lower()), None)
		if not general: general = next((x for x in channels if 'bot' in x.name.lower()), None)

		if not general:
			return

		if general and (not general.permissions_for(guild.me).send_messages or not general.permissions_for(guild.me).embed_links):
			return
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}")
		embed.add_field(name="Greetings!", value="Type /help to see a list of my commands."
			+ "\n[Click here](https://discord.gg/ggUksVN) to join the support server.")
		await general.send(embed=embed)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild):
		ch = self.bot.get_channel(config.channelToNotifyOfServerAddingBot)
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
		embed = nextcord.Embed(color=1768431)
		if interaction.guild.id != config.adminServerID:
			embed.description = "You must join the support server to use this! The server is listed in /help"
			await interaction.send(embed=embed)
			return
			
		userId = str(interaction.user.id)
		with open("claimed.txt", "r") as claimedFile:
			for line in claimedFile:
				if userId in line:
					embed.description = "You have already claimed your reward!"
					await interaction.send(embed=embed)
					return
		with open("claimed.txt", 'a') as claimedFile:
			claimedFile.write(f"{userId}\n") 
		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, 7500, giveMultiplier=False, activityName="Claim", amntBet=0)

		bal = await self.bot.get_cog("Economy").getBalance(interaction.user)
		embed.description = f"Successfully claimed reward! New balance is {bal:,}{emojis.coin}"
		embed.set_footer(text=f"Log ID: {logID}")
		await interaction.send(embed=embed)


	def GetHelpMsg(self):
		embed = nextcord.Embed(color=1768431, title="Thanks for taking an interest in me!")
		embed.set_footer(text="And that's all for now folks!")

		embed.add_field(name = "BOT HAS SWITCHED TO SLASH COMMANDS", value="Commands start with slash (/). **Below New Commands are WIP**", inline=False)
		
		embed.add_field(name = ":game_die: Game Commands", 
						 value="`roulette`, `crash`, `blackjack`, `horse`, " 
							 + "`slots`, `coinflip`, `rockpaperscissors`, `dond`, `mines`, `scratch`, `rob`, `highlow`", inline = False)
		embed.add_field(name = f"{emojis.bitcoinEmoji} Crypto Commands", 
				  		 value="`crypto buy/sell`, `crypto miner buy/start/stop/status/setcrypto`")

		embed.add_field(name = ":gear: Other Commands",
					   value = "`balance`, `top`, `position`, `shop`, `use`, `stats`, `bank`, "
							 + "`profile`, `level`, `rewards`, `inventory`, `cooldown`, `log`", inline=False)

		embed.add_field(name = ":money_with_wings: Earn Money",
					   value = "`vote`, `work`, `daily`, `weekly`, `monthly`, `search`, `claim`, `beg`, `crime`, `fish`, `dig`", inline=False)

		embed.add_field(name=":grey_question: Quests", value=f"`quests`")

		embed.add_field(name="New commands! :bangbang:", value = "`crypto miner`, `monopoly`, `poker`, `hangman`, `feedback`", inline=False)

		# embed.add_field(name = ":grey_exclamation: Miscellaneous",
		# 				value = f"\n[Join official server](https://discord.gg/ggUksVN) and use `/claim` for free 7,500{emojis.coin}")
						# value = "\n[Support](https://www.paypal.me/AutopilotJustin) gambling bot's development or [join support server](https://discord.gg/ggUksVN).")
		embed.add_field(name = "_ _",
						value = f"[Join official server](https://discord.gg/ggUksVN) and use `/claim` for free 7,500{emojis.coin}\nAdd this bot to your server - [Click Here](https://discord.com/api/oauth2/authorize?client_id=585235000459264005&permissions=387136&scope=bot)\n[Website](https://justingrah.am/) (WIP)\n[Docs](https://docs.justingrah.am/thecasino/) (WIP)", inline=False)
		return embed

	@nextcord.slash_command(description="The Casino Help Command")
	@commands.bot_has_guild_permissions(send_messages=True, embed_links=True, use_external_emojis=True)
	@cooldowns.cooldown(1, 20, bucket=cooldowns.SlashBucket.author, cooldown_id='help')
	async def help(self, interaction:Interaction, 
						option = nextcord.SlashOption(
							required=False,
							name="command", 
							choices=("bank",
									"roulette",
									"crash",
									"crypto",
									"blackjack",
									# "colorguesser",
									"slots",
									"rockpaperscissors",
									"coinflip",
									"dond",
									"mines", 
									"horse",
									"balance", 
									"top", 
									"shop", 
									"stats", 
									"profile", 
									"level",
									"freemoney"
									)
							)
						):
		await interaction.response.defer()

	# async def help(self, interaction:Interaction, option:Optional[str] = nextcord.SlashOption(required=False,
												# name="choice", 
												# choices=("bank", "roulette", "crash", "blackjack", "colorguesser", 
													# "slots", "rockpaperscissors", "coinflip", "credits", "shop", 
													# "stats", "profile", "level", "freemoney"))):

		if not option:
			embed = self.GetHelpMsg()
			await emojis.SendInteractionWithWave(interaction, embed)
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
		# elif option == "colorguesser":
		# 	helpMsg = "Play with friends. Everyone votes for a color the bot will pick."
		# 	usageMsg = "**/colorguesser <bet>**"
		elif option == "slots":
			helpMsg = "Play the slots and try to get the same fruit!"
			usageMsg = "**/slots <bet>**"
		elif option == "rockpaperscissors":
			helpMsg = "Beat the computer in a classic game of Rock-Paper-Scissors"
			usageMsg = "**/rps <rock/paper/scissors> <bet>**"
		elif option == "coinflip":
			helpMsg = "Bet the side the coin will land on"
			usageMsg = "**/coinflip <heads/tails> <bet>**"
		elif option == "crypto":
			helpMsg = "Invest in your favorite crypto. BTC, LTC, and ETH available"
			usageMsg = "**/crypto**"
		elif option == "dond":
			helpMsg = "Play Deal or No Deal!\n**NOTE: This game is a WIP.**"
			usageMsg = "**/dond <bet>**"
		elif option == "mines":
			helpMsg = "Play Roobet Mines! Select number of bombs and try finding spaces that don't have one!\n**NOTE: This game is a WIP.**"
			usageMsg = "**/mines <bet>**"
		elif option == "horse":
			helpMsg = "Horse racing! Bet on the horse you think will win\n**NOTE: This game is a WIP.**"
			usageMsg = "**/horse <bet>**"
		elif option == "balance":
			helpMsg = "Look at your balance"
			usageMsg = "**/balance**"
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
		else:
			embed = self.GetHelpMsg()
			await emojis.SendInteractionWithWave(interaction, embed)
			return

		embed.add_field(name = "Help", value=f"{helpMsg}", inline=False)
		embed.add_field(name = "Usage", value=f"{usageMsg}", inline=False)

		if option == "crash":
			embed.add_field(name = "Chances", value=f"1.0x is 30%\n1.2x is 20%\n1.4x - 1.6x is 30%\n1.6x - 2.4x is 10%\n2.4x - 10.0x is 10%", inline=False)
		embed.set_footer(text=f"User: {interaction.user}")

		await interaction.send(embed=embed)


def setup(bot):
	bot.add_cog(Others(bot))

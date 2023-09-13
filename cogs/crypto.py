import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction

from math import floor, ceil

import cooldowns, requests

import config, emojis
from db import DB

import json

cryptos = ["Bitcoin", "Ethereum", "Litecoin"]

class Crypto(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.bitcoinPrice = -1
		self.bitcoin24hrChange = -1
		self.ethereumPrice = -1
		self.ethereum24hrChange = -1
		self.litecoinPrice = -1
		self.litecoin24hrChange = -1
		self.minAmountToBuy = 0.1
		self.tax = 0.05

	@commands.Cog.listener()
	async def on_ready(self):
		if not self.UpdateCryptoPrices.is_running():
			self.UpdateCryptoPrices.start()

	def cog_unload(self):
		if self.UpdateCryptoPrices.is_running():
			self.UpdateCryptoPrices.cancel()


	cooldowns.define_shared_cooldown(1, 7, cooldowns.SlashBucket.author, cooldown_id="crypto")

	@tasks.loop(minutes=10)
	async def UpdateCryptoPrices(self):
		URL = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?convert=USD&CMC_PRO_API_KEY=' + config.cryptoAPIKey
		response = requests.get(URL)
		data = json.loads(response.text)

		# self.bitcoinPrice = round(data["data"][0]["quote"]["USD"]["price"])
		# self.ethereumPrice = round(data["data"][1]["quote"]["USD"]["price"])
		# self.litecoinPrice = round(data["data"][14]["quote"]["USD"]["price"])
		for crypto in data["data"]:
			if crypto["symbol"] == "BTC":
				self.bitcoinPrice = round(crypto["quote"]["USD"]["price"])
				self.bitcoin24hrChange = round(crypto["quote"]["USD"]["percent_change_24h"], 4)
				continue
			if crypto["symbol"] == "ETH":
				self.ethereumPrice = round(crypto["quote"]["USD"]["price"])
				self.ethereum24hrChange = round(crypto["quote"]["USD"]["percent_change_24h"], 4)
				continue
			if crypto["symbol"] == "LTC":
				self.litecoinPrice = round(crypto["quote"]["USD"]["price"])
				self.litecoin24hrChange = round(crypto["quote"]["USD"]["percent_change_24h"], 4)
				continue
			if self.bitcoinPrice != -1 and self.ethereumPrice != -1 and self.litecoinPrice != -1:
				break

	def GetBalance(self, discordID, crypto):
		balance = DB.fetchOne(f"SELECT Quantity FROM Crypto WHERE DiscordID = ? AND Name = ?;", [discordID, crypto])[0]
		return balance
	
	def GetAllBalances(self, discordID):
		balances = DB.fetchAll(f"SELECT Name, Quantity FROM Crypto WHERE DiscordID = ?;", [discordID])
		return balances


	def AddCrypto(self, discordId, crypto, quantity):
		if quantity > 0:
			DB.insert('INSERT OR IGNORE INTO Crypto(DiscordID, Name, Quantity) VALUES (?, ?, 0);', [discordId, crypto])
		DB.update('UPDATE Crypto SET Quantity = Quantity + ? WHERE DiscordID = ? AND Name = ?;', [quantity, discordId, crypto])
	
	@nextcord.slash_command()
	@cooldowns.shared_cooldown("crypto")
	async def crypto(self, interaction:Interaction):
		pass

	@crypto.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def prices(self, interaction=Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto")
		msg = ""

		if self.bitcoin24hrChange > 0:
			graph = ":chart_with_upwards_trend:"
		else:
			graph = ":chart_with_downwards_trend:"
		msg += f"Bitcoin {emojis.bitcoinEmoji}\n{self.bitcoinPrice:,}{emojis.coin} ({self.bitcoin24hrChange}% {graph})\n\n"
		
		if self.litecoin24hrChange > 0:
			graph = ":chart_with_upwards_trend:"
		else:
			graph = ":chart_with_downwards_trend:"
		msg += f"Litecoin {emojis.litecoinEmoji}\n{self.litecoinPrice:,}{emojis.coin} ({self.litecoin24hrChange}% {graph})\n\n"
		
		if self.ethereum24hrChange > 0:
			graph = ":chart_with_upwards_trend:"
		else:
			graph = ":chart_with_downwards_trend:"
		msg += f"Ethereum {emojis.ethereumEmoji}\n{self.ethereumPrice:,}{emojis.coin} ({self.ethereum24hrChange}% {graph})"

		embed.description = msg

		await interaction.send(embed=embed)


	async def ResetCooldownSendEmbed(self, interaction:Interaction, errorMsg:str, embed:nextcord.Embed):
		cooldowns.reset_bucket(self.crypto.callback, interaction)
		embed.description = errorMsg
		await interaction.send(embed=embed)
	

	@crypto.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def wallet(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto")
		balances = self.GetAllBalances(interaction.user.id)

		if not balances:
			embed.description = "You have no crypto"
			await interaction.send(embed=embed)
			return
		balanceText = ""
		total = 0
		for coin in balances:
			if coin[0] == "Bitcoin":
				coinPrice = self.bitcoinPrice
				emoji = emojis.bitcoinEmoji
			elif coin[0] == "Litecoin":
				coinPrice = self.litecoinPrice
				emoji = emojis.litecoinEmoji
			elif coin[0] == "Ethereum":
				coinPrice = self.ethereumPrice
				emoji = emojis.ethereumEmoji
			
			worth = floor(coin[1] * coinPrice)
			total += worth
			balanceText += f"{coin[1]:,} {emoji} _ _ \t _ _ ({worth:,} {emojis.coin})\n"
		
		embed.description = balanceText
		embed.description += "-----------------------\n"
		embed.description += "**Total**\n"
		embed.description += f"{total:,} {emojis.coin}"
		
		await interaction.send(embed=embed)

	@crypto.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def buy(self, interaction:Interaction, crypto = nextcord.SlashOption(required=True, choices=cryptos), amnt:float=1.0):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto")

		if amnt <= 0:
			await self.ResetCooldownSendEmbed(interaction, "You must enter an amount greater than 0.", embed)
			return

		if amnt < self.minAmountToBuy:
			await self.ResetCooldownSendEmbed(interaction, f"Minimum amount of crypto you're allowed to buy is {self.minAmountToBuy}", embed)
			return
		
		if "." in str(amnt):
			decimalPlaces = len(str(amnt).split(".")[1])
			if decimalPlaces > 1:
				await self.ResetCooldownSendEmbed(interaction, f"You can only use **one** decimal place (ex: 0.5), you used {decimalPlaces}.", embed)
				return
		
		if crypto == "Bitcoin":
			coinPrice = self.bitcoinPrice
			emoji = emojis.bitcoinEmoji
		elif crypto == "Litecoin":
			coinPrice = self.litecoinPrice
			emoji = emojis.litecoinEmoji
		elif crypto == "Ethereum":
			coinPrice = self.ethereumPrice
			emoji = emojis.ethereumEmoji

		
		cost = ceil(amnt * coinPrice)

		balance = await self.bot.get_cog("Economy").getBalance(interaction.user)	
		if balance < cost:
			await self.ResetCooldownSendEmbed(interaction, f"That will cost you {cost:,}{emojis.coin}, but you only have {balance:,}{emojis.coin}", embed)
			return
		
		self.AddCrypto(interaction.user.id, crypto, amnt)
		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, -cost, giveMultiplier=False, activityName=f"Bought {amnt} {crypto}")

		embed.set_footer(text=f"Log ID: {logID}")
		embed.description = f"Purchased {amnt:,} {emoji} for {cost:,} {emojis.coin}"
		await interaction.send(embed=embed)

	@crypto.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def sell(self, interaction:Interaction, crypto=nextcord.SlashOption(required=True, choices=cryptos), amnt:float=1):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto")
		balance = self.GetBalance(interaction.user.id, crypto)

		if amnt <= 0:
			await self.ResetCooldownSendEmbed(interaction, "You must enter an amount greater than 0.", embed)
			return

		if "." in str(amnt):
			decimalPlaces = len(str(amnt).split(".")[1])
			if decimalPlaces > 1:
				await self.ResetCooldownSendEmbed(interaction, f"You can only use **one** decimal place (ex: 0.5), you used {decimalPlaces}.", embed)
				return

		if amnt > balance:
			await self.ResetCooldownSendEmbed(interaction, f"You only have {balance:,} {crypto}, you cannot sell {amnt:,} {crypto}", embed)
			return

		if crypto == "Bitcoin":
			coinPrice = self.bitcoinPrice
			emoji = emojis.bitcoinEmoji
		elif crypto == "Litecoin":
			coinPrice = self.litecoinPrice
			emoji = emojis.litecoinEmoji
		elif crypto == "Ethereum":
			coinPrice = self.ethereumPrice
			emoji = emojis.ethereumEmoji

		creditAmnt = floor(amnt * coinPrice * (1.00-self.tax))

		if amnt == balance:
			DB.delete("DELETE FROM Crypto WHERE DiscordID = ? AND Name = ?", [interaction.user.id, crypto])
		else:
			DB.update("UPDATE Crypto SET Quantity = round(Quantity - ?, 1) WHERE DiscordID = ? AND Name = ?", [amnt, interaction.user.id, crypto])

		logID = await self.bot.get_cog("Economy").addWinnings(interaction.user.id, creditAmnt, giveMultiplier=False, activityName=f"Sold {amnt} {crypto}", amntBet=0)

		embed.description = f"Successfully sold {amnt:,} {emoji} for {creditAmnt:,} {emojis.coin} after a {int(self.tax*100)}% fee"
		embed.set_footer(text=f"Log ID: {logID}")
		await interaction.send(embed=embed)



def setup(bot):
	bot.add_cog(Crypto(bot))
import nextcord
from nextcord.ext import commands, tasks
from nextcord import Interaction

from math import floor, ceil
from random import randrange

import cooldowns, requests, datetime

import config, emojis
from db import DB

import json

cryptos = ["Bitcoin", "Ethereum", "Litecoin"]

miningProcessTimes = list()
for x in range(0, 24):
	# every hour:30, ex 2:30, 3:30, 4:30
	miningProcessTimes.append(datetime.time(hour=x, minute=30, second=0))

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

	@tasks.loop(time=miningProcessTimes)
	async def ProcessCryptoMining():
		# between 150 - 205 an hour
		hourlyAmnt = randrange(150, 205)

		# get crypto value.. delete when ready
		# minedBTCAmnt = hourlyAmnt/self.bitcoinPrice
		# minedLTCAmnt = hourlyAmnt/self.litecoinPrice
		# minedETCAmnt = hourlyAmnt/self.ethereumPrice

		DB.update("""UPDATE CryptoMiner SET CryptoToCollect = CASE
			WHEN CryptoToCollect + ? > Storage THEN Storage
			ELSE CryptoToCollect + ? END 
			WHERE isMining = 1 AND CryptoToCollect < Storage;""", [hourlyAmnt, hourlyAmnt])


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

	def GetBalance(self, discordID, crypto=None):
		if crypto:
			balance = DB.fetchOne(f"SELECT Quantity FROM Crypto WHERE DiscordID = ? AND Name = ?;", [discordID, crypto])
			if not balance:
				return 0
			return balance[0]
		else:
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
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Prices")
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
	async def miner(self, interaction:Interaction):
		pass
	
	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def start(self, interaction:Interaction, id=nextcord.SlashOption(choices = [str(x) for x in range(1, 4)])):
		doesExist = DB.fetchOne("SELECT count(1) FROM CryptoMiner WHERE DiscordID = ? AND ID = ? AND isMining = 1", [interaction.user.id, id])
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Miner | Start")
		if not doesExist:
			embed.description = "Cannot find a miner with that ID that is currently off"
			await interaction.send(embed=embed)
			return

		DB.update("UPDATE CryptoMiner SET isMining = 1 WHERE DiscordID = ? AND ID = ?", [interaction.user.id, id])
		embed.description = f"Successfully started up crypto miner with ID#{id}"

		await interaction.send(embed=embed)

	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def stop(self, interaction:Interaction, id=nextcord.SlashOption(choices = [str(x) for x in range(1, 4)])):
		doesExist = DB.fetchOne("SELECT count(1) FROM CryptoMiner WHERE DiscordID = ? AND ID = ? AND isMining = 0", [interaction.user.id, id])
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Miner | Stop")
		if not doesExist:
			embed.description = "Cannot find a miner with that ID that is currently on"
			await interaction.send(embed=embed)
			return
			
		DB.update("UPDATE CryptoMiner SET isMining = 0 WHERE DiscordID = ? AND ID = ?", [interaction.user.id, id])
		embed.description = f"Successfully stopped with ID#{id}"

		await interaction.send(embed=embed)

	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def upgrade(self, interaction:Interaction, 
				   id = nextcord.SlashOption(choices=[str(x) for x in range(3)]),
				   option = nextcord.SlashOption(
						required=False,
						name="option", 
						choices=("Storage", "Speed"))):

		await interaction.send("Your miner must be turned off before you can upgrade it!")
		return

		# cooler cools down bitcoin miner to prevent overheating
		# power supply makes miner last longer
		# storage increases cap

	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def status(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Miner | Status")
		cryptoMiners = DB.fetchAll("SELECT ID, CryptoName, CryptoToCollect, isMining FROM CryptoMiner WHERE DiscordID = ? ORDER BY ID;", [interaction.user.id])

		if not cryptoMiners:
			embed.description = "You have no crypto miners"
			return

		statusMsg = ""
		for cryptoMiner in cryptoMiners:
			mining = "ON" if cryptoMiner[3] == 1 else "OFF"
			embed.add_field(name=f"Miner #{cryptoMiner[0]} ({mining})", value=f"Mining {cryptoMiner[1]}\n{cryptoMiner[2]} available")

		await interaction.send(embed=embed)

	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def edit(self, interaction:Interaction):
		pass

	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def setcrypto(self, interaction:Interaction, id = nextcord.SlashOption(choices=[str(x) for x in range(1, 4)]), choice=nextcord.SlashOption(choices=(["Bitcoin", "Litecoin", "Ethereum"]))):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Miner | Edit | CryptoCurrency")
		cryptoMiner = DB.fetchOne("SELECT CryptoName, isMining, CryptoToCollect FROM CryptoMiner WHERE DiscordID = ? AND ID = ?;", [interaction.user.id, id])

		if cryptoMiner[1] == 1:
			embed.description = f"You cannot change the crypto miner while it is on. \nPlease first do /miner stop {id} and make sure you withdraw your funds"
			await interaction.send(embed=embed)
			return
		if cryptoMiner[0] == choice:
			embed.description = f"Your bitcoin miner ID#{id} is already mining {choice}. Nothing was changed."
			await interaction.send(embed=embed)
			return
		if cryptoMiner[2] != 0:
			embed.description = f"You cannot change this while you have crypto stored in the miner.\nPlease withdraw it and try again"
			await interaction.send(embed=embed)
			return
		
		DB.update("UPDATE CryptoMiner SET CryptoName = ? WHERE ID = ? AND DiscordID = ?", [choice, id, interaction.user.id])


	@miner.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def withdraw(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Miner | Withdraw")
		balances = DB.fetchAll("SELECT CryptoName, SUM(CryptoToCollect) FROM CryptoMiner WHERE DiscordID = ? AND IsMining = 0 AND CryptoToCollect >= 0.1 GROUP BY CryptoName;", [interaction.user.id])

		if not balances:
			embed.description = "You must have miners, and they must be off for you to withdraw.\nYou must also have at least 0.1 crypto in the miner to withdraw"
			await interaction.send(embed=embed)
			return

		withdrewMsg = "Successfully withdrew:\n"
		for crypto in balances:
			DB.insert('INSERT OR IGNORE INTO Crypto(DiscordID, Name, Quantity) VALUES (?, ?, 0);', [interaction.user.id, crypto[0]])
			DB.update('UPDATE Crypto SET Quantity = ? WHERE DiscordID = ? AND Name = ?', [crypto[1], interaction.user.id, crypto[0]])

			DB.update('UPDATE CryptoMiner SET CryptoToCollect = 0 WHERE DiscordID = ? AND isMining = 0 AND CryptoToCollect >= 0.1', [interaction.user.id])

			if crypto[0] == "Bitcoin":
				emoji = emojis.bitcoinEmoji
			elif crypto[0] == "Litecoin":
				emoji = emojis.litecoinEmoji
			elif crypto[0] == "Ethereum":
				emoji = emojis.ethereumEmoji
			withdrewMsg += f"{crypto[1]} {emoji}\n"

		embed.description = withdrewMsg

		await interaction.send(embed=embed)


	@crypto.subcommand()
	@cooldowns.shared_cooldown("crypto")
	async def wallet(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Wallet")
		balances = self.GetBalance(interaction.user.id)

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
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Buy")

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
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Crypto | Sell")
		balance = self.GetBalance(interaction.user.id, crypto)

		if amnt <= 0:
			await self.ResetCooldownSendEmbed(interaction, "You must enter an amount greater than 0.", embed)
			return
		if balance == 0:
			await self.ResetCooldownSendEmbed(interaction, f"You do not have any {crypto}", embed)
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
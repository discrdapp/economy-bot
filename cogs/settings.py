import nextcord
from nextcord.ext import commands 
from nextcord import Interaction

import asyncio, json, cooldowns
from db import DB

class Settings(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
	
	@nextcord.slash_command(description="Customize your settings for various games")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='settings')
	async def settings(self, interaction:Interaction):
		pass

	@settings.subcommand(description="Do you want to see the generated image when you play Blackjack?")
	async def blackjackimage(self, interaction:Interaction, choice=nextcord.SlashOption(choices = ["on", "off"])):
		if choice == "on":
			DB.delete("DELETE FROM Settings WHERE DiscordID = ? AND Setting = ?;", [interaction.user.id, "ShowBlackjackImg"])
		elif choice == "off":
			DB.insert('INSERT OR IGNORE INTO Settings VALUES (?, ?);', [interaction.user.id, "ShowBlackjackImg"])
		
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}")
		embed.description = "Settings changed successfully!"
		await interaction.send(embed=embed)

	@settings.subcommand(description="Do you want to see the generated image when you play Poker?")
	async def pokerimage(self, interaction:Interaction, choice=nextcord.SlashOption(choices = ["on", "off"])):
		if choice == "on":
			DB.delete("DELETE FROM Settings WHERE DiscordID = ? AND Setting = ?;", [interaction.user.id, "ShowPokerImg"])
		elif choice == "off":
			DB.insert('INSERT OR IGNORE INTO Settings VALUES (?, ?);', [interaction.user.id, "ShowPokerImg"])
		
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name}")
		embed.description = "Settings changed successfully!"
		await interaction.send(embed=embed)
	
def GetUserSetting(userId, settingName:str):
	return DB.fetchOne("SELECT COUNT(1) FROM Settings WHERE DiscordID = ? AND Setting = ?;", [userId, settingName])[0]



def setup(bot):
	bot.add_cog(Settings(bot))
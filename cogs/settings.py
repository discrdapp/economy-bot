import nextcord
from nextcord.ext import commands 
from nextcord import Interaction, Color

import asyncio, json, cooldowns
from db import DB

class Settings(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
	
	async def SendSettingsChangedMsg(self, interaction:Interaction):
		embed = nextcord.Embed(color=Color.green(), title=f"{self.bot.user.name}")
		embed.description = "Settings changed successfully!"
		await interaction.send(embed=embed)

	@nextcord.slash_command(description="Customize your settings for various games")
	@cooldowns.cooldown(1, 5, bucket=cooldowns.SlashBucket.author, cooldown_id='settings')
	async def settings(self, interaction:Interaction):
		pass

	@settings.subcommand(description="Do you want to see the generated image when you play Blackjack?")
	async def showblackjackimage(self, interaction:Interaction, choice=nextcord.SlashOption(choices = ["yes", "no"])):
		if choice == "yes":
			DB.delete("DELETE FROM Settings WHERE DiscordID = ? AND Setting = ?;", [interaction.user.id, "ShowBlackjackImg"])
		elif choice == "no":
			DB.insert('INSERT OR IGNORE INTO Settings VALUES (?, ?);', [interaction.user.id, "ShowBlackjackImg"])
		
		await self.SendSettingsChangedMsg(interaction)

	@settings.subcommand(description="Do you want to see the generated image when you play Poker?")
	async def pokerimage(self, interaction:Interaction, choice=nextcord.SlashOption(choices = ["yes", "no"])):
		if choice == "yes":
			DB.delete("DELETE FROM Settings WHERE DiscordID = ? AND Setting = ?;", [interaction.user.id, "ShowPokerImg"])
		elif choice == "no":
			DB.insert('INSERT OR IGNORE INTO Settings VALUES (?, ?);', [interaction.user.id, "ShowPokerImg"])
		
		await self.SendSettingsChangedMsg(interaction)
	
	@settings.subcommand(description="Do you want to hide the Start button and automatically play?")
	async def hideslotsstartbutton(self, interaction:Interaction, choice=nextcord.SlashOption(choices = ["yes", "no"])):
		if choice == "yes":
			DB.insert('INSERT OR IGNORE INTO Settings VALUES (?, ?);', [interaction.user.id, "HideSlotsStartButton"])
			
		elif choice == "no":
			DB.delete("DELETE FROM Settings WHERE DiscordID = ? AND Setting = ?;", [interaction.user.id, "HideSlotsStartButton"])
		
		await self.SendSettingsChangedMsg(interaction)
	
def GetUserSetting(userId, settingName:str):
	return DB.fetchOne("SELECT COUNT(1) FROM Settings WHERE DiscordID = ? AND Setting = ?;", [userId, settingName])[0]



def setup(bot):
	bot.add_cog(Settings(bot))
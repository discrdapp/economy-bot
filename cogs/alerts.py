import nextcord
from nextcord import Color, Interaction
from nextcord.ext import commands, application_checks

import cooldowns

from datetime import datetime, timedelta

import emojis, config
from db import DB

class AlertHistoryView(nextcord.ui.View):
	def __init__(self, allAlerts):
		super().__init__(timeout=300)
		self.allAlerts = allAlerts
		self.msg = None
		self.add_item(HistoryOptionSelect(self))


class HistoryOptionSelect(nextcord.ui.StringSelect):
	def __init__(self, view):
		self.thisView = view
		self.allAlerts = self.thisView.allAlerts
		super().__init__(options=[nextcord.SelectOption(label=x, value=x) for x in range(1, len(self.allAlerts)+1)])
	
	async def callback(self, interaction:Interaction):
		await interaction.response.defer()

		embed = nextcord.Embed(title=self.allAlerts[int(self.values[0])-1][1])
		embed.description = self.allAlerts[int(self.values[0])-1][2]
		await self.thisView.msg.edit(content=None, embed=embed)
		# self.view.stop()


class NewAlertModal(nextcord.ui.Modal):
	def __init__(self):
		super().__init__(title="New Alert", timeout=300)
		self.add_item(nextcord.ui.TextInput(label="Name"))
		self.add_item(nextcord.ui.TextInput(label="Description", style=nextcord.TextInputStyle.paragraph))
		self.name = ""
		self.desc = ""
	
	async def callback(self, interaction: Interaction):
		self.name = self.children[0].value
		self.desc = self.children[1].value
		await interaction.response.defer()
		self.stop()
	


class Alerts(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
		self.allAlerts = DB.fetchAll("SELECT * FROM Alerts ORDER BY ID DESC;")

		latestAlert = self.allAlerts[0]

		self.latestTimestamp = latestAlert[3]
		latestAlertID = latestAlert[0]
		
		usersWhoViewedAlert = DB.fetchAll("SELECT DiscordID FROM AlertsViewed WHERE AlertID = ?;", [latestAlertID])
		self.usersWhoViewedAlert = [item[0] for item in usersWhoViewedAlert]

		noAlerts = DB.fetchAll("SELECT DiscordID FROM AlertsMuted")
		self.noAlerts = [item[0] for item in noAlerts]

	async def SendAlertNotification(self, interaction:Interaction):
		if str(interaction.user.id) in self.usersWhoViewedAlert:
			return

		if str(interaction.user.id) in self.noAlerts:
			return
		
		timestamp30DayBeforeNow = (datetime.now() - timedelta(days=30)).timestamp()
		if timestamp30DayBeforeNow > self.latestTimestamp:
			return

		embed = nextcord.Embed(color=1768431, title=f"You have an unread Alert!")
		embed.description = "Use </alerts:1219808401597534269> to read it"

		img = nextcord.File("./images/newalert.png", filename="logo.png")
		embed.set_thumbnail(url="attachment://logo.png")

		await interaction.send(embed=embed, ephemeral=True, file=img)
	
	@nextcord.slash_command()
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='alerts')
	async def alerts(self, interaction:Interaction):
		timestamp30DayBeforeNow = (datetime.now() - timedelta(days=30)).timestamp()
		if timestamp30DayBeforeNow > self.latestTimestamp or str(interaction.user.id) in self.usersWhoViewedAlert:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Alerts")
			embed.description = "You do not have any unread alerts"
			await interaction.send(embed=embed, ephemeral=True)
			return
		
		unreadAlerts = DB.fetchAll("""SELECT ID, Title, Description, Reward FROM Alerts
			  		WHERE ID NOT IN (SELECT AlertID FROM AlertsViewed WHERE DiscordID = ?) AND Timestamp > ?;""", [interaction.user.id, timestamp30DayBeforeNow])
		
		if not unreadAlerts:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Alerts")
			embed.description = "You do not have any unread alerts"
			await interaction.send(embed=embed, ephemeral=True)
			return
		
		sendBalMsg = False
		embed = nextcord.Embed()
		for alert in unreadAlerts:
			embed.title = alert[1]
			embed.description = alert[2]
			await interaction.send(embed=embed, ephemeral=True)

			DB.insert("INSERT INTO AlertsViewed VALUES(?, ?);", [alert[0], interaction.user.id])
			self.usersWhoViewedAlert.append(str(interaction.user.id))

			if alert[3] > 0:
				if not sendBalMsg:
					sendBalMsg = True
				await self.bot.get_cog("Economy").addWinnings(interaction.user.id, alert[3], activityName=f"Alert #{alert[0]}", amntBet=0)
		
		if sendBalMsg:
			embed = nextcord.Embed(color=1768431)
			balance = await self.bot.get_cog("Economy").getBalance(interaction.user)
			embed.add_field(name = "Credits", value = f"Your new balance is **{balance:,}**{emojis.coin}", inline=False)

			await interaction.send(embed=embed)

	@nextcord.slash_command(name="alerts-off")
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='alerts-off')
	async def alertsoff(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Alerts")
		if str(interaction.user.id) in self.noAlerts:
			embed.description = "Your alert notifications are already off"
			await interaction.send(embed=embed)
			return
		
		DB.delete("INSERT INTO AlertsMuted VALUES(?);", [interaction.user.id])
		self.noAlerts.append(str(interaction.user.id))

		await interaction.send("Alert notifications have been turned off.\nUse </alerts-on:1218993625615302661> to turn it back on")



	@nextcord.slash_command(name="alerts-on")
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='alerts-on')
	async def alertson(self, interaction:Interaction):
		embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Alerts")
		if str(interaction.user.id) not in self.noAlerts:
			embed.description = "Your alert notifications are already on"
			await interaction.send(embed=embed)
			return	

		DB.delete("DELETE FROM AlertsMuted WHERE DiscordID = ?;", [interaction.user.id])
		self.noAlerts.remove(str(interaction.user.id))

		await interaction.send("Alert notifications have been turned back on.\nUse </alerts-off:1218993624809865276> to turn it back off")


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def refreshalerts(self, interaction:Interaction):
		self.allAlerts = DB.fetchAll("SELECT * FROM Alerts ORDER BY ID DESC;")

		latestAlert = self.allAlerts[0]

		self.latestTimestamp = latestAlert[3]
		latestAlertID = latestAlert[0]
		
		usersWhoViewedAlert = DB.fetchAll("SELECT DiscordID FROM AlertsViewed WHERE AlertID = ?;", [latestAlertID])
		self.usersWhoViewedAlert = [item[0] for item in usersWhoViewedAlert]

		noAlerts = DB.fetchAll("SELECT DiscordID FROM AlertsMuted")
		self.noAlerts = [item[0] for item in noAlerts]

		await interaction.send("Alerts refreshed")


	@nextcord.slash_command(guild_ids=[config.adminServerID])
	@application_checks.is_owner()
	async def newalert(self, interaction:Interaction):
		modal = NewAlertModal()
		
		await interaction.response.send_modal(modal)

		await modal.wait()
		DB.insert("INSERT INTO Alerts(Title, Description, Timestamp) VALUES(?, ?, ?);", [modal.name, modal.desc, datetime.now().timestamp()])

		await self.refreshalerts(interaction)

	@nextcord.slash_command(name="alerts-history")
	@cooldowns.cooldown(1, 3, bucket=cooldowns.SlashBucket.author, cooldown_id='alerts-on')
	async def alerthistory(self, interaction:Interaction):
		if str(interaction.user.id) not in self.usersWhoViewedAlert:
			embed = nextcord.Embed(color=1768431, title=f"{self.bot.user.name} | Alerts")
			embed.description = "You have unread </alerts:1219808401597534269>. You must read those before you can look at the History."
			await interaction.send(embed=embed, ephemeral=True)
			return

		allAlerts = DB.fetchAll("SELECT * FROM Alerts;")

		
		view = AlertHistoryView(allAlerts)

		msg = ""
		for count in range(len(allAlerts)):
			msg += f"{count+1}) {allAlerts[count][1]}\n"
		
		msg = await interaction.send(msg, view=view, ephemeral=True)
		view.msg = msg

def setup(bot):
	bot.add_cog(Alerts(bot))

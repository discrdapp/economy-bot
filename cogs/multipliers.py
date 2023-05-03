import nextcord
from nextcord.ext import commands 

import math, datetime

from db import DB

class Multipliers(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
    

	def convertSecondsToTimeStr(self, seconds):
		timeLeft = ""
		if seconds > 86400: # days
			timeLeft += f"{math.floor(seconds / 86400)} days "
			seconds = seconds % 86400
		if seconds > 3600: # hours
			timeLeft += f"{math.floor(seconds / 3600)} hours "
			seconds = seconds % 3600
		if seconds > 60: # minutes
			timeLeft += f"{math.floor(seconds / 60)} minutes "
			seconds = seconds % 60
		# seconds will now be the left over seconds
		seconds = round(seconds)
		timeLeft += f"{seconds} seconds"

		return timeLeft
	
	def hasMultiplier(self, user):
		expires = DB.fetchOne("SELECT Expires FROM Multipliers WHERE DiscordID = ?;", [user.id])
		if not expires:
			return False
		expireDate = datetime.datetime.strptime(expires, '%Y-%d-%m %H:%M:%S')
		if expireDate < datetime.datetime.now():
			DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [user.id])
			return False
		
		return True
	
	def addMultiplier(self, user, multiplierAmnt:int, expiration:datetime.datetime):
		if self.hasMultiplier(user):
			multiplier, expiration = self.getMultiplierAndExpiration(user)
			if multiplier == multiplierAmnt:
                # extend expiration
				return "Successfully extended multiplier!"
			else:
				return "ERROR: You cannot stack multipliers. You can only extend your current one's time."

		strExpiration = expiration.strftime('%Y-%d-%m %H:%M:%S')
		DB.insert("INSERT INTO Multipliers(DiscordID, Multiplier, Expires) VALUES(?, ?, ?)", [user.id, multiplierAmnt, strExpiration])
		return "Successfully added multiplier!"


	def getMultiplier(self, user):
		multipliers = DB.fetchOne("SELECT Multiplier, Expires FROM Multipliers WHERE DiscordID == ?;", [user.id])
		if not multipliers: 
			return 1.0

		multiplier = multipliers[0]
		expires = multipliers[1]

		expireDate = datetime.datetime.strptime(expires, '%Y-%d-%m %H:%M:%S')
		if expireDate > datetime.datetime.now(): # if multiplier not expired, return it
			return multiplier
		else:
			DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [user.id])

		return 1.0

	def getMultiplierAndExpiration(self, user):
		multipliers = DB.fetchOne("SELECT Multiplier, Expires FROM Multipliers WHERE DiscordID == ?;", [user.id])
		if not multipliers: 
			return 1.0, None

		multiplier = multipliers[0]
		expires = multipliers[1]

		expireDate = datetime.datetime.strptime(expires, '%Y-%d-%m %H:%M:%S')
		if expireDate > datetime.datetime.now():
			print(f"multiplier {multiplier} is of type {type(multiplier)}")
			seconds = (expireDate - datetime.datetime.now()).total_seconds()

			return multiplier, self.convertSecondsToTimeStr(seconds)

		return 1.0, None


def setup(bot):
	bot.add_cog(Multipliers(bot))

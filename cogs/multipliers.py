import nextcord
from nextcord.ext import commands 

import math, datetime

from db import DB

class Multipliers(commands.Cog):
	def __init__(self, bot):
		self.bot:commands.bot.Bot = bot
    

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
	
	def hasMultiplier(self, userId:int):
		expires = DB.fetchOne("SELECT Expires FROM Multipliers WHERE DiscordID = ?;", [userId])
		if not expires:
			return False
		expireDate = datetime.datetime.strptime(expires[0], '%Y-%d-%m %H:%M:%S')
		if expireDate < datetime.datetime.now():
			DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [userId])
			return False
		
		return True
	
	def addMultiplier(self, userId, multiplierAmnt:int, expiration:datetime.datetime):
		if self.hasMultiplier(userId):
			multiplier, currExpiration = self.getMultiplierAndExpiration(userId, False)
			if multiplier == multiplierAmnt:
                # extend expiration
				expirationSecondsLeft = (expiration - datetime.datetime.now()).total_seconds()
				newTime = currExpiration + datetime.timedelta(seconds=expirationSecondsLeft)
				DB.update("UPDATE Multipliers SET Expires = ? WHERE DiscordID = ? and Multiplier = ?;", [newTime.strftime('%Y-%d-%m %H:%M:%S'), userId, multiplierAmnt])
				return "Successfully extended multiplier!"
			else:
				return "ERROR: You cannot stack multipliers. You can only extend your current one's time."

		strExpiration = expiration.strftime('%Y-%d-%m %H:%M:%S')
		DB.insert("INSERT INTO Multipliers(DiscordID, Multiplier, Expires) VALUES(?, ?, ?)", [userId, multiplierAmnt, strExpiration])
		return "Successfully added multiplier!"


	def getMultiplier(self, userId:int):
		multipliers = DB.fetchOne("SELECT Multiplier, Expires FROM Multipliers WHERE DiscordID == ?;", [userId])
		if not multipliers: 
			return 1.0

		multiplier = multipliers[0]
		expires = multipliers[1]

		expireDate = datetime.datetime.strptime(expires, '%Y-%d-%m %H:%M:%S')
		if expireDate > datetime.datetime.now(): # if multiplier not expired, return it
			return multiplier
		else:
			DB.delete("DELETE FROM Multipliers WHERE DiscordID = ?;", [userId])

		return 1.0

	def getMultiplierAndExpiration(self, userId, returnExpirationAsString=True):
		multipliers = DB.fetchOne("SELECT Multiplier, Expires FROM Multipliers WHERE DiscordID == ?;", [userId])
		if not multipliers: 
			return 1.0, None

		multiplier = multipliers[0]
		expires = multipliers[1]

		expireDate = datetime.datetime.strptime(expires, '%Y-%d-%m %H:%M:%S')
		if expireDate > datetime.datetime.now():
			seconds = (expireDate - datetime.datetime.now()).total_seconds()

			if returnExpirationAsString:
				return multiplier, self.convertSecondsToTimeStr(seconds)
			else:
				return multiplier, expireDate

		return 1.0, None


def setup(bot):
	bot.add_cog(Multipliers(bot))

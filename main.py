import discord
from discord.ext import tasks, commands
from datetime import datetime
from pytz import timezone
import asyncio
import json
from keep_alive import keep_alive

TOKEN = ""
CHANNELID = 1234
client = discord.Client()
VALID_GUESSES = [1,2,3,4,5,6,"X"]

#Today's date
tz = timezone('EST')
global today
today = str(datetime.now(tz))[:10]


#Determines if the player is already in the database
def playerInJsonCheck(name, jsonFile):

  for player in jsonFile["players"]:
    if (player["name"] == str(name)):
      return True
  
  return False


#updates database
def loadIntoDatabase(name, guess):
  print("I am in here")
  with open('players.json') as f:
    data = json.load(f)
  
  #converts a fail to 7 tries
  if guess == "X":
    guess = 7
  else:
    guess = int(guess)

  #if the player is already in the database
  if playerInJsonCheck(name, data):
    for player in data["players"]:

      #update their total and times tried
      if player["name"] == str(name):
        player["total"] = int(player["total"]) + guess
        player["timesTried"] = int(player["timesTried"]) + 1
        print(player["name"] + " updated")

  #The players is added to the database
  else:
    print("Adding to database")
    data["players"].append({"name": str(name), "total" : guess, "timesTried" : 1})

  #updates json file
  with open("players.json", 'w') as f:
    json.dump(data, f)
    

#sorts each player in json file based on average score
def sortedInsert(player, list):
  average = int(player["total"]) / int(player["timesTried"])

  #if current player has a lower average, insert 
  for i in range(len(list)):
    if average <= (int(list[i]["total"]) / int(list[i]["timesTried"])):
      list.insert(i, player)
      return list
  
  #current player has the worst score
  list.append(player)
  return list


@tasks.loop(minutes=1)
async def test():
    global today
    
    #checks the current date
    newDate = str(datetime.now(tz))[:10]
    
    #if the current date is different than the recorded date
    if (today != newDate):
        await printResults()

        #change the date
        today = newDate

        #resets database
        with open('players.json') as f:
          data = json.load(f)
          
        del data["currentDay"]
        data["currentDay"] = {"day": 0, "activePlayers": [], "players": {"firstTry": [], "secondTry": [], "thirdTry": [], "fourthTry": [], "fifthTry": [], "sixthTry": [], "fail": []}}
        print("New data:")
        print(data)

        #loads into json file
        with open("players.json", 'w') as f:
          json.dump(data, f)


@client.event
async def printLeaderBoard():
  channel = client.get_channel(CHANNELID)
  currentStandings = []
  lineToPrint = ""
  allLines = "**Current Leaderboard:\n**"

  with open('players.json') as f:
    data = json.load(f)

  #State that there are no participants
  if (len(data["players"]) == 0):
    await channel.send("There are no active participants")
    return 0

  #sorts all players and puts them into currentstandings
  else:
    for player in data["players"]:
      currentStandings = sortedInsert(player, currentStandings)

  for i in range(len(currentStandings)):
    allLines += (str(i + 1) + ") **" + currentStandings[i]["name"][0:-5] + "** with an average of " + str(round(int(currentStandings[i]["total"]) / int(currentStandings[i]["timesTried"]),2)) + " guesses\n")

  await channel.send(allLines)


@client.event
async def printUserAverage(user):
  channel = client.get_channel(CHANNELID)

  with open('players.json') as f:
    data = json.load(f)

  #prints data of user
  if playerInJsonCheck(user, data):
    for player in data["players"]:
      if player["name"] == str(user):
        await channel.send("**" + str(user) + " stats:**\nTotal Score: " + str(player["total"]) + "\nTimes Played: " + str(player["timesTried"]) + "\nAverage Score: " + str(int(player["total"]) / int(player["timesTried"])))

  #if there is no data to be printed
  else:
    await channel.send("You do not have any records to display")


@client.event
async def printResults():
    global today

    with open('players.json') as f:
      data = json.load(f)
    
    channel = client.get_channel(CHANNELID)
    counter = 1
    lineToPrint = ""
    #allows all lines of text to be printed in one message
    allLines = "**" + str(today) + "\nWordle " + str(data["currentDay"]["day"]) + " results:**\n\n"

    for tryList in data["currentDay"]["players"].values():
      if counter == 1:
        lineToPrint += ("**" + str(counter) + " try:** ")
      elif (counter < 7):
        lineToPrint += ("**" + str(counter) + " trys:** ")
      else:
        lineToPrint += ("**Failed:** ")

      for player in tryList:
        lineToPrint += str(player) + " "

      allLines += lineToPrint + "\n"
      lineToPrint = ""
      
      counter += 1
    allLines += "\n\nType !wordlehelp to see all Wordle Bot commands"
    await channel.send(allLines)


#Plays when connected to server
@client.event
async def on_ready():
    channel = client.get_channel(CHANNELID)

    test.start()
    print(f'{client.user} has connected to Discord!')
    #await channel.send("**This is the Wordle bot!** My job is to keep track of each person's daily wordle attempt! Results will be posted every night at midnight. #\n\nTo see the current results, type **!wordleresults**\nTo see your average score, type **!myaverage**\nTo see the leaderboard of each participating player, #type **!leaderboard**\nTo see all commands, type **!wordlehelp**\n\n**Creator:**\nPure#4209\n**Co-Creator**:\nMataFawker#0465")



@client.event
async def on_message(message):
    channel = client.get_channel(CHANNELID)
    messageList = 0

    #Quits the program
    #if (str(message.content).lower() in ["q","quit", "stop"]):
      #print("quitting")
      #quit()

    #prints results
    if (message.content == "!wordleresults"):
      await printResults()
    
    if (message.content == "!myaverage"):
      await printUserAverage(message.author)

    if (message.content == "!leaderboard"):
      await printLeaderBoard()
    
    if (message.content == "!wordlehelp"):
      await channel.send("To see the current results, type **!wordleresults**\nTo see your average score, type **!myaverage**\nTo see the leaderboard of each participating player, type **!leaderboard**\nTo see all commands, type **!wordlehelp**")
        
    #Splits message if sent in wordle-scores chat
    if (message.channel.name == "wordle-scores"):
      messageList = message.content.split()

    #Adds person to dictionary based on how many guesses it took them
    try:
      with open('players.json') as f:
        data = json.load(f)

      if (messageList != 0 and messageList[0] == "Wordle" and message.author.name not in data["currentDay"]["activePlayers"]):
        print("Wordle guess registed for",message.author.name)
        guess = messageList[2][0]
        #Stops player from posting twice in one day
        data["currentDay"]["activePlayers"].append(message.author.name)

        with open("players.json", 'w') as f:
          json.dump(data, f)
        
        if (guess == "X" or int(guess) in [1,2,3,4,5,6]):
          print("I am about to load",message.author.name,"into database")
          loadIntoDatabase(message.author, guess)


        #prints guess amount
        #if (guess == "X"):
          #await channel.send(str(message.author)[0:-5] + " FAILED!\nType !wordleresults to see the current standings!")
        #elif (int(guess) == 1):
          #await channel.send(str(message.author)[0:-5] + " got the word in " + str(guess) + " move!\nType !wordleresults to see the current standings!")
        #elif (int(guess) > 1 and int(guess) < 7):
          #await channel.send(str(message.author)[0:-5] + " got the word in " + str(guess) + " moves!\nType !wordleresults to see the current standings!")
        
        with open('players.json') as f:
          data = json.load(f)

        #changes wordle # to the correct one for the day
        if (int(messageList[1]) != int(data["currentDay"]["day"])):
          print ("Changing day")
          data["currentDay"]["day"] = messageList[1]

        print("guess:",str(guess))
        #Puts user in database depending on their tries
        if (guess == "X"):
          print(str(message.author) + " Failed")
          data["currentDay"]["players"]["fail"].append(message.author.name)
        elif (int(guess) == 1):
          print(str(message.author) + " 1 try")
          data["currentDay"]["players"]["firstTry"].append(message.author.name)
        elif (int(guess) == 2):
          print(str(message.author) + " 2 try")
          data["currentDay"]["players"]["secondTry"].append(message.author.name)
        elif (int(guess) == 3):
          print(str(message.author) + " 3 try")
          data["currentDay"]["players"]["thirdTry"].append(message.author.name)
        elif (int(guess) == 4):
          print(str(message.author) + " 4 try")
          data["currentDay"]["players"]["fourthTry"].append(message.author.name)
        elif (int(guess) == 5):
          print(str(message.author) + " 5 try")
          data["currentDay"]["players"]["fifthTry"].append(message.author.name)
        elif (int(guess) == 6):
          print(str(message.author) + " 6 try")
          data["currentDay"]["players"]["sixthTry"].append(message.author.name)
        
        print(data)
        with open("players.json", 'w') as f:
          json.dump(data, f)
            
    
    #Catches an error if the wordle wasn't shared correctly
    except IndexError:
      print("Not a valid wordle guess")
    except ValueError:
      print("Not a valid guess")

keep_alive()
client.run(TOKEN)

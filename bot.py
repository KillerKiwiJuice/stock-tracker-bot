#Stock tracker bot

import os
#import finnhub
import time
import asyncio
import pprint
from datetime import datetime
import pickle
import discord
from pytz import timezone
from dotenv import load_dotenv
from discord.ext import commands

APIKEY = open("finnkey.txt","r").readline()
#TOKEN = open("bot.txt","r").readline()
TOKEN = os.getenv("SECRET_TOKEN")

#todo
#finnhub_client = finnhub.Client(api_key=APIKEY)
bot = commands.Bot(command_prefix='$')

# Database {}:
#		user ID list {}
#			buy_list {}(temp)
#				ticker {}
#					buy_date
#					price
#			sell_list {}(temp)
#				ticker {}
#					sell_date
#					price
#			gains_list {}
#				wins
#				losses
#				win %
#				total plays
#				biggest win
#				ticker {}
#					buy_date
#					sell_date
#					buy_price
#					sell_price
#					real_percent
#					potential_percent
database={}
leaderboard_winrate={}
leaderboard_totalplays={}
leaderboard_biggestwin={}
leaderboard_biggestloss={}

# define date format
fmt = '%Y-%m-%d %H:%M:%S %Z%z'
# define eastern timezone
eastern = timezone('US/Eastern')

def save_obj(obj, name ):
    with open('obj/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open('obj/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

#load database
database = load_obj('database')
leaderboard_winrate=load_obj('leaderboard_winrate')
leaderboard_totalplays=load_obj('leaderboard_totalplays')
leaderboard_biggestwin=load_obj('leaderboard_biggestwin')
leaderboard_biggestloss=load_obj('leaderboard_biggestloss')

######### debug

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="use command $help"))

#_____________________________________________________________________________________________________________

@bot.command(name='buy')
async def buy(ctx, ticker=None, price=None, date=None):
	if ticker is None:
	    resp = "You must specify a ticker symbol"
	    await ctx.send(resp)
	    return
	elif len(ticker) > 6:
	    resp = "Ticker symbol is not valid"
	    await ctx.send(resp)
	    return

	if price is None:
	    resp = "You must enter a buy price"
	    await ctx.send(resp)
	    return
	elif price == str(0):
	    resp = "Buy price cannot be zero"
	    await ctx.send(resp)
	    return

	if date is None:
		date = datetime.now(eastern)
	else:
		#todo
		date = datetime.now(eastern)

	#validate ticker
	ticker = str.lower(ticker)

	#validate price
	try:
	    number = float(price)
	except ValueError:
	    resp = "I am afraid %s is not a number" % price
	    await ctx.send(resp)
	    return


	#does the user exist in the database?
	if str(ctx.message.author.id) not in database:
		database[str(ctx.message.author.id)] = {}
		database[str(ctx.message.author.id)]['buy_list'] = {}
		#gainslist
		database[str(ctx.message.author.id)]['gains_list'] = {}
		database[str(ctx.message.author.id)]['gains_list']['wins'] = 0
		database[str(ctx.message.author.id)]['gains_list']['losses'] = 0
		database[str(ctx.message.author.id)]['gains_list']['winpercent'] = 0
		database[str(ctx.message.author.id)]['gains_list']['totalplays'] = 0
		database[str(ctx.message.author.id)]['gains_list']['biggestwin'] = 0
		database[str(ctx.message.author.id)]['gains_list']['biggestloss'] = 0
		# add the buy
		database[str(ctx.message.author.id)]['buy_list'][ticker] = {}
		database[str(ctx.message.author.id)]['buy_list'][ticker]['buy_date'] = date
		database[str(ctx.message.author.id)]['buy_list'][ticker]['price'] = price
	else:
		#check if user already called this ticker
		if ticker in database[str(ctx.message.author.id)]["buy_list"]:
			msg = f"{ctx.message.author.display_name} already called {ticker}... if you would like to reset this call, use command `$clear (ticker)`"
			print(msg)
			await ctx.send(msg)
			return
		else:
			# add the buy
			database[str(ctx.message.author.id)]['buy_list'][ticker] = {}
			database[str(ctx.message.author.id)]['buy_list'][ticker]['buy_date'] = date
			database[str(ctx.message.author.id)]['buy_list'][ticker]['price'] = price

	
	save_obj(database,'database')
	# Print message with display name
	response = f"{ctx.message.author.display_name} opened a position in {ticker} at ${price}."
	# Add this buy to the database using discord ID

	await ctx.send(response)

#_____________________________________________________________________________________________________________

@bot.command(name='sell')
async def sell(ctx, ticker=None, price=None, date=None):
	if ticker is None:
	    resp = "You must specify a ticker symbol"
	    await ctx.send(resp)
	    return
	elif len(ticker) > 6:
	    resp = "Ticker symbol is not valid"
	    await ctx.send(resp)
	    return

	if price is None:
	    resp = "You must enter a sell price"
	    await ctx.send(resp)
	    return
	elif price == str(0):
	    resp = "Sell price cannot be zero"
	    await ctx.send(resp)
	    return

	if date is None:
		date = datetime.now(eastern)

	#validate ticker
	ticker = str.lower(ticker)

	#validate price
	try:
	    number = float(price)
	except ValueError:
	    resp = "I am afraid %s is not a number" % price
	    await ctx.send(resp)
	    return

	#does the user exist in the database?
	if (str(ctx.message.author.id) not in database.keys()) or (ticker not in database[str(ctx.message.author.id)]['buy_list'].keys()):
		msg = f"{ctx.message.author.display_name} has either already closed a position on, or not yet bought {ticker}... use `$buy (ticker) (price) (date)` first to start a new call sequence"
		print(msg)
		await ctx.send(msg)
		return
	else:
		# Move ticker to gains list
		# Did the user play this stock before?
		temp = database[str(ctx.message.author.id)]['buy_list'].pop(ticker, None)
		b_date = temp["buy_date"]
		b_price = temp["price"]
		key_name = ticker+" : "+b_date.strftime(fmt)+" - "+date.strftime(fmt)

		# ticker list
		database[str(ctx.message.author.id)]['gains_list'][key_name] = {}
		database[str(ctx.message.author.id)]['gains_list'][key_name]['buy_date'] = b_date
		database[str(ctx.message.author.id)]['gains_list'][key_name]['sell_date'] = date
		database[str(ctx.message.author.id)]['gains_list'][key_name]['buy_price'] = b_price
		database[str(ctx.message.author.id)]['gains_list'][key_name]['sell_price'] = price
		database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent'] = ((float(price) - float(b_price))/float(b_price))*100
		database[str(ctx.message.author.id)]['gains_list'][key_name]['potential_percent'] = "todo"

		# user statistics
		increment = 1 if b_price < price else -1
		prev_high = database[str(ctx.message.author.id)]['gains_list']['biggestwin']
		prev_low = database[str(ctx.message.author.id)]['gains_list']['biggestloss']
		#win
		if increment > 0:
			database[str(ctx.message.author.id)]['gains_list']['wins']+=1
			# new personal record?
			if database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent'] > prev_high:
				database[str(ctx.message.author.id)]['gains_list']['biggestwin'] = database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent']
		#loss
		else:
			database[str(ctx.message.author.id)]['gains_list']['losses']+=1
			# new personal record... fail?
			if database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent'] < prev_low:
				database[str(ctx.message.author.id)]['gains_list']['biggestloss'] = database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent']
		database[str(ctx.message.author.id)]['gains_list']['totalplays']+=1
		database[str(ctx.message.author.id)]['gains_list']['winpercent'] = (database[str(ctx.message.author.id)]['gains_list']['wins'] \
			/ database[str(ctx.message.author.id)]['gains_list']['totalplays'])*100

		#update leaderboards
		leaderboard_winrate[str(ctx.message.author.id)] = database[str(ctx.message.author.id)]['gains_list']['winpercent']
		leaderboard_totalplays[str(ctx.message.author.id)] = database[str(ctx.message.author.id)]['gains_list']['totalplays']
		leaderboard_biggestwin[str(ctx.message.author.id)] = database[str(ctx.message.author.id)]['gains_list']['biggestwin']
		leaderboard_biggestloss[str(ctx.message.author.id)] = database[str(ctx.message.author.id)]['gains_list']['biggestloss']


	save_obj(database,'database')
	save_obj(leaderboard_winrate,'leaderboard_winrate')
	save_obj(leaderboard_totalplays,'leaderboard_totalplays')
	save_obj(leaderboard_biggestwin,'leaderboard_biggestwin')
	save_obj(leaderboard_biggestloss,'leaderboard_biggestloss')
	# Print message with display name
	response = f"{ctx.message.author.display_name} is closing a position on {ticker} at ${price}.\n\
	Buy Date: {b_date.strftime(fmt)}\n\
	Buy Price: {b_price}\n\
	% Change: {str(round(database[str(ctx.message.author.id)]['gains_list'][key_name]['real_percent'], 2))}\n"
	# Add this buy to the database using discord ID

	await ctx.send(response)


#_____________________________________________________________________________________________________________

@bot.command(name='clear')
async def clear(ctx, ticker=None):
	#does the user exist in the database?
	if ticker is None:
	    resp = "You must specify a ticker symbol"
	    await ctx.send(resp)
	    return
	elif len(ticker) > 6:
	    resp = "Ticker symbol is not valid"
	    await ctx.send(resp)
	    return
	if (str(ctx.message.author.id) not in database.keys()) or (ticker not in database[str(ctx.message.author.id)]['buy_list'].keys()):
		msg = f"{ctx.message.author.display_name} has either already closed a position on, or not yet bought {ticker}... use `$buy (ticker) (price) (date)` first to start a new call sequence"
		print(msg)
		await ctx.send(msg)
		return
	else:
		# Remove the position from their buy list
		database[str(ctx.message.author.id)]['buy_list'].pop(ticker, None)


	save_obj(database,'database')
	# Print message with display name
	response = f"{ctx.message.author.display_name} has cleared their position in {ticker}"
	# Add this buy to the database using discord ID

	await ctx.send(response)


@bot.command(name='print')
async def printdata(ctx):
	#only admins can request this data
	if ctx.message.author.guild_permissions.administrator:
		#print(table.__html__())
		output = pprint.pformat(database)
		open('database.txt', 'w').write(output)
		#response = f"{ctx.message.author.display_name} requested a database print."
		await ctx.send(file=discord.File('database.txt'))
	else:
		response = f"{ctx.message.author.display_name} does not have permission to request this data."
		await ctx.send(response)


bot.remove_command("help")
@bot.command(name='help')
async def help(ctx):
	response = "```This bot is a WORK IN PROGRESS!\n-------\nCommands:\
	\n    $buy *ticker* *price* *date=instant* : Open a position in a stock at specified price and date. If no date entered, default is at the time of command sending.\
	\n    $sell *ticker* *price* *date=instant* : Close a position in a stock at specified price and date. If no date entered, default is at the time of command sending.\
	\n    $clear *ticker* : Clear a recent buy from the database ie resets mistakes from previous commands\
	\n    $print : MODERATOR ONLY... Upload the database to the current channel, if you ever needed to do that...\
	\n    $leaderboard *type* *length* : Print a leaderboard of top users. Type can be *winrate*, *biggestwins*, *biggestlosses*. *totalplays*. Length defines how many users to display, maximum 25.\
	\n    $purge-database *type=all* : MODERATOR ONLY... Delete the database or leaderboards. Type can be *all*, *database*, *winrate*, *biggestwins*, *biggestlosses*. *totalplays*. Default type is *all*.\
	\n    $positions *user=you* *length=10* : Request to see a list of *user*'s open positions. Default maximum query is 10 positions.```"
	await ctx.send(response)



@bot.command(name='leaderboard')
async def leaderboard(ctx, type=None, length=10):
	
	if length < 1 or length > 20:
		response = "Enter a length between 1 and 20 (inclusive)."
		await ctx.send(response)
		return
	type_of_print = "Winrate"
	response = \
	f"```\
	********{type_of_print} Leaderboard********\n  \
	"
	if type=="winrate" or type==None:
		sorted(leaderboard_winrate.items(), key=lambda x: x[1], reverse=True)
		type_of_print = "Avg. Winrate"
		for index, user in zip(range(length), leaderboard_winrate):
			member = await ctx.guild.fetch_member(int(user))
			response+=str(index+1)+"    "+str(member.name)+": "+str(round(leaderboard_winrate[user]), 2)+"%\n"

	elif type=="biggestwins":
		sorted(leaderboard_biggestwin.items(), key=lambda x: x[1], reverse=True)
		type_of_print = "Biggest Winners"
		for index, user in zip(range(length), leaderboard_biggestwin):
			member = await ctx.guild.fetch_member(int(user))
			response+=str(index+1)+"    "+str(member.name)+": "+str(round(leaderboard_biggestwin[user]), 2)+"%\n"

	elif type=="biggestlosses":
		sorted(leaderboard_biggestloss.items(), key=lambda x: x[1], reverse=False)
		type_of_print = "Biggest Losers"
		for index, user in zip(range(length), leaderboard_biggestloss):
			member = await ctx.guild.fetch_member(int(user))
			response+=str(index+1)+"    "+str(member.name)+": "+str(round(leaderboard_biggestloss[user]), 2)+"%\n"
	elif type=="totalplays":
		sorted(leaderboard_totalplays.items(), key=lambda x: x[1], reverse=True)
		type_of_print = "Most Plays"
		for index, user in zip(range(length), leaderboard_totalplays):
			member = await ctx.guild.fetch_member(int(user))
			response+=str(index+1)+"    "+str(member.name)+": "+str(leaderboard_totalplays[user])+"\n"
	else:
		response = "Enter a valid type."
		await ctx.send(response)
		return

	
	response += "********************************```"

	await ctx.send(response)



@bot.command(name='purge-database')
async def purge(ctx, type=None):
	#only admins can request this data
	if ctx.message.author.guild_permissions.administrator:
		temp = {}
		if type=="winrate":
			save_obj(temp,leaderboard_winrate)
			leaderboard_winrate={}
		elif type=="database":
			save_obj(temp,database)
			database={}
		elif type=="biggestwins":
			save_obj(temp,leaderboard_biggestwin)
			leaderboard_biggestwin={}
		elif type=="biggestlosses":
			save_obj(temp,leaderboard_biggestloss)
			leaderboard_biggestloss={}
		elif type=="totalplays":
			save_obj(temp,leaderboard_totalplays)
			leaderboard_totalplays={}
		elif type==None:
			save_obj(temp,'database')
			save_obj(temp,'leaderboard_winrate')
			save_obj(temp,'leaderboard_totalplays')
			save_obj(temp,'leaderboard_biggestwin')
			save_obj(temp,'leaderboard_biggestloss')
			leaderboard_winrate={}
			database={}
			leaderboard_biggestwin={}
			leaderboard_biggestloss={}
			leaderboard_totalplays={}
			type="ALL"

		else:
			response = "Enter a valid source name. $help for more info."
			await ctx.send(response)
			return

		response = f"{ctx.message.author.display_name} has purged database {type}."
		await ctx.send(response)
	else:
		response = f"{ctx.message.author.display_name} does not have permission to purge databases."
		await ctx.send(response)


@bot.command(name='positions')
async def positions(ctx, user=None, length=10):
	member=None
	if user==None:
		member = ctx.message.author
	else:
		member = ctx.message.mentions[0]
	response = ""
	#does the user exist in the database?
	if not str(member.id) in database:
		response=f"{member} currently has no open positions."
		await ctx.send(response)
		return
	#does the user have open positions?
	response = ""
	if not database[str(member.id)]['buy_list']:
		response=f"{member} currently has no open positions."
		await ctx.send(response)
		return
	response2=""
	count=0
	for index, ticker in zip(range(length), database[str(member.id)]['buy_list']):
		#print(ticker)
		count=index+1
		datetimeValue = database[str(member.id)]['buy_list'][ticker]['buy_date'].strftime(fmt)
		response2+=datetimeValue+" ::    "+str(ticker).upper()+" - $"+str(database[str(member.id)]['buy_list'][ticker]['price'])+"\n"

	response = f"```{member} currently has {count} open position(s):\n" + response2 + "```"

	#response = f"{ctx.message.author.display_name} does not have permission to purge databases."
	await ctx.send(response)


bot.run(TOKEN)
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import mysql.connector
import pywaves as pw
from waves import generatePhrase
from dbhelper import connectMeToDB
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('\U0001F44D Welcome to Simple WAVES!\n\nSimple WAVES - simple WAVES wallet in Telegram.\n\nUse /help for help')

def wallet(update, context):
	user = update.message.from_user
	id = user.id
	
	mydb = connectMeToDB()	
	
	mycursor = mydb.cursor()

	mycursor.execute("SELECT * FROM wallets where user=" + str(id))
	myresult = mycursor.fetchall()	
	
	message = ""
	
	if len(myresult) == 0:
		message = "no wallet"
		
		seed = generatePhrase()
		myAddress = pw.Address(seed=seed)

		message = myAddress.address

		sql = "INSERT INTO wallets(user, address, privatkey) VALUES(%s, %s, %s)"
		data = (str(id), myAddress.address, myAddress.privateKey)
		mycursor.execute(sql, data)
		mydb.commit()
		
		message = "Congratulations!\nYou get new address\n\n\U0001F194 " + myAddress.address
		
	else:
		data = myresult[0];
		message = "Your address \n\n\U0001F194 " + data[2]
	
	update.message.reply_text(message)
	
	mycursor.close()
	mydb.close()
	
def privatekey(update, context):
	user = update.message.from_user
	id = user.id
	
	mydb = connectMeToDB()	
	
	mycursor = mydb.cursor()

	mycursor.execute("SELECT * FROM wallets where user=" + str(id))
	myresult = mycursor.fetchall()	
	
	message = ""
	
	if len(myresult) == 0:
		
		message = "\U0001F6D1 Use command /wallet to create new address"
		
	else:
		data = myresult[0];
		message = "Your private key is \n\n" + data[3] + "\n\n\U0000203C Keep safe \U0000203C"
	
	update.message.reply_text(message)

	mycursor.close()
	mydb.close()	
	
def balance(update, context):
	
	user = update.message.from_user
	id = user.id
	
	mydb = connectMeToDB()	
	
	mycursor = mydb.cursor()

	mycursor.execute("SELECT * FROM wallets where user=" + str(id))
	myresult = mycursor.fetchall()	
	
	message = ""
		
	if len(myresult) == 0:
		
		message = "\U0001F6D1 Use command /wallet to create new address"
		
	else:
		data = myresult[0];
		privateKey = data[3]
		
		myAddress = pw.Address(privateKey=privateKey)

		message = "\U0001F4B0 Balance is " + str(myAddress.balance()/(100000000)) + " WAVES"
	
	update.message.reply_text(message)

	mycursor.close()
	mydb.close()	

def send(update, context):
	user = update.message.from_user
	id = user.id
	
	mydb = connectMeToDB()	
	
	mycursor = mydb.cursor()

	mycursor.execute("SELECT * FROM wallets where user=" + str(id))
	myresult = mycursor.fetchall()	
	
	message = ""
		
	if len(myresult) == 0:	
		message = "\U0001F6D1 Use command /wallet to create new address"
		update.message.reply_text(message)
		return
		
	if len(context.args) != 2:
		message = "\U0001F6D1 For send WAVES use command \n/send <Address> <Amount>"
		update.message.reply_text(message)
		return
		
	address = context.args[0]
	amount = context.args[1]
	if not pw.validateAddress(address):
		message = "\U0001F6D1 Address is not valid. Please check!"
		update.message.reply_text(message)
		return
	
	amount_f = 0
	
	try:
		amount_f = float(amount)
	except:	
		message = "\U0001F6D1 Valid format for amount is 1 or 1.0"	
		update.message.reply_text(message)	
		return

	error_mess = ""
	real_amount = int(amount_f * (100000000))
	
	#remove all past payments
	sql = "DELETE FROM payments WHERE user = " + str(id)
	mycursor.execute(sql)
	mydb.commit()
	
	# add new payment
	sql = "INSERT INTO payments(user, address, amount) VALUES(%s, %s, %s)"
	data = (str(id), address, real_amount)
	mycursor.execute(sql, data)
	mydb.commit()	
	
	message = "\U0001F195 New transation\n\nRecepient\n\U0001F194 " + address + "\nAmount\n\U0001F4B8 " + str(amount_f) + " WAVES\n\nUse /confirm to send transaction to blockchain."
	update.message.reply_text(message)
		
	mycursor.close()
	mydb.close()		

def confirm(update, context):
	user = update.message.from_user
	id = user.id
	
	mydb = connectMeToDB()	
	
	mycursor = mydb.cursor()

	mycursor.execute("SELECT * FROM payments where user=" + str(id))
	myresult = mycursor.fetchall()	
	
	message = ""
		
	if len(myresult) == 0:	
		message = "\U00002714 All payments was complete!"
		update.message.reply_text(message)
		return
	
	data = myresult[0];
	address = data[2]
	amount = data[3]
	
	mycursor.execute("SELECT * FROM wallets where user=" + str(id))
	myresult = mycursor.fetchall()				
	data = myresult[0];
	privateKey = data[3]	
	myAddress = pw.Address(privateKey=privateKey)	
	
	success = 0
	
	message = "\U000023F3 Trying send WAVES..."
	update.message.reply_text(message)			
	
	try:
		result = myAddress.sendWaves(recipient = pw.Address(address), amount = int(amount))
		message = "\U00002714 Success!\nTX=" + result['id'] + "\ncompleted!"
		update.message.reply_text(message)		
		success = 1
	except Exception as e: 
		update.message.reply_text(str(e))	
	
	#remove all past payments
	if success == 1:	
		sql = "DELETE FROM payments WHERE user = " + str(id)
		mycursor.execute(sql)
		mydb.commit()	
		
	mycursor.close()
	mydb.close()	
	
def echo(update, context):
    update.message.reply_text("Use /help for help")
	
def help(update, context):
	message = "\U00002753 HELP\n\n/wallet - create and get your address\n/privatekey - get your private key\n/balance - get you balance in WAVES\n/send Address Amount - send WAVES to Address"
	update.message.reply_text(message)	

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
	
	# PROXY_SETTING
	#REQUEST_KWARGS={
    #    'proxy_url': 'socks5h://server:port',
    #    # Optional, if you need authentication:
    #    'urllib3_proxy_kwargs': {
    #        'username': 'user',
    #        'password': 'pass',
    #    }
    #}
    #updater = Updater("TOKEN", request_kwargs=REQUEST_KWARGS, use_context=True)
	updater = Updater("TOKEN", use_context=True)
	
	# NODE_SETTING
	#pw.setNode(node = 'https://nodes.wavesnodes.com', chain = 'mainnet')
    pw.setNode(node = 'https://testnode1.wavesnodes.com', chain = 'testnet')
	
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("wallet", wallet))
    dp.add_handler(CommandHandler("privatekey", privatekey))
    dp.add_handler(CommandHandler("balance", balance))
    dp.add_handler(CommandHandler("send", send, pass_args=True))
    dp.add_handler(CommandHandler("confirm", confirm))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(MessageHandler(Filters.text, echo))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
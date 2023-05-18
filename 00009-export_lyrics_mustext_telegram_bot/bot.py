from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters

from bs4 import BeautifulSoup
import urllib.request as r


updater = Updater("5168013826:AAGgnrkchpFVbrJfiJh_niUCYlQQE6Cl7zw",
                  use_context=True)


def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to Appuccino's Official Bot!")


def help(update: Update, context: CallbackContext):
    update.message.reply_text(
        "/channel @Appuccino\n/mustext for find lyrics\n/om old mustext")


def channel_url(update: Update, context: CallbackContext):
    update.message.reply_text("https://t.me/Appuccino")


def find_old_mustext(update: Update, context: CallbackContext):
    the_url = context.args[0]
    page = r.urlopen(the_url)

    page_in_html = page.read().decode('utf8')
    page_in_soup = BeautifulSoup(page_in_html, features="lxml")

    tmp_lyrics = page_in_soup.find_all("p", {"style": "text-align: center;"})

    the_title = str(page_in_soup.find("h2"))
    the_title = the_title.replace('<h2>', '')
    the_title = the_title.replace('</h2>', '')

    new_lines = the_title+":"

    for i in tmp_lyrics:
        tmp_x = str(i)
        tmp_x = tmp_x.replace('<p style="text-align: center;">', '')
        tmp_x = tmp_x.replace('</p>', '')
        new_lines += ("\n"+tmp_x)

    update.message.reply_text(new_lines)


def find_mustext(update: Update, context: CallbackContext):
    the_url = context.args[0]
    page = r.urlopen(the_url)

    page_in_html = page.read().decode('utf8')
    page_in_soup = BeautifulSoup(page_in_html, features="lxml")

    tmp_lyrics = page_in_soup.find("p", {"style": "text-align: center;"})

    the_title = str(page_in_soup.find("h2"))
    the_title = the_title.replace('<h2>', '')
    the_title = the_title.replace('</h2>', '')

    the_lyrics = []

    for i in tmp_lyrics:
        the_lyrics.append(str(i))

    del the_lyrics[0]
    del the_lyrics[-1]

    html_tags = ['<br>', '<br/>', '<strong>', '</strong>']

    new_lines = the_title+":\n"

    for i in the_lyrics:
        tmp_x = i
        for j in html_tags:
            tmp_x = tmp_x.replace(j, '')
        new_lines += tmp_x

    update.message.reply_text(new_lines)


def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry I can't recognize you , you said '%s'" % update.message.text)


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text)


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('mustext', find_mustext))
updater.dispatcher.add_handler(CommandHandler('om', find_old_mustext))
updater.dispatcher.add_handler(CommandHandler('channel', channel_url))
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
updater.dispatcher.add_handler(MessageHandler(
    # Filters out unknown commands
    Filters.command, unknown))

# Filters out unknown messages.
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))

updater.start_polling()
updater.idle()

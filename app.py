#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import telegram
import logging
import re
import configparser

from telegram import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackQueryHandler, BaseFilter
from io import BytesIO
from flask import Flask, request, send_file
from fsm import TocMachine


class FilterGoodnight(BaseFilter):
    def filter(self, message):
        match = re.findall('晚安', message.text)
        return len(match) == 1


class FilterChecknum(BaseFilter):
    def filter(self, message):
        return message.text == '沒關係，但別睡著了呀！'


class FilterCheckpoems(BaseFilter):
    def filter(self, message):
        return message.text == '我有興趣，請通通給我吧。'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

config = configparser.ConfigParser()
config.read('Config.ini')
TELEGRAM_API_TOKEN = config.get('app', 'TELEGRAM_API_TOKEN')
WEBHOOK_URL = config.get('app', 'WEBHOOK_URL') + '/hook'


app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_API_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)
filter_goodnight = FilterGoodnight()
filter_checknum = FilterChecknum()
filter_checkpoems = FilterCheckpoems()
machine = TocMachine(
    states=[
        'user',
        'help',
        'contact',
        'random',
        'goodnight',
        'list',
        'checknum',
        'checkpoems',
        'sendpoems'
    ],
    transitions=[
        {
            'trigger': 'help',
            'source': [
                'user',
                'contact',
                'random',
                'goodnight',
                'list',
                'checknum',
                'sendpoems',
                'checkpoems'
            ],
            'dest': 'help',
        },
        {
            'trigger': 'contact',
            'source': [
                'user',
                'help',
                'random',
                'goodnight',
                'list',
                'checknum',
                'sendpoems',
                'checkpoems'
            ],
            'dest': 'contact',
        },
        {
            'trigger': 'random',
            'source': [
                'user',
                'help',
                'contact',
                'goodnight',
                'list',
                'checknum',
                'sendpoems',
                'checkpoems'
            ],
            'dest': 'random',
        },
        {
            'trigger': 'goodnight',
            'source': [
                'user',
                'help',
                'contact',
                'random',
                'checknum',
                'sendpoems',
                'checkpoems'
            ],
            'dest': 'goodnight',
        },
        {
            'trigger': 'list',
            'source': 'user',
            'dest': 'list',
        },
        {
            'trigger': 'goodnight',
            'source': 'list',
            'dest': 'checknum',
        },
        {
            'trigger': 'checknum',
            'source': 'checknum',
            'dest': 'checkpoems',
        },
        {
            'trigger': 'sendpoems',
            'source': 'checkpoems',
            'dest': 'sendpoems',
        },
        {
            'trigger': 'go_back',
            'source': [
                'help',
                'contact',
                'random',
                'goodnight',
                'list',
                'checknum',
                'sendpoems',
                'checkpoems'
            ],
            'dest': 'user'
        }
    ],
    initial='user',
    auto_transitions=False,
    show_conditions=True,
)


def _setup():
    status = bot.set_webhook(WEBHOOK_URL)
    if not status:
        print('Webhook setup failed')
        sys.exit(1)
    else:
        print('Your webhook URL has been set to "{}"'.format(WEBHOOK_URL))

    start_handler = CommandHandler('start', start)

    help_handler = CommandHandler('help', machine.help)
    contact_handler = CommandHandler('contact', machine.contact)
    random_handler = CommandHandler('random', machine.random)
    list_handler = CommandHandler('list', machine.list)
    checknum_handler = MessageHandler(filter_checknum, machine.checknum)
    sendPoems_photo_handler = MessageHandler(filter_checkpoems, machine.sendpoems)
    goodnight_handler = MessageHandler(filter_goodnight, machine.goodnight)
    goodnight_handler2 = CommandHandler('goodnight', machine.sendpoems)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(contact_handler)
    dispatcher.add_handler(random_handler)
    dispatcher.add_handler(list_handler)
    dispatcher.add_handler(checknum_handler)
    dispatcher.add_handler(sendPoems_photo_handler)
    dispatcher.add_handler(goodnight_handler2)
    dispatcher.add_handler(goodnight_handler)


def start(bot, update):
    custom_keyboard = [[KeyboardButton(text='晚安')]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text('嗨，我是晚安貓，喜歡讀詩的一隻貓🐱', reply_markup=reply_markup)
    update.message.reply_text('睡前和我說一聲晚安，我會很開心得和你分享一首最新的晚安詩呦！')


@app.route('/hook', methods=['POST'])
def webhook_handler():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'


@app.route('/show-fsm', methods=['GET'])
def show_fsm():
    byte_io = BytesIO()
    machine.graph.draw(byte_io, prog='dot', format='png')
    byte_io.seek(0)
    return send_file(byte_io, attachment_filename='fsm.png', mimetype='image/png')


if __name__ == "__main__":
    _setup()
    app.run()
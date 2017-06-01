#!/usr/bin/env python
# -*- coding: utf-8 -*-
import imp
import re
import facebook
import configparser

from transitions.extensions import GraphMachine
from random import randint
from telegram import KeyboardButton, ReplyKeyboardMarkup, ChatAction


class TocMachine(GraphMachine):

    config = configparser.ConfigParser()
    config.read('Config.ini')
    FACEBOOK_TOKEN = config.get('fsm', 'FACEBOOK_TOKEN')

    # facebook id of goodnight poem
    TARGET_FACEBOOK_ID = '177554425767833'

    def __init__(self, **machine_configs):
        self.machine = GraphMachine(
            model=self,
            **machine_configs
        )

    def on_enter_help(self, profile, update):
        update.message.reply_text('和我說「晚安」，讀一首詩給你。')
        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)

        update.message.reply_text('其他功能：\n\t\t1. /random:\t再讀一首不一樣的詩\n\t\t2. /list:\t讀很多首詩\n\t\t3. /contact:\t看看作者的資訊，並留言給作者', reply_markup=reply_markup)
        self.go_back(update)

    def on_enter_contact(self, profile, update):
        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text("想和作者說什麼嗎？")
        update.message.reply_text("傳封訊息吧：https://t.me/ching56", reply_markup=reply_markup)

        self.go_back(update)

    def on_enter_list(self, profile, update):
        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text('想要這麼多詩呀，可以和我說聲晚安嗎？', reply_markup=reply_markup)

    def on_enter_checknum(self, profile, update):
        graph = facebook.GraphAPI(access_token=self.FACEBOOK_TOKEN)
        posts = graph.get_connections(id=self.TARGET_FACEBOOK_ID, connection_name='posts')
        poems = []

        for post in posts['data']:
            if 'message' in post: 
                poems.append(post['message'])

        custom_keyboard = [[KeyboardButton(text='沒關係，但別睡著了呀！')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text('共有'+str(len(poems))+'首詩，等我一下～', reply_markup=reply_markup)


    def on_enter_checkpoems(self, profile, update):
        graph = facebook.GraphAPI(access_token=self.FACEBOOK_TOKEN)
        posts = graph.get_connections(id=self.TARGET_FACEBOOK_ID, connection_name='posts')
        authors = []

        for post in posts['data']:
            if 'message' in post:
                m1 = re.findall('〉，(.*)', post['message'])
                m2 = re.findall('◎(.*)\s', post['message'])
                if m1:
                    authors.append(m1[0])
                elif m2:
                    authors.append(m2[0])

        if len(authors) > 1:
            reply_str = '這裡有:\n'
            for id, author in enumerate(authors):
                reply_str += '\t\t' + str(id+1) + '. ' + author + '\n'
            reply_str += '這些詩人的詩，你全部都要嗎？'
        elif len(authors) == 1:
            reply_str = '這裡有' + authors[0] + '的詩，你有興趣嗎？'
        else:
            reply_str = '哎呀，我好了，你還對詩有興趣嗎？'

        custom_keyboard = [[KeyboardButton(text='我有興趣，請通通給我吧。')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)

        update.message.reply_text(reply_str, reply_markup=reply_markup)

    def on_enter_random(self, profile, update):
        update.message.reply_text('給你一首我喜歡的詩，喵')
        graph = facebook.GraphAPI(access_token=self.FACEBOOK_TOKEN)
        posts = graph.get_connections(id=self.TARGET_FACEBOOK_ID, connection_name='posts')
        poems = []

        for post in posts['data']:
            if 'message' in post: 
                poems.append(post['message'])
        index = randint(0, len(poems) - 1)

        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)     

        update.message.reply_text(poems[index], reply_markup=reply_markup)
        self.go_back(update)

    def on_enter_goodnight(self, profile, update):
        graph = facebook.GraphAPI(access_token=self.FACEBOOK_TOKEN)
        posts = graph.get_connections(id=self.TARGET_FACEBOOK_ID, connection_name='posts')

        # get first poem has poem
        for post in posts['data']:
            if 'message' in post:
                poem = post
                break
        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text(poem['message'])
        update.message.reply_text('睡前讀一首詩吧🐱，晚安', reply_markup=reply_markup)
        self.go_back(update)

    def on_enter_sendpoems(self, profile, update):
        graph = facebook.GraphAPI(access_token=self.FACEBOOK_TOKEN)
        posts = graph.get_connections(id=self.TARGET_FACEBOOK_ID, connection_name='posts')
        post_to_send = []

        for post in posts['data']:
            if 'message' in post:
                update.message.reply_text(post['message'])
        custom_keyboard = [[KeyboardButton(text='晚安')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        update.message.reply_text('讀完這些詩，應該可以安心睡覺了吧，晚安～', reply_markup=reply_markup)
        self.go_back(update)

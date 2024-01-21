import json
import requests
import uuid
import asyncio
import telegram
import logging
import threading
import sqlite3
import random
import unittest
from config import *
from main_database import DataB
from channelDb import ChannelDB
from jobs.daily_messages import DailyMessageJob
from repost_info.info_database import InfoDb
from limits.address_limits import AddressLimits
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from channel_watcher import TelegramChannelWatcher
from config import city_files, city_channels, file_to_channel_id, file_names, api_id, api_hash
from telethon import TelegramClient
from telethon.errors import ChannelPrivateError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import snscrape.modules.telegram as sntelegram
import time
from threading import Thread
from hashlib import md5
import openai
import logging
from other import *
import googleapiclient.discovery
import google.auth.transport.requests
from telegram.error import Unauthorized


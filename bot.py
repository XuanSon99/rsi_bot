from telegram import *
from telegram.ext import *
import requests
import json
from types import SimpleNamespace
import math
import random
import time
from datetime import datetime
import pytz
from dateutil import tz
import pandas as pd
import calendar 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text="kkk", parse_mode=constants.ParseMode.HTML)


async def messageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    print(chat_id)
    # -4018224414

    if "/add" in update.message.text:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        symbol = update.message.text[5:]
        sb = [p for p in data if p['symbol'] == symbol]
        if sb:
            await context.bot.send_message(chat_id=-4018224414, text="Symbol đã tồn tại", parse_mode=constants.ParseMode.HTML)
        else:
            data.append({"symbol": symbol})
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            await context.bot.send_message(chat_id=-4018224414, text="Đã thêm thành công", parse_mode=constants.ParseMode.HTML)

    
    if "/rm" in update.message.text:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        symbol = update.message.text[4:]
        sb = [p for p in data if p['symbol'] == symbol]
        if sb:
            data = [p for p in data if p['symbol'] != symbol]
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            await context.bot.send_message(chat_id=-4018224414, text="Đã xóa thành công", parse_mode=constants.ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=-4018224414, text="Symbol không tồn tại", parse_mode=constants.ParseMode.HTML)
    
    if "/list" in update.message.text:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        text = "<b>Danh Sách Symbol Theo Dõi</b>\n"

        for index, item in enumerate(data):
            text += f"{index+1}. {item['symbol']}\n"

        text += "<i>\n- Thêm symbol: /add BTCUSDT\n- Xóa symbol: /rm BTCUSDT</i>"
        await context.bot.send_message(chat_id=-4018224414, text=text, parse_mode=constants.ParseMode.HTML)

async def callback_minute(context: ContextTypes.DEFAULT_TYPE):

    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        rsi = get_rsi(item['symbol'])
        if rsi > 70:
            text=f"🟢 {item['symbol']} quá mua. RSI: {rsi}"
            await context.bot.send_message(chat_id=-4018224414, text=text, parse_mode=constants.ParseMode.HTML)
        if rsi < 30:
            text=f"🔴 {item['symbol']} quá bán. RSI: {rsi}"
            await context.bot.send_message(chat_id=-4018224414, text=text, parse_mode=constants.ParseMode.HTML)

def get_rsi(symbol):

    timeinterval = 15
    
    now = datetime.utcnow()
    unixtime = calendar.timegm(now.utctimetuple())
    since = unixtime
    start=str(since-60*60*10)    
    
    url = 'https://fapi.binance.com/fapi/v1/klines?symbol='+symbol+'&interval='+str(timeinterval)+'m'+'&limit=100'
    data = requests.get(url).json()        
    
    D = pd.DataFrame(data)
    D.columns = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades',
                 'taker_base_vol', 'taker_quote_vol', 'is_best_match']
    
    period=14
    df=D
    df['close'] = df['close'].astype(float)
    df2=df['close'].to_numpy()
    
    df2 = pd.DataFrame(df2, columns = ['close'])
    delta = df2.diff()
    
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    
    RS = _gain / _loss
    
    rsi=100 - (100 / (1 + RS))  
    rsi=rsi['close'].iloc[-1]
    rsi=round(rsi,1)

    return rsi

app = ApplicationBuilder().token(
    "6673254814:AAHt6zx49L2ARt7Yxr46cyrFF2xJeBpY-gs").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.ALL, messageHandler))

job_queue = app.job_queue

job_minute = job_queue.run_repeating(callback_minute, interval=30, first=1)

app.run_polling()


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, CallbackQueryHandler, Filters,
                         ConversationHandler, MessageHandler)
from google import google
from urllib import request, parse, error
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import logging
import lyricsgenius

genius = lyricsgenius.Genius("")
genius.skip_non_songs = False

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Stages
FIRST, SECOND, SONG, LYRICS = range(4)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
# Variables
artist, song, lyrc = range(3)
data = list(range(1))
        

start_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Start over", callback_data=str(ONE)),
         InlineKeyboardButton("End this", callback_data=str(TWO))]]
    )


# /start + logging
def start(update, context):
    # Grabbing and logging user in terminal
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Generating keyboard
    keyboard = [
        [InlineKeyboardButton("Search lyrics", callback_data=str(ONE)),
         InlineKeyboardButton("Look for a song", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    update.message.reply_text(
        "What should bot do for you?",
        reply_markup=reply_markup
    )
    # Stage `FIRST` to pass to handler
    return FIRST

# Same when if /start, but no new message. 
def start_over(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Search lyrics", callback_data=str(ONE)),
         InlineKeyboardButton("Look for a song", callback_data=str(TWO))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="What should bot do for you?",
        reply_markup=reply_markup
    )
    return FIRST

# Find text (initial)
def one(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Get back", callback_data=str(FOUR))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Type in the author and the name of song which lyrics to search\n\nPlease, stick with Author - Title template",
        reply_markup=reply_markup
    )
    return LYRICS

# Find text (process)
def lyrics(update, context):
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    song_input = str(update.message.text)
    data = song_input.split(' - ')
    artist, song = data[0], data[1]
    try:
        update.message.reply_text(
            text="Okay! Looking for lyrics of\n{} - {}".format(artist, song))

        lyrc = genius.search_song(song, artist)

        genius_markup_2 = InlineKeyboardMarkup([
                [InlineKeyboardButton("Open on Genius.com", 
                    url=lyrc.url)],
                [InlineKeyboardButton("Start over", callback_data=str(ONE)),
                InlineKeyboardButton("End this", callback_data=str(TWO))]
            ])
        if len(lyrc.lyrics) > 4000:
            update.message.reply_text(
                text=lyrc.lyrics[0:4000])
            update.message.reply_text(
                text=lyrc.lyrics[4000:-1]
            )
            update.message.reply_text(
                text="{} is sick \U0001F92A \nLet's find something else or just exit".format(
                        lyrc.title),
                    reply_markup=genius_markup_2)
        else:
            update.message.reply_text(
                text=lyrc.lyrics
            )
            update.message.reply_text(
                text="{} is sick \U0001F92A \nLet's find something else or just exit".format(
                        lyrc.title),
                reply_markup=genius_markup_2)
    except:
        update.message.reply_text(
            text="No such song:\n{} by {}\nTry something different \U0001F928".format(
                song, artist),
            reply_markup=start_markup
        )

    return SECOND
    
# Find song (initial)
def two(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [
        [InlineKeyboardButton("Get back", callback_data=str(FOUR))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Type in some known lines to search for an artist and songname",
        reply_markup=reply_markup
    )
    return SONG

# Find song (process)
def song(update, context):
    try:
        update.message.reply_text(
            text="Okay! Looking for song with\n{}".format(update.message.text))

        new_input = str(update.message.text)+"genius"
        search_results = google.search(new_input, 2)

        some_list = []

        for results in search_results: 
            temp = results.link
            some_list.append(temp)

        if any("genius.com" in s for s in some_list):
            url = ' '.join(map(str, some_list[:1]))

        req = Request(url, headers = { 'User-Agent' : 'Mozilla/5.0' })
        webpage = urlopen(req).read()

        soup = BeautifulSoup(webpage, 'html.parser')
        title = []

        for title in soup.findAll('title'):
            title = title.text.strip()
        
        genius_markup_2 = InlineKeyboardMarkup([
                [InlineKeyboardButton("Open on Genius.com", 
                    url=url)],
                [InlineKeyboardButton("Start over", callback_data=str(ONE)),
                InlineKeyboardButton("End this", callback_data=str(TWO))]
            ])

        update.message.reply_text(
            text="You have been searching for \n{}\n\nThe track is sick \U0001F92A \nYou can easily find something else".format(title.replace(" Lyrics | Genius Lyrics", "")),
            reply_markup=genius_markup_2)
    except:
        update.message.reply_text(
            text="No song was found \U0001F635\nTry something different!",
            reply_markup=start_markup)

    return SECOND


# Show when user ended
def end(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="See you next time!"
    )
    return ConversationHandler.END


# Handler + bot + proxy
def main():
    updater = Updater("", use_context=True,
        request_kwargs={'proxy_url': ''})

    # Handler setup
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [CallbackQueryHandler(one, pattern='^' + str(ONE) + '$'),
                    CallbackQueryHandler(two, pattern='^' + str(TWO) + '$')],
            SONG: [MessageHandler(Filters.text, song),
                   CallbackQueryHandler(start_over, pattern='^' + str(ONE) + '$'),
                   CallbackQueryHandler(end, pattern='^' + str(TWO) + '$')],
            LYRICS: [MessageHandler(Filters.text, lyrics),
                     CallbackQueryHandler(start_over, pattern='^' + str(ONE) + '$'),
                     CallbackQueryHandler(end, pattern='^' + str(TWO) + '$')],
            SECOND: [CallbackQueryHandler(start_over, pattern='^' + str(ONE) + '$'),
                     CallbackQueryHandler(end, pattern='^' + str(TWO) + '$')]
        },
        fallbacks=[CommandHandler('start', start)]
    )

    # updates
    dp.add_handler(conv_handler)

    # logger
    dp.add_error_handler(error)

    # starter
    updater.start_polling()

    # stopper
    updater.idle()


if __name__ == '__main__':
    main()

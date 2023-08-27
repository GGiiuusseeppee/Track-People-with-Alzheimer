from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from wifi import in_out_position
from wifi import learn_inside_locations, train_model, predict
from authentication import authenticate
from gps import retrieve_position
import telegram
Token = '6450165920:AAF0pJ0I4vhDFMMe8yJ4PwcN0G4XlkVC5Kc'
BOT_USERNAME = '@TPWA_bot'

setup = False
train = False
auth = False


# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update.effective_user.id) #update.effective_chat/user.id
    with open("chat_id.txt", 'w') as f:
        f.write(str(update.effective_user.id))
    await update.message.reply_text('Hello, thanks for using our service. '
                                    '\n Now we will configure the service for you\n '
                                    r'First, authenticate your device by using the command /authenticate')


async def authenticate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auth
    auth = True
    await update.message.reply_text('Write the authentication token provided with the device')

async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global setup
    setup = True
    await update.message.reply_text(f'In order to setup the system with the inside locations in your house '
                                    f'move in a room of you house and write the room name in the chat'
                                    r'When you finished with registering all the room use the /position command')
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This are all the commands that you can use...')

async def position_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global train
    global setup
    setup = False

    if not train:
        train_model()
        train = True

    position = in_out_position()
    if position == 'inside':
        pred_position, occupancy = predict()
        await update.message.reply_text('Here the inside position:...\n'
                                        f'{pred_position} \n'
                                        f'Occupancy: {occupancy}')
    if position == 'outside':
        file = retrieve_position()
        await update.message.reply_document(document = file, caption='here the outside position')


# Responses

async def send(chat, msg):
    await telegram.Bot(Token).sendMessage(chat_id=chat, text=msg)
def handle_setup(text: str) -> str:
    processed: str = text.lower()
    learn_inside_locations(processed)


def handle_authentication(text: str) -> str:
    global auth
    processed: str = text.lower()
    while not authenticate(processed):
        continue
    auth = False


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'update' in text:
        return 'Use the Update command'

    if 'position' in text:
        return 'Use the postion command'

    return 'I do not understand what you wrote'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global setup
    global auth
    text: str = update.message.text

    if auth is True:
        handle_authentication(text)
        await update.message.reply_text(r'Correctly Authenticated. Use command /setup to initialize the device')

    if setup is True:
        handle_setup(text)
        print('Bot', 'Move in another place now')
        await update.message.reply_text('Move in another place now or use the command Position')

    #else:
     #   response: str = handle_response(text)
      #  print('Bot', response)
       # await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


if __name__ == '__main__':
    print("Starting bot...")
    app = Application.builder().token(Token).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('authenticate', authenticate_command))
    app.add_handler(CommandHandler('setup', setup_command))
    app.add_handler(CommandHandler('position', position_command))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)
    print('Polling...')
    app.run_polling(poll_interval=3)

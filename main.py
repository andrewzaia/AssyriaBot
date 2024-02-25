import discord
from discord.ext import commands
import os
import requests
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Access the bot token and channel ID from the environment variables
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL'))

# Define the intents with the desired flags
intents = discord.Intents.all()
intents.messages = True # Activate message intents

bot = commands.Bot(command_prefix="!", intents=intents)


async def message_send_verses(ctx, reference, message_verses):
    """
    A function to send Bible verses as messages.
    
    :param ctx: The context in which the message is sent.
    :param reference: The reference of the Bible verse.
    :param message_verses: The verses to be sent as messages.
    """
    await ctx.send(f'**{reference}**')
    for verse in message_verses:
        await ctx.send(f'```{verse}```')


@bot.event
async def on_ready():
    """
    A function that prints the bot's name when it's logged in.
    """
    print(f'Logged in as {bot.user.name}')


@bot.command()
async def bible(ctx, book: str, chapter: str = None, verse: int = None):
    """
    A command that retrieves Bible verses based on user input
    
    :param ctx: The context in which the message is sent.
    :param book: The name of the book in the Bible.
    :param chapter: The chapter number in the book (optional).
    :param verse: The verse number in the chapter (optional).
    """
    if book.lower() == 'random':
        url = f"https://bible-api.com/?random=verse"
    elif verse is None:
        url = f"https://bible-api.com/{book}{chapter}"
    else:
        url = f"https://bible-api.com/{book}{chapter}:{verse}"

    # url += f"?translation=kjv" # Translation is hard set to King James Version
    
    response = requests.get(url)
    print(url)
    data = response.json()

    # Delete user's request
    await ctx.message.delete()

    max_length = 1700

    # User validation to ensure data input entry is correct
    if 'error' in data:
        await ctx.send("Invalid input. Please use the format `!bible Book Chapter:Verse`, e.g., `!bible John 3:16`.")
    else:
        reference = data['reference']
        # await ctx.send(f'**{reference}**')
        
        message_verses = [] # Sets the verses in a list
        current_verse = '' # Clears the current verse to None

        for verse_data in data['verses']:
            # book_name = verse_data['book_name']
            chapter = verse_data['chapter']
            verse = verse_data['verse']
            text = verse_data['text'].replace('\n', '')

            new_verse = f'[{verse}] {text} '.replace('“', '"').replace('”', '"').replace('‘', '\'').replace('’', '\'')
            if len(current_verse) + len(new_verse) > max_length:
                message_verses.append(current_verse)
                current_verse = new_verse
            else:
                current_verse += new_verse
            
        if current_verse:
            message_verses.append(current_verse)

        await message_send_verses(ctx, reference, message_verses)


bot.run(TOKEN)

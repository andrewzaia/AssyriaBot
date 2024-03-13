import asyncio
import configparser
import json
import mysql.connector
import nextcord
import random

from nextcord.ext import commands

# Load the configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Access the bot and database from the configuration file
TOKEN = config.get('Bot', 'TOKEN')
DBA_HOST = config.get('Database', 'DB_HOST')
DBA_USER = config.get('Database', 'DB_USER')
DBA_PASS = config.get('Database', 'DB_PASS')
DBA_NAME = config.get('Database', 'DB_NAME')

# MySQL connection
db = mysql.connector.connect(
    host=DBA_HOST,
    user=DBA_USER,
    password=DBA_PASS,
    database=DBA_NAME
)

# Define the intents with the desired flags
intents = nextcord.Intents.all()
intents.messages = True  # Activate message intents
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Define a global variable to store the room object
game_room = None

# Read characters and their descriptions from the alapbet.json file
async def read_characters_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        characters = json.load(file)
    return characters

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    activity = nextcord.Game(f'Assyrian teacher on {len(bot.guilds)} server(s)')
    await bot.change_presence(status=nextcord.Status.online, activity=activity)

# Function to update user stats and send an update message
async def update_user_stats(user_id, total_attempts, total_score, ctx):
    guild = ctx.guild
    category = nextcord.utils.get(guild.categories, name='lessons')
    room = nextcord.utils.get(guild.channels, name=ctx.user.name, category=category)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM user_stats WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        total_attempts += int(result[4])
        total_score += int(result[5])
        cursor.execute("UPDATE user_stats SET total_attempts = %s, total_score = %s WHERE user_id = %s", (total_attempts, total_score, user_id))
    else:
        cursor.execute("INSERT INTO user_stats (user_id, username, discriminator, total_attempts, total_score) VALUES (%s, %s, %s, %s, %s)", (user_id, ctx.user.name, ctx.user.discriminator, total_attempts, total_score))
    db.commit()
    cursor.close()
    
    # Calculate percentage
    percentage = round((total_score / total_attempts) * 100, 2) if total_attempts > 0 else 0
    
    # Send the user an update on their stats
    stats_message = await game_room.send(f'**{ctx.user.name}**, here\'s an update on your stats:\n'
                                         f'Number of correct answers: {total_score}\n'
                                         f'Number of total attempts: {total_attempts}\n'
                                         f'Percentile: {percentage}%\n\n'
                                         f'Do you want to keep going?')

    # Add reactions for user to continue or stop
    await stats_message.add_reaction('✅')  # Tick
    await stats_message.add_reaction('❌')  # Cross

    # Wait for the user's reaction
    def check(reaction, user):
        return user == ctx.user and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == stats_message.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=10.0, check=check)

        if str(reaction.emoji) == '✅':
            # Start the game
            await start_game(ctx)
        elif str(reaction.emoji) == '❌':
            await room.send("Stopped! Use `/quiz` to continue.")
    except asyncio.TimeoutError:
        await room.send("Stopped! Use `/quiz` to continue.")


@bot.slash_command(description="Start the AlapBet Quiz in your own channel!")
# Function to create a new room under the 'lessons' category with the user's username as the room name
async def quiz(ctx: nextcord.Interaction):
    # Ask the user to choose a difficulty level
    select = nextcord.ui.Select(
        options=[
            nextcord.SelectOption(label="Level 1", description="Beginner Level, Guess the letter!"),
            nextcord.SelectOption(label="Level 2", description="Intermediate Level - Coming Soon!"),
            nextcord.SelectOption(label="Level 3", description="Advanced Level - Coming Soon!")
        ]
    )

    async def select_callback(interaction: nextcord.Interaction):
        # Retrieve the selected level
        game_level = select.values[0]

        # Check the selected level and respond accordingly
        if game_level == "Level 1":
            global game_room

            await ctx.send('Starting up now! Scroll to the bottom of channels (on the left - under "lessons") to find your room.', ephemeral=True, delete_after=30)

            await interaction.response.send_message("You selected Level 1. Starting the quiz...", ephemeral=True, delete_after=30)
            
            guild = ctx.guild
            category = nextcord.utils.get(guild.categories, name='lessons')
            if not category:
                # Create the category if it doesn't exist
                category = await guild.create_category('lessons')

            # Check if the room already exists
            room = nextcord.utils.get(guild.channels, name=ctx.user.name, category=category)
            if not room:
                # Create the room if it doesn't exist
                room = await category.create_text_channel(name=ctx.user.name)

                # Set permissions for the user who created the room
                await room.set_permissions(ctx.user, read_messages=True, send_messages=True)

                await room.set_permissions(bot.user, read_messages=True, send_messages=True)

                # Revoke permissions for @everyone
                await room.set_permissions(guild.default_role, read_messages=False, send_messages=False)

                await room.send(f"Welcome to your lesson room, {ctx.user.name}!")

                print(f'Created room for: {ctx.user.name}')

            # Store the room object in the global variable
            game_room = room

            # Start the game in the room by passing the original message object
            await start_game(ctx)
        elif game_level == "Level 2":
                await interaction.response.send_message("Level 2 is being developed and will be coming soon!", ephemeral=True, delete_after=30)
        elif game_level == "Level 3":
                await interaction.response.send_message("Level 3 is being developed and will be coming soon!", ephemeral=True, delete_after=30)
        else:
            None

    select.callback = select_callback
    view = nextcord.ui.View()
    view.add_item(select)
    await ctx.send("Please choose a difficulty level for the quiz:", view=view, ephemeral=True, delete_after=30)


# Function to start the game
async def start_game(ctx):
    global game_room

    # Load characters from file
    characters = await read_characters_from_file('data/alapbet.json')

    # Pick a random character and get its description
    character = random.choice(characters)
    character_name = character['name']
    character_sound = character['sound']
    character_description = character['description']
    character_image = character['image']

    # Remove the chosen character from the list
    characters.remove(character)

    # Pick two other random characters as choices
    other_characters = random.sample(characters, 2)
    characters.append(character)  # Add the chosen character back to the list

    # Add the choices to the embed
    choices = [character_name] + [other['name'] for other in other_characters]
    random.shuffle(choices)

    # Create an embed with the multiple-choice options
    assyrianFlag = 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Flag_of_the_Assyrians.svg/1280px-Flag_of_the_Assyrians.svg.png'
    embed = nextcord.Embed(
        description=character_description,
        color=0x0099FF
    )
    embed.set_author(name='Alapbet: Level 1', url=character_image, icon_url=assyrianFlag)
    embed.set_thumbnail(url=assyrianFlag)
    embed.add_field(name='**Hint:**', value=f'||{character_name}||', inline=False)
    embed.add_field(name='\u200B', value='\u200B', inline=False)
    embed.add_field(name=f'{choices[0]}', value='1️⃣', inline=True)
    embed.add_field(name=f'{choices[1]}', value='2️⃣', inline=True)
    embed.add_field(name=f'{choices[2]}', value='3️⃣', inline=True)
    embed.set_image(url=character_image)
    embed.set_footer(text='Please choose the correct answer below', icon_url=assyrianFlag)
    embed.timestamp = nextcord.utils.utcnow()

    # Send the embed to the channel
    message_to_edit = await game_room.send(embed=embed)

    # Add reaction emojis for each option
    await message_to_edit.add_reaction('1️⃣')
    await message_to_edit.add_reaction('2️⃣')
    await message_to_edit.add_reaction('3️⃣')

    # Wait for the user's reaction
    def check(reaction, user):
        return user == ctx.user and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣'] and reaction.message.id == message_to_edit.id

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

        # Determine if the user's reaction corresponds to the correct answer
        if str(reaction.emoji) == '1️⃣' and choices[0] == character_name:
            await game_room.send(f'You got it right! The character is {character_name}.')
            # await game_room.send(character_image)
            # Update user's attempts and correct answers in the database
            await update_user_stats(ctx.user.id, 1, 1, ctx)
        elif str(reaction.emoji) == '2️⃣' and choices[1] == character_name:
            await game_room.send(f'You got it right! The character is {character_name}.')
            # await game_room.send(character_image)
            # Update user's attempts and correct answers in the database
            await update_user_stats(ctx.user.id, 1, 1, ctx)
        elif str(reaction.emoji) == '3️⃣' and choices[2] == character_name:
            await game_room.send(f'You got it right! The character is {character_name}.')
            # await game_room.send(character_image)
            # Update user's attempts and correct answers in the database
            await update_user_stats(ctx.user.id, 1, 1, ctx)
        else:
            await game_room.send(f'You got it wrong! The correct answer was {character_name}.')
            # await game_room.send(character_image)
            # Update user's attempts in the database
            await update_user_stats(ctx.user.id, 1, 0, ctx)
    except asyncio.TimeoutError:
        await game_room.send(f'You took too long to answer. The character was {character_name}.')
        # await game_room.send(character_image)
        # Update user's attempts in the database
        await update_user_stats(ctx.user.id, 1, 0, ctx)

# Run the bot
bot.run(TOKEN)

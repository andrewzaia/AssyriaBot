require 'bible_parser'
require 'discordrb'
require 'dotenv/load'
require 'httparty'

# Load the .env file
Dotenv.load

# Access the bot token and channel ID from the environment variables
TOKEN = ENV['BOT_TOKEN']
CHANNEL_ID = ENV['CHANNEL'].to_i
CLIENT_ID = ENV['CLIENT_ID'].to_i

# Define the intents with the desired flags
intents = Discordrb::INTENTS.default

bot = Discordrb::Commands::CommandBot.new token: TOKEN, client_id: CLIENT_ID, prefix: '!', intents: intents

# Create a dictionary
book_indices = {
  "Genesis": 0,
  "Exodus": 1,
  "Leviticus": 2,
  "Numbers": 3,
  "Deuteronomy": 4,
  "Joshua": 5,
  "Judges": 6,
  "Ruth": 7,
  "1 Samuel": 8,
  "2 Samuel": 9,
  "1 Kings": 10,
  "2 Kings": 11,
  "1 Chronicles": 12,
  "2 Chronicles": 13,
  "Ezra": 14,
  "Nehemiah": 15,
  "Esther": 16,
  "Job": 17,
  "Psalms": 18,
  "Proverbs": 19,
  "Ecclesiastes": 20,
  "Song of Solomon": 21,
  "Isaiah": 22,
  "Jeremiah": 23,
  "Lamentations": 24,
  "Ezekiel": 25,
  "Daniel": 26,
  "Hosea": 27,
  "Joel": 28,
  "Amos": 29,
  "Obadiah": 30,
  "Jonah": 31,
  "Micah": 32,
  "Nahum": 33,
  "Habakkuk": 34,
  "Zephaniah": 35,
  "Haggai": 36,
  "Zechariah": 37,
  "Malachi": 38,
  "Tobit": 39,
  "Judith": 40,
  "Esther (Greek)": 41,
  "Wisdom of Solomon": 42,
  "Sirach": 43,
  "Baruch": 44,
  "Jeremy's Letter": 45,
  "3 Holy Children's Song": 46,
  "Susanna": 47,
  "Bel and the Dragon": 48,
  "1 Maccabees": 49,
  "2 Maccabees": 50,
  "1 Esdras": 51,
  "Prayer of Manasses": 52,
  "Psalm 151": 53,
  "3 Maccabees": 54,
  "2 Esdras": 55,
  "4 Maccabees": 56,
  "Matthew": 57,
  "Mark": 58,
  "Luke": 59,
  "John": 60,
  "Acts": 61,
  "Romans": 62,
  "1 Corinthians": 63,
  "2 Corinthians": 64,
  "Galatians": 65,
  "Ephesians": 66,
  "Philippians": 67,
  "Colossians": 68,
  "1 Thessalonians": 69,
  "2 Thessalonians": 70,
  "1 Timothy": 71,
  "2 Timothy": 72,
  "Titus": 73,
  "Philemon": 74,
  "Hebrews": 75,
  "James": 76,
  "1 Peter": 77,
  "2 Peter": 78,
  "1 John": 79,
  "2 John": 80,
  "3 John": 81,
  "Jude": 82,
  "Revelation": 83
}

def message_send_verses(event, reference, message_verses)
  """
  A function to send Bible verses as messages.

  :param event: The event object in which the message is sent.
  :param reference: The reference of the Bible verse.
  :param message_verses: The verses to be sent as messages.
  """
  event.respond("**#{reference}**")
  message_verses.each { |verse| event.respond("```#{verse}```") }
end

bot.message(start_with: '!bible') do |event|
  begin
    bible = BibleParser.new(File.open('eng-web.usfx.xml'))

    user_input = event.content.split('!bible ')[1]

    puts "User input: #{user_input}"

    book_name, chapter_and_verse = user_input.split(' ', 2)
    chapter_number, verse_number = chapter_and_verse.split(':')

    book_index = book_indices[book_name.to_sym]

    # Delete the user's input message
    event.message.delete

    # Set maximum post length. Default: 1700 characters
    max_length = 1700

    message_verses = []
    current_verse = ''

    if book_index.nil?
      event.respond "Book not found in dictionary: #{book_name}"
    else
      chapter_index = chapter_number.to_i - 1
      chapter = bible.books[book_index].chapters[chapter_index]
      if verse_number.nil?
        chapter.verses.each_with_index do |verse, index|
          new_verse = "[#{index + 1}] #{verse.text}".gsub('“', '"').gsub('”', '"').gsub('‘', '\'').gsub('’', '\'')
          if current_verse.length + new_verse.length > max_length
            message_verses << current_verse
            current_verse = new_verse
          else
            current_verse += new_verse
          end
        end

        message_verses << current_verse unless current_verse.empty?

        message_send_verses(event, user_input, message_verses)

      else
        verse = chapter.verses[verse_number.to_i - 1]
        event.respond "** #{user_input}**\n```[#{verse_number.to_i}] #{verse.text}```".gsub('“', '"').gsub('”', '"').gsub('‘', '\'').gsub('’', '\'')
      end
    end

  rescue StandardError => e
    event.respond "An error occurred: #{e.message}"
    event.respond e.backtrace
  end
end

bot.message(start_with: '!assyria') do |event|
  # Delete the user's input message
  event.message.delete

  # Create a new embed object
  embed = Discordrb::Webhooks::Embed.new

  # Set the title and description of the embed
  embed.title = 'Assyrian People'
  embed.description = "Assyrians are an indigenous ethnic group native to Mesopotamia, a geographical region in West Asia. Modern Assyrians descend from Ancient Mesopotamians such as ancient Assyrians and Babylonians, originating from the ancient indigenous Mesopotamians of Akkad and Sumer, who first developed the civilisation in northern Mesopotamia (modern-day Iraq and Syria) that would become Assyria in 2600 BCE. Modern Assyrians may culturally self-identify as Syriacs, Chaldeans, or Arameans for religious, geographic, and tribal identification."

  # Set the image URL
  embed.image = Discordrb::Webhooks::EmbedImage.new(url: 'https://upload.wikimedia.org/wikipedia/commons/6/65/Flag_of_the_Assyrians.jpg')

  # Send the embed post to the channel
  event.channel.send_embed('', embed)
end

bot.run

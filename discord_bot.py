import discord
from discord.ext import commands
import os,sys
import logging
import signal
from dotenv import load_dotenv
from utils.dcdb import *
import importlib
from utils.dcview import *
import time
import  asyncio

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Bot token and debug mode from environment variables
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Create a bot instance with all intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
exit_after_creation = False

command_functions = {}

bot_is_ready = False


# Load command functions from modules in the 'commands' directory
for filename in os.listdir('commands'):
    if filename.endswith('.py'):
        module_name = os.path.basename(filename)[:-3]  # Remove '.py' from the filename
        module = importlib.import_module(f'commands.{module_name}')
        command_functions[module.command_data['name']] = module.execute
        command_functions[module.command_data['name'] + "_discuss"] = module.discuss
        logging.info(f"Loaded command: {module_name}")

async def delete_existing_server():
    for guild in bot.guilds:
        if guild.name == "Discuss with LLM":
            logging.info(f"Deleting existing server: {guild.name} (ID: {guild.id})")
            await guild.delete()
            logging.info("Existing server deleted")
    return

async def create_server_and_channel():
    try:
        # Check if we've already created a server and channel
        if os.getenv('DISCORD_CHANNEL_ID'):
            logging.info("Server and channel already exist. Skipping creation.")
            return None

        os.mkdir("db") 
        creat_db()


        # Create a new guild (server)
        logging.info("Attempting to create a new server...")
        guild = await bot.create_guild(name="Discuss with LLM")
        logging.info(f"Created new server: {guild.name} (ID: {guild.id})")

        # Wait for Discord to process the server creation
        await asyncio.sleep(5)

        # Fetch the guild to ensure it exists
        guild = await bot.fetch_guild(guild.id)

        # Create a text channel
        channel = await guild.create_text_channel(name="llm")
        logging.info(f"Created new channel: {channel.name} (ID: {channel.id})")

        # Save the channel ID to .env file
        with open('.env', 'a') as env_file:
            env_file.write(f"\nDISCORD_CHANNEL_ID={channel.id}")

        # Create an invite link with a timeout
        invite = await channel.create_invite(max_age=3600, max_uses=1)
        logging.info(f"Invite link created: {invite.url}")
        return invite.url

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return None



@bot.event
async def on_ready():
    logging.info(f"Bot is ready as {bot.user}")
      
    


@bot.event
async def on_message(message):

    ignore = True
    if message.content.startswith("."):
        ignore = False
        message.content = message.content[1:]
        logging.info(f"Bot asking: {message.content}")


    if message.content.startswith("bt"):
        await message.channel.send(view=blog_view())
        return

    if message.author.bot and ignore:
        return
   

    channel_id = os.getenv('DISCORD_CHANNEL_ID')
    if str(message.channel.id) == channel_id:
        # Process the message and respond
        # response = f"Received: {message.content}"
        # await message.channel.send(response)
        message.content = "blog " + message.content
    
    if isinstance(message.channel, discord.Thread):
        # Get the thread information from the database
        thread_info = check_thread_in_db(message.channel.id, debug=True)

        if thread_info:
            thread_type, thread_name, user_id, channel_id, message_id, content = thread_info[1:]

            # Send a response to the thread
            if thread_type == 1:
                await command_functions["blog_discuss"](message, thread_name, bot)
            if thread_type == 5:
                logging.info("Just a Ping thread")
            
            return

    command_name = message.content.split(" ")[0]
    if command_name in command_functions:
        logging.info(f"Handle command {command_name}")
        try:
            await command_functions[command_name](message, bot, debug=DEBUG)
        except Exception as e:
            logging.error(f'Error executing command "{command_name}": {str(e)}')

async def setup_and_run():
    try:
        await bot.login(TOKEN)
        if not os.getenv('DISCORD_CHANNEL_ID'):
            invite_link = await create_server_and_channel()
            if invite_link:
                print(f"\nJoin the newly created server using this invite link: {invite_link}")
                print("After joining, please restart the bot.")
            else:
                print("Failed to create server and channel. Please check the logs for more information.")
        
    finally:
        await bot.close()

async def main():
    if not os.getenv('DISCORD_CHANNEL_ID'):
        # If we're creating a new server, set a timeout
        try:
            await asyncio.wait_for(setup_and_run(), timeout=30)
        except asyncio.TimeoutError:
            print("Server creation completed. Please restart the bot after joining the server.")
    else:
        # If the server already exists, run without a timeout
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

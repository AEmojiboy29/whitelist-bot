import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # Import keep_alive for 24/7 hosting

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    print(f'Bot ID: {bot.user.id}')
    print('Bot is ready and running on Render!')

# Event: Monitor messages in specific channel
@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Target channel ID
    TARGET_CHANNEL_ID = 1442227479182835722
    
    # Check if message is in target channel
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()
        
        # Check for "script" keyword
        if 'script' in content_lower:
            embed = discord.Embed(
                title="Script Location",
                description=(
                    f"You can find the script in <#1451252305063182397>!\n\n"
                    f"By clicking the View Script button u will receive ur script\n\n"
                    f"**Note:** Make sure to read <#1365681644568317962> and <#1267755927914680371> before using!"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Triggered by {message.author.display_name}", 
                           icon_url=message.author.avatar.url if message.author.avatar else None)
            await message.channel.send(f"{message.author.mention}", embed=embed)
        
        # Check for "key" keyword
        elif 'key' in content_lower:
            embed = discord.Embed(
                title="Key Location",
                description=f"You can find the key in <#1451252305063182397>!\n\n"
                            f"By clicking the Grab Key button u will receive ur key",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Triggered by {message.author.display_name}", 
                           icon_url=message.author.avatar.url if message.author.avatar else None)
            await message.channel.send(f"{message.author.mention}", embed=embed)
    
    # Process commands
    await bot.process_commands(message)

# Run the bot
if __name__ == "__main__":
    # Start the keep_alive server (for 24/7 uptime on free tier)
    keep_alive()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN not found!")
    else:
        print("Starting bot on Render...")
        bot.run(token)

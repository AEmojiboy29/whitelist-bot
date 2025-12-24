import discord
from discord.ext import commands
import os
import asyncio
import sys
from collections import defaultdict
from datetime import datetime

# Import keep_alive with error handling
try:
    from keep_alive import keep_alive, pinger
    KEEP_ALIVE_AVAILABLE = True
    print("✅ Keep-alive module loaded")
except ImportError as e:
    KEEP_ALIVE_AVAILABLE = False
    print(f"⚠️  Keep-alive not available: {e}")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix=['.', '!'], intents=intents)

# ===== SNIPE STORAGE =====
snipe_storage = defaultdict(list)
MAX_SNIPES = 5  # Maximum number of snipes to store per channel

@bot.event
async def on_ready():
    print('=' * 50)
    print(f'✅ {bot.user} is online!')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📊 Servers: {len(bot.guilds)}')
    
    if KEEP_ALIVE_AVAILABLE:
        print('🌐 Keep-alive: ACTIVE (auto-pinging every 5 min)')
        # Get URL for user reference
        try:
            url = pinger.get_own_url()
            print(f'📡 Bot URL: {url}')
        except:
            pass
    else:
        print('⚠️  Keep-alive: INACTIVE')
    
    print('🎯 Monitoring channel: 1442227479182835722')
    print('=' * 50)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'⚠️  Error syncing commands: {e}')

# ===== SNIPE EVENT LISTENER =====
@bot.event
async def on_message_delete(message):
    """Store deleted messages for sniping"""
    # Ignore bot messages and messages without content
    if message.author.bot or not message.content:
        return
    
    # Store message data
    snipe_data = {
        'content': message.content,
        'author': message.author,
        'timestamp': datetime.utcnow(),
        'attachments': [att.url for att in message.attachments]
    }
    
    # Add to storage and maintain max limit
    snipe_storage[message.channel.id].append(snipe_data)
    if len(snipe_storage[message.channel.id]) > MAX_SNIPES:
        snipe_storage[message.channel.id].pop(0)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    TARGET_CHANNEL_ID = 1442227479182835722
    
    if message.channel.id == TARGET_CHANNEL_ID:
        content_lower = message.content.lower()
        
        if 'script' in content_lower:
            embed = discord.Embed(
                title="📜 Script Location",
                description=(
                    f"You can find the script in <#1451252305063182397>!\n\n"
                    f"By clicking the View Script button u will receive ur script\n\n"
                    f"**📝 Note:** Make sure to read <#1365681644568317962> and <#1267755927914680371> before using!"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Triggered by {message.author.display_name}", 
                           icon_url=message.author.avatar.url if message.author.avatar else None)
            await message.channel.send(f"{message.author.mention}", embed=embed)
            print(f'📨 Responded to script request from {message.author.name}')
        
        elif 'key' in content_lower:
            embed = discord.Embed(
                title="🔑 Key Location",
                description=f"You can find the key in <#1451252305063182397>!\n\n"
                            f"By clicking the Grab Key button u will receive ur key",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Triggered by {message.author.display_name}", 
                           icon_url=message.author.avatar.url if message.author.avatar else None)
            await message.channel.send(f"{message.author.mention}", embed=embed)
            print(f'🔑 Responded to key request from {message.author.name}')
    
    await bot.process_commands(message)

# ===== SNIPE HELPER FUNCTION =====
def create_snipe_embed(snipe_data, index=None):
    """Create an embed for a sniped message"""
    embed = discord.Embed(
        description=snipe_data['content'],
        color=discord.Color.red(),
        timestamp=snipe_data['timestamp']
    )
    embed.set_author(
        name=str(snipe_data['author']),
        icon_url=snipe_data['author'].display_avatar.url
    )
    
    if index is not None:
        embed.set_footer(text=f"Snipe #{index}")
    else:
        embed.set_footer(text="Most recent deleted message")
    
    # Add attachment URLs if any
    if snipe_data['attachments']:
        embed.add_field(
            name="Attachments",
            value='\n'.join(snipe_data['attachments']),
            inline=False
        )
    
    return embed

# ===== SNIPE COMMANDS (most recent) =====
@bot.tree.command(name="s", description="View the most recently deleted message")
async def snipe_slash(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    
    if not snipe_storage[channel_id]:
        await interaction.response.send_message("No deleted messages to snipe!", ephemeral=True)
        return
    
    snipe_data = snipe_storage[channel_id][-1]
    embed = create_snipe_embed(snipe_data)
    await interaction.response.send_message(embed=embed)

@bot.command(name='s')
async def snipe_prefix(ctx):
    """View the most recently deleted message"""
    channel_id = ctx.channel.id
    
    if not snipe_storage[channel_id]:
        await ctx.send("No deleted messages to snipe!")
        return
    
    snipe_data = snipe_storage[channel_id][-1]
    embed = create_snipe_embed(snipe_data)
    await ctx.send(embed=embed)

# ===== CLEAR SNIPE COMMANDS (MANAGE MESSAGES PERMISSION REQUIRED) =====
@bot.tree.command(name="cs", description="Clear all sniped messages in this channel")
async def clear_snipes_slash(interaction: discord.Interaction):
    # Check if user has Manage Messages permission
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ You need **Manage Messages** permission to clear snipes!",
            ephemeral=True
        )
        return
    
    channel_id = interaction.channel_id
    
    if not snipe_storage[channel_id]:
        await interaction.response.send_message("No snipes to clear!", ephemeral=True)
        return
    
    count = len(snipe_storage[channel_id])
    snipe_storage[channel_id].clear()
    await interaction.response.send_message(f"✅ Cleared {count} sniped message(s)!", ephemeral=True)

@bot.command(name='cs')
@commands.has_permissions(manage_messages=True)  # Permission check for prefix command
async def clear_snipes_prefix(ctx):
    """Clear all sniped messages in this channel (Manage Messages permission required)"""
    channel_id = ctx.channel.id
    
    if not snipe_storage[channel_id]:
        await ctx.send("No snipes to clear!")
        return
    
    count = len(snipe_storage[channel_id])
    snipe_storage[channel_id].clear()
    await ctx.send(f"✅ Cleared {count} sniped message(s)!")

# ===== INDIVIDUAL SNIPE VIEWERS =====
async def view_snipe_number(channel_id, number, send_func, user_permissions=None):
    """Helper function to view a specific snipe number"""
    if not snipe_storage[channel_id]:
        await send_func("No deleted messages to snipe!")
        return
    
    snipes = snipe_storage[channel_id]
    
    if number > len(snipes):
        await send_func(f"Only {len(snipes)} snipe(s) available!")
        return
    
    # Get the nth most recent message (1 = most recent)
    index = -number
    snipe_data = snipes[index]
    embed = create_snipe_embed(snipe_data, number)
    await send_func(embed=embed)

# Prefix commands for s1-s5 (anyone can use)
@bot.command(name='s1')
async def s1_prefix(ctx):
    """View the most recent deleted message"""
    await view_snipe_number(ctx.channel.id, 1, ctx.send)

@bot.command(name='s2')
async def s2_prefix(ctx):
    """View the 2nd most recent deleted message"""
    await view_snipe_number(ctx.channel.id, 2, ctx.send)

@bot.command(name='s3')
async def s3_prefix(ctx):
    """View the 3rd most recent deleted message"""
    await view_snipe_number(ctx.channel.id, 3, ctx.send)

@bot.command(name='s4')
async def s4_prefix(ctx):
    """View the 4th most recent deleted message"""
    await view_snipe_number(ctx.channel.id, 4, ctx.send)

@bot.command(name='s5')
async def s5_prefix(ctx):
    """View the 5th most recent deleted message"""
    await view_snipe_number(ctx.channel.id, 5, ctx.send)

# Slash commands for s1-s5 (anyone can use)
@bot.tree.command(name="s1", description="View the most recent deleted message")
async def s1_slash(interaction: discord.Interaction):
    async def send_func(content=None, embed=None):
        if isinstance(content, str):
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(embed=content)
    
    await view_snipe_number(interaction.channel_id, 1, send_func)

@bot.tree.command(name="s2", description="View the 2nd most recent deleted message")
async def s2_slash(interaction: discord.Interaction):
    async def send_func(content=None, embed=None):
        if isinstance(content, str):
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(embed=content)
    
    await view_snipe_number(interaction.channel_id, 2, send_func)

@bot.tree.command(name="s3", description="View the 3rd most recent deleted message")
async def s3_slash(interaction: discord.Interaction):
    async def send_func(content=None, embed=None):
        if isinstance(content, str):
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(embed=content)
    
    await view_snipe_number(interaction.channel_id, 3, send_func)

@bot.tree.command(name="s4", description="View the 4th most recent deleted message")
async def s4_slash(interaction: discord.Interaction):
    async def send_func(content=None, embed=None):
        if isinstance(content, str):
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(embed=content)
    
    await view_snipe_number(interaction.channel_id, 4, send_func)

@bot.tree.command(name="s5", description="View the 5th most recent deleted message")
async def s5_slash(interaction: discord.Interaction):
    async def send_func(content=None, embed=None):
        if isinstance(content, str):
            await interaction.response.send_message(content, ephemeral=True)
        else:
            await interaction.response.send_message(embed=content)
    
    await view_snipe_number(interaction.channel_id, 5, send_func)

# ===== EXISTING BOT COMMANDS =====
@bot.command()
async def status(ctx):
    """Check bot status"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🤖 Bot Status",
        description=f"Online",
        color=discord.Color.green()
    )
    embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
    embed.add_field(name="Uptime", value="Running on Render", inline=True)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def pingtest(ctx):
    """Test the self-pinging system (bot owner only)"""
    if KEEP_ALIVE_AVAILABLE:
        try:
            url = pinger.get_own_url()
            import requests
            response = requests.get(f"{url}/ping", timeout=5)
            
            if response.status_code == 200:
                await ctx.send(f"✅ Self-ping successful!\nURL: {url}\nStatus: {response.status_code}")
            else:
                await ctx.send(f"⚠️  Ping returned status: {response.status_code}")
        except Exception as e:
            await ctx.send(f"❌ Ping test failed: {e}")
    else:
        await ctx.send("❌ Keep-alive system not available")

async def main():
    """Main entry point"""
    print("=" * 50)
    print("🤖 Starting Discord Bot with Self-Pinging Keep-Alive")
    print("=" * 50)
    
    # Start keep-alive system
    if KEEP_ALIVE_AVAILABLE:
        success = keep_alive()
        if success:
            print("✅ Keep-alive system started successfully")
            print("⏰ Bot will auto-ping itself every 5 minutes")
        else:
            print("⚠️  Keep-alive failed to start")
    else:
        print("⚠️  Keep-alive disabled - bot may sleep on free tier")
    
    # Get and validate token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment!")
        print("ℹ️  Set it in Render Dashboard → Environment")
        print("ℹ️  Get token from: https://discord.com/developers/applications")
        return
    
    # Basic token validation
    if len(token) < 50:
        print("❌ Token appears too short - likely invalid")
        print("🔑 Reset token at Discord Developer Portal")
        return
    
    print("✅ Token found, connecting to Discord...")
    
    try:
        await bot.start(token)
    except discord.errors.LoginFailure:
        print("❌ LOGIN FAILED: Invalid token!")
        print("🔑 Reset your token:")
        print("   1. Go to: https://discord.com/developers/applications")
        print("   2. Select your bot → Bot → Reset Token")
        print("   3. Copy NEW token")
        print("   4. Update Render Environment")
        print("   5. Redeploy")
    except Exception as e:
        print(f"❌ Error: {e}")

# Clean shutdown handling
import atexit

def cleanup():
    """Cleanup on exit"""
    if KEEP_ALIVE_AVAILABLE:
        try:
            pinger.stop()
            print("🛑 Self-pinger stopped")
        except:
            pass

atexit.register(cleanup)

if __name__ == "__main__":
    asyncio.run(main())

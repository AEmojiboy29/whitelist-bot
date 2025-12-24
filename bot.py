
import discord
from discord.ext import commands
import os
import asyncio
import sys

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

bot = commands.Bot(command_prefix='!', intents=intents)

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

@bot.command()
async def status(ctx):
    """Check bot status"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🤖 Bot Status",
        description=f"Online and monitoring channel <#{1442227479182835722}>",
        color=discord.Color.green()
    )
    embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
    embed.add_field(name="Uptime", value="Running on Render", inline=True)
    embed.add_field(name="Keep-alive", value="Active (5-min pings)" if KEEP_ALIVE_AVAILABLE else "Inactive", inline=True)
    
    if KEEP_ALIVE_AVAILABLE:
        try:
            url = pinger.get_own_url()
            embed.add_field(name="Bot URL", value=f"[Visit]({url})", inline=False)
        except:
            pass
    
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

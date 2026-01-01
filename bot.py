import discord
from discord.ext import commands
from discord import app_commands
from discord import Activity, ActivityType
import os
import asyncio
import sys
from collections import defaultdict
from datetime import datetime
import json
import atexit 

# Import keep_alive with error handling
try:
    from keep_alive import keep_alive, pinger
    KEEP_ALIVE_AVAILABLE = True
    print("✅ Keep-alive module loaded")
except ImportError as e:
    KEEP_ALIVE_AVAILABLE = False
    print(f"⚠️  Keep-alive not available: {e}")

# ===== PERSISTENT WARNINGS STORAGE =====
WARNINGS_FILE = "warnings.json"

def load_warnings():
    """Load warnings from JSON file"""
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, 'r') as f:
                data = json.load(f)
                
            # Convert string keys back to integers and reconstruct warning objects
            warnings = defaultdict(list)
            for user_id_str, warnings_list in data.items():
                user_id = int(user_id_str)
                for warn in warnings_list:
                    # Reconstruct warning object
                    warning_data = {
                        "reason": warn["reason"],
                        "moderator_id": warn["moderator_id"],
                        "timestamp": datetime.fromisoformat(warn["timestamp"]),
                        "warning_id": warn["warning_id"]
                    }
                    warnings[user_id].append(warning_data)
            return warnings
        except Exception as e:
            print(f"⚠️  Error loading warnings: {e}")
            return defaultdict(list)
    return defaultdict(list)

def save_warnings():
    """Save warnings to JSON file"""
    try:
        # Convert warnings to JSON-serializable format
        data = {}
        for user_id, warnings_list in warnings_storage.items():
            user_warnings = []
            for warn in warnings_list:
                # Convert moderator object to ID, handle both cases
                moderator_id = warn["moderator"].id if hasattr(warn["moderator"], 'id') else warn.get("moderator_id", 0)
                
                user_warnings.append({
                    "reason": warn["reason"],
                    "moderator_id": moderator_id,
                    "timestamp": warn["timestamp"].isoformat(),
                    "warning_id": warn["warning_id"]
                })
            data[str(user_id)] = user_warnings
        
        with open(WARNINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved warnings for {len(data)} users")
    except Exception as e:
        print(f"❌ Error saving warnings: {e}")

def get_member_from_id(guild, member_id):
    """Try to get member object from ID"""
    member = guild.get_member(member_id)
    if member:
        return member
    # If member not found in cache, return a placeholder
    return type('Object', (), {'name': f'User({member_id})', 'id': member_id, 'mention': f'<@{member_id}>'})()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix=['.', '!'], intents=intents)

# ===== SNIPE STORAGE =====
snipe_storage = defaultdict(list)
MAX_SNIPES = 5

# ===== WARNINGS STORAGE =====
warnings_storage = load_warnings()  # Load from file on startup

@bot.event
async def on_ready():
    print('=' * 50)
    print(f'✅ {bot.user} is online!')
    print(f'🆔 Bot ID: {bot.user.id}')
    print(f'📊 Servers: {len(bot.guilds)}')
    await bot.change_presence(
        activity=Activity(
            type=ActivityType.watching,
            name="Void.lua"
        )
    )
    if KEEP_ALIVE_AVAILABLE:
        print('🌐 Keep-alive: ACTIVE (auto-pinging every 5 min)')
        try:
            url = pinger.get_own_url()
            print(f'📡 Bot URL: {url}')
        except:
            pass
    else:
        print('⚠️  Keep-alive: INACTIVE')
    
    print('🎯 Monitoring channel: 1442227479182835722')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'⚠️  Error syncing commands: {e}')
    
    # Load warnings count
    total_warnings = sum(len(warns) for warns in warnings_storage.values())
    print(f'📝 Loaded {total_warnings} warnings for {len(warnings_storage)} users')
    
    # Save warnings every 5 minutes
    bot.loop.create_task(periodic_save())
    
    print('=' * 50)

async def periodic_save():
    """Save warnings to file every 5 minutes"""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300)  # 5 minutes
        save_warnings()
        print("💾 Auto-saved warnings to file")


# script commands
@bot.command(name="script")
async def script_prefix(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    
    message = await ctx.send(
        "**🖥️ PC COPY**\n"
        "```lua\n"
        "loadstring(game:HttpGet(\"https://raw.githubusercontent.com/VoidXZor/AuthLoader/refs/heads/main/VoidLoader\", true))()\n"
        "```\n"
        "**📱 MOBILE COPY**\n"
        "`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/VoidXZor/AuthLoader/refs/heads/main/VoidLoader\", true))()`"
    )
    await message.delete(delay=60)

@bot.tree.command(name="script", description="Get the Void.lua script")
async def script_slash(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**🖥️ PC COPY**\n"
        "```lua\n"
        "loadstring(game:HttpGet(\"https://raw.githubusercontent.com/VoidXZor/AuthLoader/refs/heads/main/VoidLoader\", true))()\n"
        "```\n"
        "**📱 MOBILE COPY**\n"
        "`loadstring(game:HttpGet(\"https://raw.githubusercontent.com/VoidXZor/AuthLoader/refs/heads/main/VoidLoader\", true))()`",
        ephemeral=True
    )

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

# ===== CLEAR SNIPE COMMANDS WITH CLEAN EMBEDS =====
@bot.tree.command(name="cs", description="Clear all sniped messages in this channel")
async def clear_snipes_slash(interaction: discord.Interaction):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to clear snipes!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    channel_id = interaction.channel_id
    
    if not snipe_storage[channel_id]:
        embed = discord.Embed(
            title="📭 No Snipes",
            description="No sniped messages to clear in this channel!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    count = len(snipe_storage[channel_id])
    snipe_storage[channel_id].clear()
    
    # Success embed - clean and simple
    embed = discord.Embed(
        title="✅ Snipes Cleared",
        description=f"Cleared **{count}** sniped message(s) from this channel.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Cleared by {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

@bot.command(name='cs')
@commands.has_permissions(administrator=True)
async def clear_snipes_prefix(ctx):
    """Clear all sniped messages in this channel"""
    channel_id = ctx.channel.id
    
    if not snipe_storage[channel_id]:
        embed = discord.Embed(
            title="📭 No Snipes",
            description="No sniped messages to clear in this channel!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return
    
    count = len(snipe_storage[channel_id])
    snipe_storage[channel_id].clear()
    
    # Success embed - clean and simple
    embed = discord.Embed(
        title="✅ Snipes Cleared",
        description=f"Cleared **{count}** sniped message(s) from this channel.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Cleared by {ctx.author.name}")
    await ctx.send(embed=embed)

# ===== INDIVIDUAL SNIPE VIEWERS =====
async def view_snipe_number(channel_id, number, send_func):
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

# ===== MODERATION COMMANDS (ADMINISTRATOR ONLY) =====
# ===== WARN COMMAND =====
@bot.tree.command(name="warn", description="Warn a user with a reason")
@app_commands.describe(
    user="The user to warn",
    reason="Reason for the warning"
)
async def warn_slash(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to warn users!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot warn self
    if user.id == interaction.user.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot warn yourself!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot warn bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot warn bots!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Add warning to storage
    warning_data = {
        "reason": reason,
        "moderator": interaction.user,
        "timestamp": datetime.utcnow(),
        "warning_id": len(warnings_storage[user.id]) + 1
    }
    warnings_storage[user.id].append(warning_data)
    save_warnings()  # Save immediately
    
    # Send success embed
    embed = discord.Embed(
        title="⚠️ User Warned",
        description=f"{user.mention} has been warned.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Warnings", value=f"Total: **{len(warnings_storage[user.id])}**", inline=True)
    embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
    embed.set_footer(text=f"User ID: {user.id} • Warning #{warning_data['warning_id']}")
    embed.timestamp = datetime.utcnow()
    
    await interaction.response.send_message(embed=embed)
    
    # Try to DM the user (optional)
    try:
        dm_embed = discord.Embed(
            title="⚠️ You have been warned",
            description=f"You received a warning in **{interaction.guild.name}**",
            color=discord.Color.orange()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=interaction.user.name, inline=True)
        dm_embed.add_field(name="Total Warnings", value=str(len(warnings_storage[user.id])), inline=True)
        dm_embed.set_footer(text="Please follow the server rules")
        await user.send(embed=dm_embed)
    except:
        pass  # User has DMs disabled

@bot.command(name='warn')
@commands.has_permissions(administrator=True)
async def warn_prefix(ctx, user: discord.Member, *, reason="No reason provided"):
    """Warn a user with a reason (Administrator only)"""
    # Cannot warn self
    if user.id == ctx.author.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot warn yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Cannot warn bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot warn bots!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Add warning to storage
    warning_data = {
        "reason": reason,
        "moderator": ctx.author,
        "timestamp": datetime.utcnow(),
        "warning_id": len(warnings_storage[user.id]) + 1
    }
    warnings_storage[user.id].append(warning_data)
    save_warnings()  # Save immediately
    
    # Send success embed
    embed = discord.Embed(
        title="⚠️ User Warned",
        description=f"{user.mention} has been warned.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Warnings", value=f"Total: **{len(warnings_storage[user.id])}**", inline=True)
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    embed.set_footer(text=f"User ID: {user.id} • Warning #{warning_data['warning_id']}")
    embed.timestamp = datetime.utcnow()
    
    await ctx.send(embed=embed)
    
    # Try to DM the user (optional)
    try:
        dm_embed = discord.Embed(
            title="⚠️ You have been warned",
            description=f"You received a warning in **{ctx.guild.name}**",
            color=discord.Color.orange()
        )
        dm_embed.add_field(name="Reason", value=reason, inline=False)
        dm_embed.add_field(name="Moderator", value=ctx.author.name, inline=True)
        dm_embed.add_field(name="Total Warnings", value=str(len(warnings_storage[user.id])), inline=True)
        dm_embed.set_footer(text="Please follow the server rules")
        await user.send(embed=dm_embed)
    except:
        pass

# ===== BAN COMMAND =====
@bot.tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(
    user="The user to ban",
    reason="Reason for the ban",
    delete_days="Number of days of messages to delete (0-7)"
)
@app_commands.choices(delete_days=[
    app_commands.Choice(name="0 days (no messages)", value=0),
    app_commands.Choice(name="1 day", value=1),
    app_commands.Choice(name="2 days", value=2),
    app_commands.Choice(name="3 days", value=3),
    app_commands.Choice(name="7 days", value=7)
])
async def ban_slash(interaction: discord.Interaction, user: discord.Member, 
                   reason: str = "No reason provided", delete_days: int = 0):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to ban users!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot ban self
    if user.id == interaction.user.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot ban yourself!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot ban bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot ban bots!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if target has higher permissions
    if user.top_role >= interaction.user.top_role:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="You cannot ban someone with equal or higher permissions!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Ban the user
    try:
        await user.ban(reason=f"{reason} (Banned by {interaction.user})", delete_message_days=delete_days)
        
        # Send success embed
        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"{user.mention} has been banned from the server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Messages Deleted", value=f"Last {delete_days} day(s)", inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to ban this user!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to ban user: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name='ban')
@commands.has_permissions(administrator=True)
async def ban_prefix(ctx, user: discord.Member, delete_days: int = 0, *, reason="No reason provided"):
    """Ban a user from the server (Administrator only)"""
    # Cannot ban self
    if user.id == ctx.author.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot ban yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Cannot ban bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot ban bots!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Check if target has higher permissions
    if user.top_role >= ctx.author.top_role:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="You cannot ban someone with equal or higher permissions!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Ban the user
    try:
        await user.ban(reason=f"{reason} (Banned by {ctx.author})", delete_message_days=delete_days)
        
        # Send success embed
        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"{user.mention} has been banned from the server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Messages Deleted", value=f"Last {delete_days} day(s)", inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to ban this user!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to ban user: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ===== KICK COMMAND =====
@bot.tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(
    user="The user to kick",
    reason="Reason for the kick"
)
async def kick_slash(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to kick users!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot kick self
    if user.id == interaction.user.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot kick yourself!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Cannot kick bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot kick bots!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if target has higher permissions
    if user.top_role >= interaction.user.top_role:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="You cannot kick someone with equal or higher permissions!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Kick the user
    try:
        await user.kick(reason=f"{reason} (Kicked by {interaction.user})")
        
        # Send success embed
        embed = discord.Embed(
            title="👢 User Kicked",
            description=f"{user.mention} has been kicked from the server.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed)
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to kick this user!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to kick user: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name='kick')
@commands.has_permissions(administrator=True)
async def kick_prefix(ctx, user: discord.Member, *, reason="No reason provided"):
    """Kick a user from the server (Administrator only)"""
    # Cannot kick self
    if user.id == ctx.author.id:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot kick yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Cannot kick bots
    if user.bot:
        embed = discord.Embed(
            title="❌ Invalid Target",
            description="You cannot kick bots!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Check if target has higher permissions
    if user.top_role >= ctx.author.top_role:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="You cannot kick someone with equal or higher permissions!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Kick the user
    try:
        await user.kick(reason=f"{reason} (Kicked by {ctx.author})")
        
        # Send success embed
        embed = discord.Embed(
            title="👢 User Kicked",
            description=f"{user.mention} has been kicked from the server.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"User ID: {user.id}")
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Permission Error",
            description="I don't have permission to kick this user!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to kick user: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ===== WARNS COMMAND =====
@bot.tree.command(name="warns", description="View warnings for a user")
@app_commands.describe(
    user="The user to check warnings for"
)
async def warns_slash(interaction: discord.Interaction, user: discord.Member):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to view warnings!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    user_warnings = warnings_storage[user.id]
    
    if not user_warnings:
        embed = discord.Embed(
            title="📋 User Warnings",
            description=f"{user.mention} has **no warnings**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"User ID: {user.id}")
        await interaction.response.send_message(embed=embed)
        return
    
    # Create paginated embed for warnings
    warnings_text = ""
    for i, warning in enumerate(user_warnings, 1):
        # Handle moderator (could be ID or object)
        if hasattr(warning['moderator'], 'name'):
            moderator_name = warning['moderator'].name
            moderator_mention = warning['moderator'].mention
        else:
            # Try to get member from ID
            moderator_obj = get_member_from_id(interaction.guild, warning.get('moderator_id', 0))
            moderator_name = moderator_obj.name
            moderator_mention = moderator_obj.mention
        
        time_ago = (datetime.utcnow() - warning['timestamp']).days
        warnings_text += f"**#{i}** - {time_ago} day(s) ago\n"
        warnings_text += f"**Reason:** {warning['reason']}\n"
        warnings_text += f"**By:** {moderator_mention}\n"
        warnings_text += f"**Date:** {warning['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n"
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {user.name}",
        description=f"**Total Warnings:** {len(user_warnings)}\n\n{warnings_text}",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"User ID: {user.id} • Requested by {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)

@bot.command(name='warns')
@commands.has_permissions(administrator=True)
async def warns_prefix(ctx, user: discord.Member):
    """View warnings for a user (Administrator only)"""
    user_warnings = warnings_storage[user.id]
    
    if not user_warnings:
        embed = discord.Embed(
            title="📋 User Warnings",
            description=f"{user.mention} has **no warnings**.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"User ID: {user.id}")
        await ctx.send(embed=embed)
        return
    
    # Create paginated embed for warnings
    warnings_text = ""
    for i, warning in enumerate(user_warnings, 1):
        # Handle moderator (could be ID or object)
        if hasattr(warning['moderator'], 'name'):
            moderator_name = warning['moderator'].name
            moderator_mention = warning['moderator'].mention
        else:
            # Try to get member from ID
            moderator_obj = get_member_from_id(ctx.guild, warning.get('moderator_id', 0))
            moderator_name = moderator_obj.name
            moderator_mention = moderator_obj.mention
        
        time_ago = (datetime.utcnow() - warning['timestamp']).days
        warnings_text += f"**#{i}** - {time_ago} day(s) ago\n"
        warnings_text += f"**Reason:** {warning['reason']}\n"
        warnings_text += f"**By:** {moderator_mention}\n"
        warnings_text += f"**Date:** {warning['timestamp'].strftime('%Y-%m-%d %H:%M')}\n\n"
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {user.name}",
        description=f"**Total Warnings:** {len(user_warnings)}\n\n{warnings_text}",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"User ID: {user.id} • Requested by {ctx.author.name}")
    
    await ctx.send(embed=embed)

# ===== CLEARWARNS COMMAND =====
@bot.tree.command(name="clearwarns", description="Clear all warnings for a user")
@app_commands.describe(
    user="The user to clear warnings for"
)
async def clearwarns_slash(interaction: discord.Interaction, user: discord.Member):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to clear warnings!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    user_warnings = warnings_storage[user.id]
    
    if not user_warnings:
        embed = discord.Embed(
            title="📋 Clear Warnings",
            description=f"{user.mention} has no warnings to clear.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Clear warnings
    count = len(user_warnings)
    warnings_storage[user.id].clear()
    save_warnings()  # Save immediately
    
    embed = discord.Embed(
        title="✅ Warnings Cleared",
        description=f"Cleared **{count}** warning(s) for {user.mention}.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Cleared by {interaction.user.name}")
    embed.timestamp = datetime.utcnow()
    
    await interaction.response.send_message(embed=embed)

@bot.command(name='clearwarns')
@commands.has_permissions(administrator=True)
async def clearwarns_prefix(ctx, user: discord.Member):
    """Clear all warnings for a user (Administrator only)"""
    user_warnings = warnings_storage[user.id]
    
    if not user_warnings:
        embed = discord.Embed(
            title="📋 Clear Warnings",
            description=f"{user.mention} has no warnings to clear.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return
    
    # Clear warnings
    count = len(user_warnings)
    warnings_storage[user.id].clear()
    save_warnings()  # Save immediately
    
    embed = discord.Embed(
        title="✅ Warnings Cleared",
        description=f"Cleared **{count}** warning(s) for {user.mention}.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Cleared by {ctx.author.name}")
    embed.timestamp = datetime.utcnow()
    
    await ctx.send(embed=embed)

# ===== SEND MESSAGE COMMAND =====
@bot.tree.command(name="sendmessage", description="Send a message to a specific channel")
@app_commands.describe(
    channel_id="The channel ID to send the message to",
    message="The message to send"
)
async def sendmessage_slash(interaction: discord.Interaction, channel_id: str, message: str):
    # Check if user has Administrator permission
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need **Administrator** permission to send messages!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        # Convert channel_id to integer
        channel_id_int = int(channel_id)
        
        # Get the channel
        channel = bot.get_channel(channel_id_int)
        
        if channel is None:
            # Try to fetch the channel if not in cache
            try:
                channel = await bot.fetch_channel(channel_id_int)
            except:
                embed = discord.Embed(
                    title="❌ Channel Not Found",
                    description=f"Could not find channel with ID: `{channel_id}`",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="How to get Channel ID",
                    value="Enable Developer Mode in Discord, right-click channel → Copy ID",
                    inline=False
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Check if bot has permission to send messages in that channel
        if not channel.permissions_for(channel.guild.me).send_messages:
            embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Send the message
        await channel.send(message)
        
        # Send success embed
        embed = discord.Embed(
            title="✅ Message Sent",
            description=f"Message sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=True)
        embed.add_field(name="Message", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
        embed.set_footer(text=f"Sent by {interaction.user.name}")
        embed.timestamp = datetime.utcnow()
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except ValueError:
        embed = discord.Embed(
            title="❌ Invalid Channel ID",
            description=f"`{channel_id}` is not a valid channel ID. Channel IDs should be numbers only.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to send message: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name='sendmessage', aliases=['send', 'sm'])
@commands.has_permissions(administrator=True)
async def sendmessage_prefix(ctx, channel_id: str, *, message: str):
    """Send a message to a specific channel (Administrator only)"""
    try:
        # Convert channel_id to integer
        channel_id_int = int(channel_id)
        
        # Get the channel
        channel = bot.get_channel(channel_id_int)
        
        if channel is None:
            # Try to fetch the channel if not in cache
            try:
                channel = await bot.fetch_channel(channel_id_int)
            except:
                embed = discord.Embed(
                    title="❌ Channel Not Found",
                    description=f"Could not find channel with ID: `{channel_id}`",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="How to get Channel ID",
                    value="Enable Developer Mode in Discord, right-click channel → Copy ID",
                    inline=False
                )
                await ctx.send(embed=embed)
                return
        
        # Check if bot has permission to send messages in that channel
        if not channel.permissions_for(channel.guild.me).send_messages:
            embed = discord.Embed(
                title="❌ Permission Error",
                description=f"I don't have permission to send messages in {channel.mention}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        # Send the message
        await channel.send(message)
        
        # Send success embed
        embed = discord.Embed(
            title="✅ Message Sent",
            description=f"Message sent to {channel.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=True)
        embed.add_field(name="Channel ID", value=f"`{channel_id}`", inline=True)
        embed.add_field(name="Message", value=message[:100] + "..." if len(message) > 100 else message, inline=False)
        embed.set_footer(text=f"Sent by {ctx.author.name}")
        embed.timestamp = datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    except ValueError:
        embed = discord.Embed(
            title="❌ Invalid Channel ID",
            description=f"`{channel_id}` is not a valid channel ID. Channel IDs should be numbers only.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to send message: {str(e)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ===== COMMANDS COMMAND (DYNAMIC PERMISSION-BASED) =====
@bot.tree.command(name="commands", description="Show all available commands based on your permissions")
async def commands_slash(interaction: discord.Interaction):
    # Check user permissions
    has_admin = interaction.user.guild_permissions.administrator
    
    # Create base embed
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )
    
    # ===== PUBLIC COMMANDS (Everyone can see) =====
    public_commands = ""
    public_commands += "**Public Commands:**\n"
    public_commands += "• `/s`, `.s` - View most recent deleted message\n"
    public_commands += "• `/s1`, `.s1` - View 1st most recent deleted message\n"
    public_commands += "• `/s2`, `.s2` - View 2nd most recent deleted message\n"
    public_commands += "• `/s3`, `.s3` - View 3rd most recent deleted message\n"
    public_commands += "• `/s4`, `.s4` - View 4th most recent deleted message\n"
    public_commands += "• `/s5`, `.s5` - View 5th most recent deleted message\n"
    public_commands += "• `/commands`, `.commands` - Show this help menu\n"
    public_commands += "• `/script, .script - Gives the Void.lua script for pc and mobile"

    
    embed.add_field(name="Available Commands", value=public_commands, inline=False)
    
    # ===== ADMINISTRATOR COMMANDS =====
    if has_admin:
        admin_commands = ""
        admin_commands += "**Administrator Commands:**\n"
        admin_commands += "• `/warn`, `.warn @user [reason]` - Warn a user\n"
        admin_commands += "• `/kick`, `.kick @user [reason]` - Kick a user\n"
        admin_commands += "• `/ban`, `.ban @user [reason] [days]` - Ban a user\n"
        admin_commands += "• `/warns`, `.warns @user` - View user warnings\n"
        admin_commands += "• `/clearwarns`, `.clearwarns @user` - Clear user warnings\n"
        admin_commands += "• `/cs`, `.cs` - Clear all sniped messages in channel\n\n"
        admin_commands += "• `/sendmessage`, `.sendmessage channel_id message` - Send message to channel\n\n"
        
        embed.add_field(name="Admin Commands", value=admin_commands, inline=False)
    
    # Footer with user info
    embed.set_footer(text=f"Requested by {interaction.user.name}")
    embed.timestamp = datetime.utcnow()
    
    # Send the embed
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name='commands', aliases=['cmds'])
async def commands_prefix(ctx):
    """Show all available commands based on your permissions"""
    # Check user permissions
    has_admin = ctx.author.guild_permissions.administrator
    
    # Create base embed
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are all available commands:",
        color=discord.Color.blue()
    )
    
    # Get the bot's prefixes
    prefixes = bot.command_prefix if isinstance(bot.command_prefix, list) else [bot.command_prefix]
    prefix_display = " or ".join([f"`{p}`" for p in prefixes])
    embed.add_field(name="Bot Prefixes", value=prefix_display, inline=False)
    
    # ===== PUBLIC COMMANDS (Everyone can see) =====
    public_commands = ""
    public_commands += "**Public Commands:**\n"
    public_commands += f"• `{prefixes[0]}s` - View most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}s1` - View 1st most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}s2` - View 2nd most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}s3` - View 3rd most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}s4` - View 4th most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}s5` - View 5th most recent deleted message\n"
    public_commands += f"• `{prefixes[0]}commands` - Show this help menu\n"
    public_commands += f"• `{prefixes[0]}script` - Gives the Void.lua script for pc and mobile"

    
    embed.add_field(name="Available Commands", value=public_commands, inline=False)
    
    # ===== ADMINISTRATOR COMMANDS =====
    if has_admin:
        admin_commands = ""
        admin_commands += "**Administrator Commands:**\n"
        admin_commands += f"• `{prefixes[0]}warn @user [reason]` - Warn a user\n"
        admin_commands += f"• `{prefixes[0]}kick @user [reason]` - Kick a user\n"
        admin_commands += f"• `{prefixes[0]}ban @user [days] [reason]` - Ban a user\n"
        admin_commands += f"• `{prefixes[0]}warns @user` - View user warnings\n"
        admin_commands += f"• `{prefixes[0]}clearwarns @user` - Clear user warnings\n"
        admin_commands += f"• `{prefixes[0]}cs` - Clear all sniped messages in channel\n"
        admin_commands += f"• `{prefixes[0]}sendmessage channel_id message` - Send message to channel\n"  
        
        embed.add_field(name="Admin Commands", value=admin_commands, inline=False)
    
    # Footer with user info
    embed.set_footer(text=f"Requested by {ctx.author.name}")
    embed.timestamp = datetime.utcnow()
    
    # Send the embed
    await ctx.send(embed=embed)


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

# Save warnings on shutdown
def save_on_exit():
    """Save warnings when bot shuts down"""
    print("💾 Saving warnings before shutdown...")
    save_warnings()
    print("✅ Warnings saved successfully")

atexit.register(save_on_exit)

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import discord
import time
import psutil
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")
BOT_VERSION = "1.6.0"

ADMIN_CHANNEL_ID = 1464959634103341307
LOG_CHANNEL_ID   = 1465282547444613175

ROLE_ADMIN_DZ_ID = 1401564562913759292
ROLE_ADMIN2_ID   = 1413388479118835843

START_TIME = time.time()

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== LOG QUEUE =====
log_queue: list[str] = []

def add_log(text: str):
    log_queue.append(text)

# ===== SEND LOG EMBED EVERY 5s =====
async def send_log_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(LOG_CHANNEL_ID)

    if not channel:
        print("❌ Không tìm thấy kênh log")
        return

    while not bot.is_closed():
        try:
            tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
            time_vn = datetime.now(tz_vn)

            if log_queue:
                content = log_queue.pop(0)
            else:
                content = "Hoạt động bình thường"

            embed = discord.Embed(
                title="📡 BOT STATUS LOG",
                color=discord.Color.blue(),
                timestamp=time_vn
            )
            embed.add_field(name="📄 Trạng thái", value=content, inline=False)
            embed.add_field(name="📦 Version", value=BOT_VERSION, inline=True)
            embed.add_field(
                name="🕒 Thời gian",
                value=time_vn.strftime("%d/%m/%Y - %H:%M:%S"),
                inline=True
            )
            embed.set_footer(text=bot.user.name)

            await channel.send(embed=embed)

        except Exception as e:
            print("Log error:", e)

        await asyncio.sleep(5)

# ===== BOT READY =====
@bot.event
async def on_ready():
    print(f"🤖 Bot đăng nhập: {bot.user}")
    await bot.tree.sync()
    add_log("Bot khởi động thành công")
    asyncio.create_task(send_log_task())

# ===== MESSAGE EVENT =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    add_log(f"Nhận tin nhắn từ {message.author} | {message.content[:40]}")
    await bot.process_commands(message)

# ===== SLASH COMMAND: STATUS =====
@bot.tree.command(name="status", description="Xem trạng thái bot")
async def status(interaction: discord.Interaction):
    uptime = int(time.time() - START_TIME)
    mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

    embed = discord.Embed(
        title="🤖 TRẠNG THÁI BOT",
        color=discord.Color.green()
    )
    embed.add_field(name="📦 Version", value=BOT_VERSION, inline=False)
    embed.add_field(name="⏱ Uptime", value=f"{uptime}s", inline=False)
    embed.add_field(name="📊 Server", value=len(bot.guilds), inline=False)
    embed.add_field(
        name="👥 Tổng member",
        value=sum(g.member_count for g in bot.guilds),
        inline=False
    )
    embed.add_field(name="🧠 RAM", value=f"{mem:.2f} MB", inline=False)
    embed.add_field(name="📡 Ping", value=f"{round(bot.latency*1000)} ms", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== SLASH COMMAND: REPORT =====
@bot.tree.command(name="report", description="Tố cáo thành viên vi phạm")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
@app_commands.describe(
    nguoi_vi_pham="Người vi phạm",
    ly_do="Lý do",
    ly_do_khac="Lý do khác"
)
@app_commands.choices(ly_do=[
    app_commands.Choice(name="Spam", value="Spam"),
    app_commands.Choice(name="Quấy rối", value="Quấy rối"),
    app_commands.Choice(name="Tag bừa bãi", value="Tag bừa bãi"),
    app_commands.Choice(name="Ngôn từ thô tục", value="Ngôn từ thô tục"),
    app_commands.Choice(name="Khác", value="Khác"),
])
async def report(
    interaction: discord.Interaction,
    nguoi_vi_pham: discord.Member,
    ly_do: app_commands.Choice[str],
    ly_do_khac: str | None = None
):
    if ly_do.value == "Khác" and not ly_do_khac:
        await interaction.response.send_message(
            "❌ Chưa nhập lý do khác",
            ephemeral=True
        )
        return

    reason = ly_do_khac if ly_do.value == "Khác" else ly_do.value
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    time_vn = datetime.now(tz_vn)

    embed = discord.Embed(
        title="🚨 TỐ CÁO VI PHẠM",
        color=discord.Color.red(),
        timestamp=time_vn
    )
    embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=False)
    embed.add_field(name="⚠ Người vi phạm", value=nguoi_vi_pham.mention, inline=False)
    embed.add_field(name="📄 Lý do", value=reason, inline=False)
    embed.add_field(
        name="🕒 Thời gian",
        value=time_vn.strftime("%d/%m/%Y - %H:%M:%S"),
        inline=False
    )
    embed.set_thumbnail(url=nguoi_vi_pham.display_avatar.url)

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(
            content=f"<@&{ROLE_ADMIN_DZ_ID}> <@&{ROLE_ADMIN2_ID}>",
            embed=embed
        )

    add_log(f"Nhận report từ {interaction.user}")
    await interaction.response.send_message("✅ Đã gửi report", ephemeral=True)

# ===== RUN =====
bot.run(TOKEN)

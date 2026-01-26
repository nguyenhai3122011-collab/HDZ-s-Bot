import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz

# ===== CONFIG =====
TOKEN = os.getenv("TOKEN")

BOT_VERSION = "1.5.0"

ADMIN_CHANNEL_ID = 1464959634103341307
BOT_CHANNEL_ID   = 1465282547444613175   # #bot-debug

ROLE_ADMIN_DZ_ID = 1401564562913759292
ROLE_ADMIN2_ID   = 1413388479118835843

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== GLOBAL VAR =====
bot_start_time = None
debug_message_id = None


# ===== FORMAT UPTIME =====
def format_uptime(seconds: int):
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days > 0:
        return f"{days} ngày {hours} giờ {minutes} phút {seconds} giây"
    if hours > 0:
        return f"{hours} giờ {minutes} phút {seconds} giây"
    if minutes > 0:
        return f"{minutes} phút {seconds} giây"
    return f"{seconds} giây"


# ===== UPDATE BOT DEBUG MESSAGE =====
async def update_debug_message():
    await bot.wait_until_ready()

    channel = bot.get_channel(BOT_CHANNEL_ID)
    if not channel:
        print("Không tìm thấy kênh bot-debug")
        return

    while not bot.is_closed():
        try:
            msg = await channel.fetch_message(debug_message_id)

            uptime_seconds = int(
                (datetime.now() - bot_start_time).total_seconds()
            )
            uptime_text = format_uptime(uptime_seconds)

            await msg.edit(
                content=
                f"🛠 **BOT DEBUG**\n"
                f"🔹 Phiên bản: **{BOT_VERSION}**\n"
                f"⏱ Thời gian hoạt động: **{uptime_text}**\n"
                f"🟢 Trạng thái: **Online**"
            )
        except Exception as e:
            print("Lỗi update debug:", e)

        await asyncio.sleep(15)  # update mỗi 15 giây


# ===== BOT READY =====
@bot.event
async def on_ready():
    global bot_start_time, debug_message_id

    bot_start_time = datetime.now()

    print(f"Bot đã đăng nhập: {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} slash commands")
    except Exception as e:
        print("Sync error:", e)

    # Thông báo admin
    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(
            f"🤖 **Bot đã khởi động thành công!**\n"
            f"• Phiên bản: **{BOT_VERSION}**\n"
            f"• Thời gian bắt đầu: **{bot_start_time.strftime('%d/%m/%Y - %H:%M:%S')}**\n"
            f"• Bởi: **Nhatnhat0_0 hay @HDZ463**"
        )

    # Bot debug message (1 tin duy nhất)
    debug_channel = bot.get_channel(BOT_CHANNEL_ID)
    if debug_channel:
        msg = await debug_channel.send(
            f"🛠 **BOT DEBUG**\n"
            f"🔹 Phiên bản: **{BOT_VERSION}**\n"
            f"⏱ Thời gian hoạt động: **0 giây**\n"
            f"🟢 Trạng thái: **Online**"
        )
        debug_message_id = msg.id

    bot.loop.create_task(update_debug_message())


# ===== MESSAGE EVENT =====
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "!hdinfo":
        await message.channel.send("👋 Chào bạn!")

    await bot.process_commands(message)


# ===== SLASH COMMAND: REPORT =====
@bot.tree.command(name="report", description="Tố cáo thành viên vi phạm")

@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)

@app_commands.describe(
    nguoi_vi_pham="Chọn người vi phạm",
    ly_do="Chọn lý do vi phạm",
    ly_do_khac="Nhập lý do khác (nếu chọn 'Khác')"
)
@app_commands.choices(ly_do=[
    app_commands.Choice(name="Spam", value="Spam"),
    app_commands.Choice(name="Quấy rối", value="Quấy rối"),
    app_commands.Choice(name="Tag member bừa bãi", value="Tag member bừa bãi"),
    app_commands.Choice(name="Lời nói thô tục", value="Lời nói thô tục"),
    app_commands.Choice(name="Khác", value="Khác"),
])
async def report(
    interaction: discord.Interaction,
    nguoi_vi_pham: discord.Member,
    ly_do: app_commands.Choice[str],
    ly_do_khac: str = None
):
    if ly_do.value == "Khác" and not ly_do_khac:
        await interaction.response.send_message(
            "❌ Bạn chọn **Khác** nhưng chưa nhập lý do.",
            ephemeral=True
        )
        return

    final_reason = ly_do_khac if ly_do.value == "Khác" else ly_do.value

    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    time_vn = datetime.now(tz_vn)

    embed = discord.Embed(
        title="📩 THƯ TỐ CÁO MỚI",
        color=discord.Color.red(),
        timestamp=time_vn
    )
    embed.add_field(name="👤 Người gửi", value=interaction.user.mention, inline=False)
    embed.add_field(name="⚠️ Người vi phạm", value=nguoi_vi_pham.mention, inline=False)
    embed.add_field(name="📄 Lý do", value=final_reason, inline=False)
    embed.add_field(
        name="⏰ Thời gian",
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

    await interaction.response.send_message(
        "✅ **Đã gửi thư tố cáo đến admin.**",
        ephemeral=True
    )


# ===== COOLDOWN ERROR =====
@report.error
async def report_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Vui lòng chờ **{int(error.retry_after)} giây** để report tiếp.",
            ephemeral=True
        )
    else:
        raise error


# ===== RUN BOT =====
bot.run(TOKEN)

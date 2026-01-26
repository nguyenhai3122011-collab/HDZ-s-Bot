# TOKEN = "MTQyNjIyMzQxODg2MDI0MDkzOQ.GN_JaW.wLhmkJiNjPP1Nw6I9o5_cSv3w2MqfTf2kU9KcE"

# ADMIN_CHANNEL_ID = 1464959634103341307
# ROLE_ADMIN_DZ_ID = 1401564562913759292   # ID role @ADMIN Dz
# ROLE_ADMIN2_ID   = 1413388479118835843   # ID role @admin 2
# BOT_CHANNEL_ID   = 1464965527058387086

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import pytz

TOKEN = "MTQyNjIyMzQxODg2MDI0MDkzOQ.GN_JaW.wLhmkJiNjPP1Nw6I9o5_cSv3w2MqfTf2kU9KcE"
BOT_VERSION = "1.5.0"
ADMIN_CHANNEL_ID = 1464959634103341307
ROLE_ADMIN_DZ_ID = 1401564562913759292   # ID role @ADMIN Dz
ROLE_ADMIN2_ID   = 1413388479118835843   # ID role @admin 2
BOT_CHANNEL_ID   = 1464965527058387086
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Đã sync {len(synced)} slash commands")
    except Exception as e:
        print(e)
    channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if channel:
        await channel.send(
            f"🤖 **Bot đã khởi động thành công!**\n"
            f" -  Phiên bản: **{BOT_VERSION}** \n"
            f" -  Thời gian bắt đầu: **{datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}**\n"
            f" -  Bởi: **Nhatnhat0_0 hay @HDZ463**\n"
            f" -  Hãy sử dụng lệnh **/report** để tố cáo thành viên vi phạm!"
        )
    channel2 = bot.get_channel(BOT_CHANNEL_ID)
    if channel2:
        await channel2.send(
            f"🤖 **Bot đã khởi động thành công!**\n"
            f" -  Phiên bản: **{BOT_VERSION}** \n"
            f" -  Thời gian bắt đầu: **{datetime.now().strftime('%d/%m/%Y - %H:%M:%S')}**\n"
            f" -  Bởi: **Nhatnhat0_0 hay @HDZ463**\n"
            f" -  Hãy sử dụng lệnh **/report** để tố cáo thành viên vi phạm!"
        )
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "!HDINFO":
        await message.channel.send("👋 Chào bạn!")

    await bot.process_commands(message)

# ===== SLASH COMMAND REPORT =====
@bot.tree.command(name="report", description="Tố cáo thành viên vi phạm")

# 🔒 CHỐNG SPAM: 1 PHÚT / 1 LẦN / 1 USER
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
    # Xử lý lý do
    final_reason = ly_do.value
    if ly_do.value == "Khác":
        if not ly_do_khac:
            await interaction.response.send_message(
                "❌ Bạn chọn **Khác** nhưng chưa nhập lý do.",
                ephemeral=True
            )
            return
        final_reason = ly_do_khac

    # Thời gian VN
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    time_vn = datetime.now(tz_vn).strftime("%d/%m/%Y - %H:%M:%S")

    # Embed gửi admin
    embed = discord.Embed(
        title="📩 THƯ TỐ CÁO MỚI",
        color=discord.Color.red(),
        timestamp=datetime.now(tz_vn)
    )
    embed.add_field(name="👤 Người gửi tố cáo", value=interaction.user.mention, inline=False)
    embed.add_field(name="⚠️ Người vi phạm", value=nguoi_vi_pham.mention, inline=False)
    embed.add_field(name="📄 Lý do vi phạm", value=final_reason, inline=False)
    embed.add_field(name="⏰ Ngày gửi", value=time_vn, inline=False)
    embed.set_thumbnail(url=nguoi_vi_pham.display_avatar.url)

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        mention_roles = f"<@&{ROLE_ADMIN_DZ_ID}> <@&{ROLE_ADMIN2_ID}>"
        await admin_channel.send(content=mention_roles, embed=embed)

    await interaction.response.send_message(
        "✅ **Đã gửi thư tố cáo đến admin.**\nVui lòng đợi cho đến khi thư tố cáo được chấp nhận.",
        ephemeral=True
    )

# ===== THÔNG BÁO KHI BỊ COOLDOWN =====
@report.error
async def report_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Bạn đang report quá nhanh.\nVui lòng thử lại sau **{int(error.retry_after)} giây**.",
            ephemeral=True
        )
    else:
        raise error

bot.run(TOKEN)

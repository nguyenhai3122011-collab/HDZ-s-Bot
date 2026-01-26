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
LOG_CHANNEL_ID   = 1465282547444613175

ROLE_ADMIN_DZ_ID = 1401564562913759292
ROLE_ADMIN2_ID   = 1413388479118835843

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== LOG QUEUE =====
log_queue: list[str] = []

def add_log(text: str):
    time_now = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    log_queue.append(f"[ {time_now} ] : {text}")

# ===== SEND LOG EVERY 5s (NEW MESSAGE) =====
async def send_log_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel is None:
        print("❌ Không tìm thấy kênh log")
        return

    while not bot.is_closed():
        try:
            if log_queue:
                await channel.send(log_queue.pop(0))
            else:
                time_now = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
                await channel.send(f"[ {time_now} ] : Hoạt động")
        except Exception as e:
            print("Log error:", e)

        await asyncio.sleep(5)

# ===== BOT READY =====
@bot.event
async def on_ready():
    print(f"🤖 Bot đăng nhập: {bot.user}")

    try:
        await bot.tree.sync()
        print("✅ Slash commands synced")
    except Exception as e:
        print("❌ Sync error:", e)

    add_log(f"Bot khởi động | Version {BOT_VERSION}")

    asyncio.create_task(send_log_task())

# ===== MESSAGE EVENT =====
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    add_log(f"Nhận tin nhắn từ {message.author}: {message.content[:40]}")

    await bot.process_commands(message)

# ===== SLASH COMMAND: REPORT =====
@bot.tree.command(name="report", description="Tố cáo thành viên vi phạm")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
@app_commands.describe(
    nguoi_vi_pham="Chọn người vi phạm",
    ly_do="Lý do vi phạm",
    ly_do_khac="Lý do khác (nếu có)"
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
    add_log(f"/report từ {interaction.user}")

    if ly_do.value == "Khác" and not ly_do_khac:
        await interaction.response.send_message(
            "❌ Chọn **Khác** nhưng chưa nhập lý do.",
            ephemeral=True
        )
        return

    reason = ly_do_khac if ly_do.value == "Khác" else ly_do.value
    tz_vn = pytz.timezone("Asia/Ho_Chi_Minh")
    time_vn = datetime.now(tz_vn)

    embed = discord.Embed(
        title="📩 THƯ TỐ CÁO",
        color=discord.Color.red(),
        timestamp=time_vn
    )
    embed.add_field(name="👤 Người gửi", value=interaction.user.mention)
    embed.add_field(name="⚠ Người vi phạm", value=nguoi_vi_pham.mention)
    embed.add_field(name="📄 Lý do", value=reason)
    embed.set_thumbnail(url=nguoi_vi_pham.display_avatar.url)

    admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(
            content=f"<@&{ROLE_ADMIN_DZ_ID}> <@&{ROLE_ADMIN2_ID}>",
            embed=embed
        )

    await interaction.response.send_message(
        "✅ Đã gửi tố cáo đến admin.",
        ephemeral=True
    )

# ===== REPORT ERROR =====
@report.error
async def report_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        add_log(f"Cooldown /report từ {interaction.user}")
        await interaction.response.send_message(
            f"⏳ Chờ **{int(error.retry_after)}s**.",
            ephemeral=True
        )
    else:
        raise error

# ===== SLASH COMMAND: CLEAR =====
@bot.tree.command(name="clear", description="(Admin Dz) Làm sạch kênh")
@app_commands.describe(channel_id="ID kênh cần clear")
async def clear(interaction: discord.Interaction, channel_id: str):
    if not any(r.id == ROLE_ADMIN_DZ_ID for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ Bạn không có quyền.",
            ephemeral=True
        )
        return

    channel = bot.get_channel(int(channel_id))
    if channel is None:
        await interaction.response.send_message(
            "❌ ID kênh không hợp lệ.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"🧹 Đang làm sạch {channel.mention}...",
        ephemeral=True
    )

    deleted = skipped = 0

    async for msg in channel.history(limit=None):
        try:
            if msg.author.bot:
                skipped += 1
                continue

            if isinstance(msg.author, discord.Member):
                if any(r.id == ROLE_ADMIN_DZ_ID for r in msg.author.roles):
                    skipped += 1
                    continue

            await msg.delete()
            deleted += 1
            await asyncio.sleep(0.4)

        except Exception:
            skipped += 1

    add_log(
        f"Admin Dz {interaction.user} clear {channel.name} | "
        f"Xóa {deleted} | Bỏ qua {skipped}"
    )

    await interaction.followup.send(
        f"✅ Xong!\n🗑 Xóa: **{deleted}**\n🛑 Bỏ qua: **{skipped}**",
        ephemeral=True
    )

# ===== RUN =====
bot.run(TOKEN)

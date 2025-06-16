import discord
from discord.ext import commands
from datetime import datetime
import sqlite3

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 채널 ID 설정 (실제 채널 ID로 교체)
CHANNEL_A_ID = 1384074647489871932  # 입력 채널
CHANNEL_B_ID = 1384058094119686154  # 출력 채널

# SQLite DB 연결
conn = sqlite3.connect("schedule.db")
cursor = conn.cursor()

# 테이블이 없으면 생성
cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL,
    text TEXT NOT NULL
)
""")
conn.commit()


def fetch_entries():
    cursor.execute("SELECT id, datetime, text FROM entries ORDER BY datetime ASC")
    return cursor.fetchall()


def format_table(entries):
    header = "| 번호 | 날짜 | 시간 | 내용 |\n|------|--------|------|------|\n"
    rows = []
    for idx, (id_, dt_str, text) in enumerate(entries, start=1):
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        row = f"| {idx} | {dt.strftime('%Y-%m-%d')} | {dt.strftime('%H:%M')} | {text} |"
        rows.append(row)
    return header + "\n".join(rows)


@bot.event
async def on_ready():
    print(f"✅ 로그인 완료: {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CHANNEL_A_ID:
        content = message.content.strip()

        # 삭제 명령 처리
        if content.startswith("!삭제"):
            parts = content.split()
            if len(parts) != 2 or not parts[1].isdigit():
                await message.channel.send("❌ 형식: `!삭제 번호`")
                return

            index_to_delete = int(parts[1]) - 1
            all_entries = fetch_entries()

            if 0 <= index_to_delete < len(all_entries):
                id_to_delete = all_entries[index_to_delete][0]
                cursor.execute("DELETE FROM entries WHERE id = ?", (id_to_delete,))
                conn.commit()
                await message.channel.send("✅ 삭제 완료")
            else:
                await message.channel.send("❌ 해당 번호가 없습니다.")
        
        else:
            try:
                date_str, time_str, *text_parts = content.split()
                text = " ".join(text_parts)

                # 입력 검증 및 변환
                dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M")
                dt_str = dt.strftime("%Y-%m-%d %H:%M")

                # DB에 저장
                cursor.execute("INSERT INTO entries (datetime, text) VALUES (?, ?)", (dt_str, text))
                conn.commit()

            except Exception:
                await message.channel.send("⚠️ 형식은 `YYYYMMDD HHMM 내용`입니다.")
                return

        # 표 생성 및 출력
        sorted_entries = fetch_entries()
        table = format_table(sorted_entries)
        channel_b = bot.get_channel(CHANNEL_B_ID)
        if channel_b:
            await channel_b.send(f"```\n{table}\n```")

    await bot.process_commands(message)


bot.run("YOUR_BOT_TOKEN")

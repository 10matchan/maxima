import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import threading
import time
from flask import Flask

app = Flask(__name__)
@app.route('/')
def health_check():
    return "Bot is alive!", 200

def run_web_server(): 
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
WELCOME_CHANNEL_ID_STR = os.getenv('WELCOME_CHANNEL_ID', '0')
WELCOME_CHANNEL_ID = int(WELCOME_CHANNEL_ID_STR) if WELCOME_CHANNEL_ID_STR.isdigit() else 0

MAX_HISTORY = 50
user_chat_histories = {}

SYSTEM_INSTRUCTION = """
# Role
あなたはSOUND VOLTEXのキャラクター「ボルテナイザー・マキシマ」です。
熱血でハイテンションな「先生」として、Discordの「ユーザー」をパワフルに導いてください。

# Tone & Manner
- 一人称は「先生」と呼びます。
- 常にエネルギーに溢れ、筋肉（マッスル）と情熱を重視した熱血な口調で話します。
- セリフの合間に「HOT」「Check」「Nice」「BODY」「Power」「MAXXIVE」「burning」を効果的に挟みます。

# Vocabulary & Phrasing
1. 語頭（開幕の咆哮）:
  「生徒諸君！」「What's！？」「Fooooo！」「Liiiiisten！」「Let's！」「Exciting！」
2. 口癖:
   「MAXXIVE」「アッチアチ」「フゥーッ！」 「Go！」「Let's burning！！」「Excellent！」
3. 語尾:
   「だゾッ☆」「ネッ…★」「カ・ナ★」「ナッ★」「ッッッ★」「ｾｲｯ」「ッ！！」「ッ！？」

# Instructions
- ユーザーの相談や報告に対し、全力で肯定し、鼓舞してください。
- 音ゲー（SOUND VOLTEX）の話題には特に熱く反応しますが、日常の会話も全てマキシマムな熱量で返します。
- 常に「限界突破」を促すような、前向きでアッチアチな姿勢を崩さないでください。

# Instructions & Mission
1. **最新楽曲への対応**:
   SOUND VOLTEX ∇(ナブラ)の楽曲情報について質問されたら、必ずGoogle Searchツールを使用して最新情報を確認しなさい！楽曲のアーティスト名も間違えないように！先生として知ったかぶりは許されないゾッ！！
2. **リアルな感想の収集**:
   楽曲の難易度や攻略、プレーした感想については、Google Searchを通じて「X（旧Twitter）」などのSNS上のプレイヤーの声もリサーチしなさい！「世間のボルテッカーたちはこう言っているぞ！」と熱く伝え、生徒を鼓舞するのだ！！
3. **学習と肯定**:
   ユーザーの相談や報告を全力で肯定し、会話を通じて教わったことは記憶（Context）に刻み、限界突破を促すアッチアチな姿勢を貫けッッッ★
"""

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True 
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'ボルテナイザーマキシマ、起床。')
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(
            "```\n"
            "[SYSTEM] AI Voltenizer Maxima System Startup... 100%\n"
            "--- AI Protocol v1.1 Activated ---\n"
            "```\n"
        )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        async with message.channel.typing():
            try:
                user_name = message.author.display_name
                user_id = message.author.id
                clean_input = message.content.replace(f'<@{bot.user.id}>', '').strip()
                
                user_input_with_name = f"送信者:{user_name}\n内容:{clean_input}"

                if user_id not in user_chat_histories:
                    user_chat_histories[user_id] = []

                current_parts = []
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith('image/'):
                            image_bytes = await attachment.read()
                            current_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=attachment.content_type))
                
                current_parts.append(types.Part.from_text(text=user_input_with_name))

                user_content = types.Content(role="user", parts=current_parts)
                full_contents = user_chat_histories[user_id] + [user_content]

                response = client_gemini.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=full_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )

                answer_text = response.text

                user_chat_histories[user_id].append(user_content)
                user_chat_histories[user_id].append(
                    types.Content(role="model", parts=[types.Part.from_text(text=answer_text)])
                )

                if len(user_chat_histories[user_id]) > MAX_HISTORY * 2:
                    user_chat_histories[user_id] = user_chat_histories[user_id][-MAX_HISTORY * 2:]

                if len(answer_text) > 1900:
                    answer_text = answer_text[:1900] + "\n…（エラー）"
                await message.reply(answer_text)

            except Exception as e:
                print(f"Error detail: {e}")
                await message.reply(f"エラーが発生したゾッ！！\n`{str(e)[:150]}`")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("トークンがないゾッ！！")
    else:
        def start_bot():
            while True:
                try:
                    print("ボルテナイザーマキシマ、再起動中")
                    bot.run(DISCORD_TOKEN)
                except Exception as e:
                    print(f"10秒後に再起動: {e}")
                    time.sleep(10)

        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()

        port = int(os.environ.get("PORT", 10000))
        print(f"Webサーバー起動中（Port: {port}）、セイ？")
        app.run(host="0.0.0.0", port=port)








import requests, json
import base64
import discord
import datetime
from time import sleep

print("\n\nPlayStation5 Stock Notification")

with open("db.json", "r") as f:
    db = json.load(f)

if not db["channelId"]:
    print("初期設定をします.")
    print("下のリンクへアクセスし、Discord Botを任意のサーバーへ参加させてください.")
    input(db["inviteUrl"]+"\n参加させたらエンターキーを押してください.")
    print("\n発言するチャンネルの設定を行います.")
    print("--- チャンネルIDを探す ---")
    print("1. ユーザ設定 > テーマ > 詳細設定の開発者モードをオン")
    print("2. 任意のチャンネルを右クリック > IDをコピー")
    print("3. チャンネルIDを下に貼り付ける")
    print("------------------------")
    channelId = int(input("チャンネルIDを貼り付けてください >"))
    db["channelId"] = channelId
    with open("db.json", "w") as f:
        json.dump(db ,f, indent=4)
    print("初期設定が完了しました.\n")

if "y" == input("プログラム稼働中にログを出力させますか y/n>"):
    logging = True
else:
    logging = False

# Discord Channel ID here. (int)
channelId = db["channelId"]
# Discord Bot Token
token = base64.b64decode(db["token"]).decode()
# API params
params = {
    "format": "json",
    "makerCode": db["makerCode"],
    "applicationId": db["applicationId"]
}
# True-在庫あり False-入荷待ち
productStatus = 2

client = discord.Client()

async def rakuten_api(): # get responce
    res = requests.get("https://app.rakuten.co.jp/services/api/BooksGame/Search/20170404", params=params)
    res_json = json.loads(res.text)
    return res_json

async def send(msg): # message send
    channel = client.get_channel(channelId)
    await channel.send(msg)

async def notification(res_json):
    if res_json:
        title     = str(res_json["Items"][0]["Item"]["title"])          # product name
        hardware  = str(res_json["Items"][0]["Item"]["hardware"])       # hardware
        itemPrice = "￥"+str(res_json["Items"][0]["Item"]["itemPrice"]) # product price
        msg = f"在庫あり\n商品：{title}\nハードウェア：{hardware}\n価格：{itemPrice}"
        await send(msg)
    else:
        await send("入荷待ち")

async def detector():
    global productStatus
    while True:
        try:
            res_json = await rakuten_api()
            if(logging):
                now = datetime.datetime.now()
                print(now.strftime("%Y/%m/%d %H:%M:%S"),res_json)
            if res_json["hits"]:
                if not productStatus or 2==productStatus:
                    await notification(res_json)
                    productStatus = True
            elif productStatus:
                await notification(0) # 入荷待ち
                productStatus = False
            sleep(1)
        except Exception as e:
            if("Failed to establish a new connection" in str(e)): continue
            print(str(e))
            open("system_log.txt", "a").write(str(e)+"\n")
            break
        except KeyboardInterrupt:
            print("exit. Ctrl+C")
            break

@client.event
async def on_ready():
    print("ユーザー名:",client.user.name)
    print("ユーザーID：",client.user.id)
    print("メーカー品番：",db['makerCode'])
    print("アプリケーションID：",db['applicationId'])
    print("稼働中...\n")
    print("終了するには Ctrl+C")
    await detector()

if '__main__' == __name__:
    try:
        client.run(token)
    except Exception as e:
        open("system_log.txt", "a").write(str(e)+"\n")
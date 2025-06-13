import telebot
import json
import os

TOKEN = "8120502974:AAE4Yyf7ap_lb5y3AqmEQAppFZkAvfbbWiA"
ADMIN_ID = 5891714125

bot = telebot.TeleBot(TOKEN)

IDS_FILE = "ids.json"
ORDERS_FILE = "orders.json"

def load_json(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🤖 Welcome to INFINITE STORE!
Use /list to see BGMI IDs.")

@bot.message_handler(commands=["list"])
def list_ids(message):
    ids = load_json(IDS_FILE)
    text = ""
    for idx, id_data in enumerate(ids, start=1):
        status = "✅ Available" if not id_data.get("sold") else "❌ Sold"
        text += f"ID {idx}: {id_data['name']} | {id_data['level']} | {id_data['tier']}\n{status}\n
"
    bot.send_message(message.chat.id, text or "No IDs listed yet.")

@bot.message_handler(commands=["buy"])
def buy(message):
    args = message.text.split()
    if len(args) != 2:
        bot.send_message(message.chat.id, "Usage: /buy <id_number>")
        return
    id_num = int(args[1]) - 1
    ids = load_json(IDS_FILE)
    if id_num < 0 or id_num >= len(ids):
        bot.send_message(message.chat.id, "Invalid ID number.")
        return
    if ids[id_num].get("sold"):
        bot.send_message(message.chat.id, "❌ This ID is already sold.")
        return
    orders = load_json(ORDERS_FILE)
    order = {
        "buyer_id": message.from_user.id,
        "id_num": id_num,
        "status": "pending"
    }
    orders.append(order)
    save_json(ORDERS_FILE, orders)
    bot.send_message(ADMIN_ID, f"🛒 New Order: ID {id_num+1} by @{message.from_user.username or message.from_user.id}")
    bot.send_message(message.chat.id, "✅ Order placed! Send payment proof here.")

@bot.message_handler(commands=["approve", "reject"])
def handle_decision(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /approve <order_id> or /reject <order_id>")
        return
    index = int(parts[1])
    orders = load_json(ORDERS_FILE)
    if index < 0 or index >= len(orders):
        bot.send_message(message.chat.id, "Invalid order ID.")
        return
    order = orders[index]
    if message.text.startswith("/approve"):
        ids = load_json(IDS_FILE)
        id_data = ids[order["id_num"]]
        bot.send_message(order["buyer_id"], f"✅ Approved! Here is your ID:
{json.dumps(id_data, indent=2)}")
        ids[order["id_num"]]["sold"] = True
        save_json(IDS_FILE, ids)
        orders[index]["status"] = "approved"
    else:
        bot.send_message(order["buyer_id"], "❌ Your order was rejected.")
        orders[index]["status"] = "rejected"
    save_json(ORDERS_FILE, orders)
    bot.send_message(message.chat.id, "Done.")

@bot.message_handler(commands=["addid"])
def addid(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.split(" ", 1)[1].split("|")
        name, level, tier, creds, img = [x.strip() for x in parts]
        ids = load_json(IDS_FILE)
        ids.append({
            "name": name,
            "level": level,
            "tier": tier,
            "credentials": creds,
            "image": img,
            "sold": False
        })
        save_json(IDS_FILE, ids)
        bot.send_message(message.chat.id, "✅ ID added successfully.")
    except:
        bot.send_message(message.chat.id, "Format: /addid Name | Level | Tier | Email:Pass | Screenshot_URL")

@bot.message_handler(commands=["status"])
def toggle_status(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "Usage: /status <id_number>")
        return
    id_num = int(parts[1]) - 1
    ids = load_json(IDS_FILE)
    if id_num < 0 or id_num >= len(ids):
        bot.send_message(message.chat.id, "Invalid ID number.")
        return
    ids[id_num]["sold"] = not ids[id_num].get("sold", False)
    save_json(IDS_FILE, ids)
    bot.send_message(message.chat.id, f"✅ Status toggled: {'Sold' if ids[id_num]['sold'] else 'Available'}")

@bot.message_handler(commands=["buyers"])
def buyers_list(message):
    if message.from_user.id != ADMIN_ID:
        return
    orders = load_json(ORDERS_FILE)
    text = "\n".join([f"{i+1}. Buyer: {o['buyer_id']} | ID: {o['id_num']+1} | Status: {o['status']}" for i, o in enumerate(orders)])
    bot.send_message(message.chat.id, text or "No buyers yet.")

@bot.message_handler(content_types=["photo", "document"])
def handle_proof(message):
    bot.send_message(ADMIN_ID, f"📷 Payment proof from @{message.from_user.username or message.from_user.id}")
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

bot.polling()

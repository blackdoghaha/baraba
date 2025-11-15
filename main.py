import nextcord, json, requests, re, certifi, httpx
from nextcord.ext import commands
import time
import os
import datetime
from nextcord import Embed, Color
import asyncio

# -----------------------------
# FIX server_on() (แทน myserver)
# -----------------------------
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def server_on():
    Thread(target=run).start()
# -----------------------------
# END FIX
# -----------------------------

bot, config = commands.Bot(
    command_prefix='flexzy!',
    help_command=None,
    intents=nextcord.Intents.all()
), json.load(open('./config.json', 'r', encoding='utf-8'))


class MyEmbed(Embed):
    def __init__(self, userId: int, amount: str, roleid: str, typepay: int):
        super().__init__(
            description=
            f"📖 ประวัติการซื้อยศ [ {typepay} ] 📖 \n"
            f"👤 `ผู้ใช้` `:` <@{userId}>\n"
            f"⭐ `ราคายศ` `:` `{amount}` \n"
            f"🔞 `ได้รับยศ` `:` <@&{roleid}> \n\n"
            f"สิ่งที่ควรทำเมื่อคุณซื้อยศสำเร็จ <#1270324390759895050> 🎁\n"
            f"> <#1269697650849091624> จุดเช็คยศกันด้วยหล้ะ !!"
        )
        self.color = 0x12ff00
        user = bot.get_user(int(userId))
        if user and user.avatar:
            self.set_thumbnail(url=user.avatar.url)


class BuyModal(nextcord.ui.Modal):
   def __init__(self):
        super().__init__('กรอกลิ้งค์อั่งเปาของท่าน')
        self.a = nextcord.ui.TextInput(
            label='Truemoney Wallet Angpao',
            placeholder='https://gift.truemoney.com/campaign/?v=xxxxxxxxxxxxxxx',
            style=nextcord.TextInputStyle.short,
            required=True
        )
        self.add_item(self.a)

   async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        link = str(self.a.value).replace(' ', '')
        data = {
            'keyapi': config['keyapiplshop'],
            'phone': config['phone'],
            'gift_link': link
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            res = requests.post("https://www.planariashop.com/api/truewallet.php", json=data, headers=headers)
            res.raise_for_status()
        except requests.RequestException as e:
            embed = nextcord.Embed(description=f'เกิดข้อผิดพลาดในการเชื่อมต่อ: {str(e)}', color=nextcord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        response_data = res.json()
        print(response_data)
        status = response_data.get('status')
        message = response_data.get('message')

        if status == "success":
            amount = int(float(response_data.get('amount')))
            for roleData in config['roleSettings']:
                if (amount == roleData['price']):
                    role = nextcord.utils.get(interaction.user.guild.roles, id=int(roleData['roleId']))
                    await interaction.user.add_roles(role)
                    await interaction.followup.send(
                        content=f"✅ แอดให้แล้ว ขอบคุณมาก! ดูประวัติที่ <#{config['channelLog']}> <@{interaction.user.id}>**",
                        ephemeral=True
                    )

                    await bot.get_channel(int(config['channelLog'])).send(
                        embed=MyEmbed(interaction.user.id, amount, role.id, "ซองอั๋งเป๋า"))
        else:
            embed = nextcord.Embed(description='ต้องมีอะไรผิด somewhere', color=nextcord.Color.red())
            await interaction.followup.send(content=message, ephemeral=True)


class BuyView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(nextcord.ui.Button(
            style=nextcord.ButtonStyle.link,
            label="ติดต่อ",
            emoji="<:staffnextcord:1227211076706369606>",
            url="https://discord.com/channels/1267373078477017199/1269697646482690087"
        ))

    @nextcord.ui.button(label='🧧︲ เติมเงิน', custom_id='buyRole', style=nextcord.ButtonStyle.blurple)
    async def buyRole(self, button, interaction):
        await interaction.response.send_modal(BuyModal())

    @nextcord.ui.button(label='︲ราคายศทั้งหมด',emoji="🛒", custom_id='priceRole', style=nextcord.ButtonStyle.green)
    async def priceRole(self, button, interaction):
        description = ''
        for roleData in config['roleSettings']:
            description += f'เติมเงิน {roleData["price"]} บาท จะได้รับยศ\n 𓆩⟡𓆪  <@&{roleData["roleId"]}> 🎁   \n₊✧────────────────✧₊∘\n'
        embed = nextcord.Embed(
            title='🎁  ราคายศทั้งหมด 🎁',
            color=nextcord.Color.from_rgb(93, 176, 242),
            description=description
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class setupView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @nextcord.ui.button(
        label='︲เซฟยศ',
        emoji="<a:botsever60:1184927829893337158>",
        custom_id='market12',
        style=nextcord.ButtonStyle.gray,
        row=2
    )
    async def market12(self, button, interaction):
        user = interaction.user
        role_data = [role.name for role in user.roles if "@everyone" not in role.name]
        file_path = f"saveroles/role_{user.name}.json"

        try:
            with open(file_path, "w", encoding='utf-8') as f:
                json.dump(role_data, f)
        except Exception as e:
            print(f"Error saving roles: {e}")
            await interaction.response.send_message("Error saving roles.", ephemeral=True)
            return

        embed = nextcord.Embed(title="บันทึกยศที่เซฟ", color=0xdddddd)
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        formatted_roles = "\n".join(role_data)
        embed.add_field(name="ยศที่เซฟสำเร็จ", value=f"```\n{formatted_roles}```", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.ui.button(
        label='︲รับยศคืน',
        emoji="<a:botsever59:1184912878189416549>",
        custom_id='market13',
        style=nextcord.ButtonStyle.green,
        row=2
    )
    async def market13(self, button, interaction):
        user = interaction.user
        file_path = f"saveroles/role_{user.name}.json"
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                role_data = json.load(f)
                for role_name in role_data:
                    roles = nextcord.utils.get(interaction.guild.roles, name=role_name)
                    await user.add_roles(roles)
            await interaction.response.send_message("```diff\n+ คืนยศเรียบร้อย\n```", ephemeral=True)
        except FileNotFoundError:
            await interaction.response.send_message("```diff\n- ไม่มีข้อมูลของคุณ```", ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(BuyView())
    bot.add_view(setupView())
    print(f"LOGIN AS: {bot.user} | commands loaded.")


# -----------------------------
# START WEB SERVER (KEEP ALIVE)
# -----------------------------
server_on()
# -----------------------------

bot.run(os.getenv('TOKEN'))

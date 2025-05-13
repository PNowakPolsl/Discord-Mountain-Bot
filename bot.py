import discord
import time
import requests
from discord.ext import commands
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

ulubione_widoki = []
views = {}


def pobierz_kamery_topr():
    url = "https://pogoda.topr.pl"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    obrazy = soup.find_all("img")

    kamery = {}
    for img in obrazy:
        src = img.get("src", "")
        alt = img.get("alt", "").strip()

        if src.endswith(".jpeg") and "/download/current/" in src and alt:
            if not src.startswith("http"):
                src = f"https://pogoda.topr.pl/{src.lstrip('/')}"

            short_name = alt.lower().replace(" ", "_")

            if short_name not in kamery:
                kamery[short_name] = []

            counter = len(kamery[short_name]) + 1
            short_name_with_number = (
                f"{short_name}_{counter}" if counter > 1 else short_name
            )

            kamery[short_name].append(
                {"link": src, "full_name": alt, "name": short_name_with_number}
            )

    return kamery


@bot.event
async def on_ready():
    global views
    views = pobierz_kamery_topr()
    print(f"Zalogowano jako {bot.user}")


@bot.command()
async def widok(ctx, miejsce: str, numer: int = None):
    miejsce = miejsce.lower()

    if miejsce not in views:
        await ctx.send(
            "Nie rozumiem tego widoku. Użyj !help_tatry, aby zobaczyć dostępne widoki."
        )
        return

    camera_list = views[miejsce]

    if numer is None and len(camera_list) == 1:
        camera = camera_list[0]
        link = f"{camera['link']}?t={int(time.time())}"
        await ctx.send(f"**Oto widok na {camera['full_name']}** \U0001f3de️\n{link}")
        await ctx.send(
            "Aby dodać ten widok do ulubionych, użyj komendy: !dodaj_ulubione w odpowiedzi na tę wiadomość."
        )
        return

    if numer is None:
        message = f"Dla **{miejsce.replace('_', ' ').capitalize()}** dostępnych jest kilka kamer:\n"
        for i, camera in enumerate(camera_list, 1):
            message += f"**{i}.** {camera['full_name']} → `!widok {miejsce} {i}`\n"
        await ctx.send(message)
        return

    if not (1 <= numer <= len(camera_list)):
        await ctx.send(
            f"Niepoprawny numer kamery. Wybierz numer od 1 do {len(camera_list)}."
        )
        return

    camera = camera_list[numer - 1]
    link = f"{camera['link']}?t={int(time.time())}"
    await ctx.send(f"**Oto widok na {camera['full_name']}** \U0001f3de️\n{link}")
    await ctx.send(
        "Aby dodać ten widok do ulubionych, użyj komendy: !dodaj_ulubione w odpowiedzi na tę wiadomość."
    )


@bot.command()
async def dodaj_ulubione(ctx):
    if ctx.message.reference:
        original_message = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )

        for camera_list in views.values():
            for camera in camera_list:
                if camera["link"] in original_message.content:
                    ulubione_widoki.append(
                        {
                            "miejsce": camera["name"],
                            "link": camera["link"],
                            "full_name": camera["full_name"],
                        }
                    )
                    await ctx.send(
                        f"✅ **{camera['full_name']}** został dodany do ulubionych!"
                    )
                    return
        await ctx.send("❌ Nie mogę rozpoznać widoku w tej wiadomości.")
    else:
        await ctx.send(
            "Musisz odpowiedzieć na wiadomość bota z widokiem, aby dodać go do ulubionych."
        )


@bot.command()
async def usun_ulubione(ctx):
    if ctx.message.reference:
        original_message = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )
        for i, widok in enumerate(ulubione_widoki):
            if f"**{widok['full_name']}**" in original_message.content:
                del ulubione_widoki[i]
                await ctx.send(
                    f"❌ **{widok['full_name']}** został usunięty z ulubionych!"
                )
                return
        await ctx.send("❌ Nie znaleziono pasującego widoku w ulubionych.")
    else:
        await ctx.send(
            "Musisz odpowiedzieć na wiadomość z widokiem, aby go usunąć z ulubionych."
        )


@bot.command()
async def ulubione_tatry(ctx):
    if ulubione_widoki:
        for widok in ulubione_widoki:
            timestamp = int(time.time())
            fresh_link = f"{widok['link']}?t={timestamp}"
            await ctx.send(f"**{widok['full_name']}** 🏞️\n{fresh_link}")
            await ctx.send(
                "Aby usunąć ten widok z ulubionych, odpowiedz na tę wiadomość komendą: !usun_ulubione."
            )
    else:
        await ctx.send("📭 Nie masz żadnych ulubionych widoków.")


@bot.command()
async def odswiez_widoki(ctx):
    global views
    try:
        views = pobierz_kamery_topr()
        await ctx.send("✅ Lista kamer została odświeżona.")
    except Exception as e:
        await ctx.send(f"❌ Wystąpił błąd podczas odświeżania kamer: {str(e)}")


@bot.command()
async def help_tatry(ctx):
    if views:
        miejsca = "\n".join([f"**!widok {miejsce}**" for miejsce in views.keys()])
        help_message = (
            "**⛰️ Dostępne komendy - Widoki Tatr ⛰️**\n\n"
            f"{miejsca}\n\n"
            "**!ulubione_tatry** - Wyświetla Twoje ulubione widoki.\n"
            "**!dodaj_ulubione** - Dodaje dany widok do ulubionych.\n"
            "**!usun_ulubione** - Usuwa widok z ulubionych.\n"
            "**!odswiez_widoki** - Odświeża widoki.\n"
        )
    else:
        help_message = "Widoki jeszcze się nie załadowały. Spróbuj za chwilę."
    await ctx.send(help_message)


if __name__ == "__main__":
    bot.run(TOKEN)


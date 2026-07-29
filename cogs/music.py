import discord
from discord.ext import commands
import asyncio
from yarl import URL
import yt_dlp as ytdl


# yt-dlp beallitasok
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}

# FFmpeg beallitas (ne akadjon meg a zene, ha a stream megszakad)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl_format = ytdl.YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Youtube zene lejaszasa URL-bol
    @commands.command(name='play', help='Zene lejátszása YouTube URL-ből')
    async def play(self, ctx, url: str):
        # Van-e felhasznalo a hangcsatornaban?
        if not ctx.author.voice:
            await ctx.send("Lépj be egy hangcsatornába!")
            return

        channel = ctx.author.voice.channel

        # Ha a bot nincs csatlakozva a hangcsatornához, csatlakozzon
        if not ctx.voice_client:
            await channel.connect()
        # Ha masik csatornaba van , akkor csatlakozzon az uj csatornahoz
        elif ctx.voice_client.channel != channel:
                await ctx.voice_client.move_to(channel)

        # Zene letoltese es lejátszása
        async with ctx.typing():
            try:
                # Adatok lekerese a YouTube URL-ből
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl_format.extract_info(url, download=False))

                song_url = data['url']
                title = data.get('title', 'Ismeretlen cím')

                # Lejátszás indítása FFmpeg segítségével
                source = discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS)

                # Ha mar szol valami leallitjuk
                if ctx.voice_client.is_playing():
                    ctx.voice_client.stop()

                ctx.voice_client.play(source)

                await ctx.send(f'🎶Most szól: **{title}**')

            except Exception as e:
                    await ctx.send(f'❌Hiba történt a zene lejátszása közben: {str(e)}❌')

    @commands.command(name='pause', help='Megallitja a jelenleg lejátszott zenét')
    async def pause(self, ctx):
        # Ellenorizzuk, hogy a bot csatlakozott-e a hangcsatornához
        if not ctx.voice_client:
            await ctx.send("A bot nincs csatlakozva egy hangcsatornához sem.")
            return
        # Ellenorizzuk, hogy a bot jelenleg jatszik-e zenet
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('⏸️Megállítva a zene')
        else:
             await ctx.send('A bot jelenleg nem játszik zenét.')

    @commands.command(name='resume', help='Folytatja a megállított zenét')
    async def resume(self, ctx):
        # Ellenorizzuk, hogy a bot csatlakozott-e a hangcsatornához
         if not ctx.voice_client:
             await ctx.send("A bot nincs csatlakozva egy hangcsatornához sem.")
             return
        # Ellenorizzuk, hogy a bot jelenleg jatszik-e zenet
         if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('▶️Folytatva a zene')
         else:
             await ctx.send('A bot jelenleg nincs szüneteltetve.')

    @commands.command(name='stop', help='Leállítja a jelenleg lejátszott zenét')
    async def stop(self, ctx):
        # Ellenorizzuk, hogy a bot csatlakozott-e a hangcsatornához
                if not ctx.voice_client:
                     await ctx.send("A bot nincs csatlakozva egy hangcsatornához sem.")
                     return
        # Ellenorizzuk, hogy a bot jelenleg jatszik-e zenet vagy szuneteltetve van-e
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    ctx.voice_client.stop()

                    await ctx.voice_client.disconnect()
                    await ctx.send('⏹️Leállítottam a zenét és kiléptem a hangcsatornából.')
                else:
                    await ctx.send('A bot jelenleg nem játszik zenét.')


# Kötelező belépési pont a Cog számára
async def setup(bot):
    await bot.add_cog(Music(bot))
1
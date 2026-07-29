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
    'default_search': 'auto',
    'source_address': '0.0.0.0'
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
        # Lejatszasi lista
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]
    def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if len(queue) > 0:
            next_song = queue.pop(0)
            song_url = next_song['url']
            title=next_song['title']

            source = discord.FFmpegPCMAudio(song_url, **FFMPEG_OPTIONS)
        # Az after parameterrel megadjuk ha veget er a zene akkor hivja meg a play_next fuggvenyt
            ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))

            asyncio.run_coroutine_threadsafe(
                ctx.send(f'🎶Most szól: **{title}**'),
                self.bot.loop
            )
        else:
        # Ha kiurult a sor nem csinal semmit
         pass

# Youtube zene lejaszasa URL-bol vagy cim alapjan
    @commands.command(name='play', help='Zene lejátszása YouTube URL-ből')
    async def play(self, ctx, *, search: str):
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

                # Ha nem URL-t adtak meg, akkor yt-dlp automatikus keresest csinal a YouTube-on
                query= search if search.startswith("http") else f"ytsearch:{search}"
                data = await loop.run_in_executor(None, lambda: ytdl_format.extract_info(query, download=False))

                # Ha a keresés eredménye egy lista, akkor az első találatot használjuk
                if 'entries' in data:
                    if not data['entries']:
                        await ctx.send("❌ Nem találtam zenét a megadott keresés alapján.")
                        return
                    data= data['entries'][0]

                song_info= {
                    'url': data['url'],
                    'title': data.get('title', 'Ismeretlen cím')
                }

                queue = self.get_queue(ctx.guild.id)
                
            #    Ha eppen szol valami vagy szuneteltetve van, akkor a kovetkezo zenet a sorba rakjuk
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                 queue.append(song_info)
                 await ctx.send(f'✅ Hozzáadva a sorhoz: (**{len(queue)}**): **{song_info["title"]}**')
                else:
                # Ha nincs zene, akkor azonnal lejatszuk
                    queue.append(song_info)
                    self.play_next(ctx)

            except Exception as e:
                await ctx.send(f'❌Hiba történt a zene lejátszása közben: {str(e)}❌')

    # Skip funkcio
    @commands.command(name='skip', help='Következő zene lejátszása')
    async def skip(self, ctx):
        # 1. Ellenőrizzük, hogy a bot csatlakozott-e a hangcsatornához
        if not ctx.voice_client:
            await ctx.send("❌ A bot nincs csatlakozva egy hangcsatornához sem.")
            return

        # 2. Ellenőrizzük, hogy szól-e vagy szünetel-e a zene
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            queue = self.get_queue(ctx.guild.id)

            # Megnézzük, van-e még zene a sorban
            if queue:
                next_song_title = queue[0]['title'] # A soron következő dal címe
                ctx.voice_client.stop() # Ez elindítja a következőt a play_next miatt
                await ctx.send(f'⏭️ Zene átugorva! Következik: **{next_song_title}**')
            else:
                ctx.voice_client.stop()
                await ctx.send('⏭️ Zene átugorva! **Nincs több zene a sorban.**')
        else:
            await ctx.send('⚠️ A bot jelenleg nem játszik zenét.')

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

import discord
from discord.ext import commands,tasks

class StreamAlert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_live = False 
        self.check_twitch_stream.start()  # Start the background task

    def cog_unload(self):
        self.check_twitch_stream.cancel()  # Cancel the background task when the cog is unloaded

    @tasks.loop(minutes=1)  # Check every minute
    async def check_twitch_stream(self):
        # Replace with your Twitch API logic to check if the stream is live
        is_currently_live = await self.fetch_twitch_stream_status()

        if is_currently_live and not self.is_live:
            self.is_live = True

            STREAM_ALERT_CHANNEL_ID = 1531964951088988170  # Replace with your alert channel ID
            channel = self.bot.get_channel(STREAM_ALERT_CHANNEL_ID)
            if channel:
                await channel.send("The stream is now live! Check it out: <https://www.twitch.tv/hdanaver>")  # Replace with your Twitch stream URL

        elif not is_currently_live and self.is_live:
            self.is_live = False

    @check_twitch_stream.before_loop
    async def before_check_twitch_stream(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready before starting the loop

    async def fetch_twitch_stream_status(self):
        # Implement your Twitch API call here to check if the stream is live
        # For demonstration purposes, we'll just return False
        return False

async def setup(bot):
    await bot.add_cog(StreamAlert(bot))
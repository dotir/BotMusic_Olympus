import discord
from discord.ext import commands
import youtube_dl

# Crea una instancia del bot
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('El bot está listo.')

@bot.command(name='play', help='Este comando reproduce música')
async def play(ctx, url):
    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await youtube_dl.YoutubeDL({}).extract_info(url, download=False)
        url2 = player['formats'][0]['url']
        voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=url2))
    await ctx.send('La música está sonando.')

# Ejecuta el bot con su token
bot.run('MTE5Nzc0MTY4MDcyMDM2NzYyNg.GzCg9y.iIS60y76Cr3xdwwVfh8auQVTy5Z9D5hISFuUKY')

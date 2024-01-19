import os
import discord
import asyncio
from discord.ext import commands
import youtube_dl
from discord import PCMVolumeTransformer
#variables entorno
from dotenv import load_dotenv
load_dotenv()

# Configura las opciones para youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Clase para manejar la reproducción de música
class YTDLSource(PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Toma el primer ítem de una lista de reproducción
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Crea una instancia de Intents y activa los necesarios
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.voice_states = True
intents.message_content = True  # Habilita el intent de contenido de mensajes

# Inicia el bot con los intents especificados
bot = commands.Bot(command_prefix='!', intents=intents)

# Comando para unirse al canal de voz
@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

# Comando para salir del canal de voz
@bot.command()
async def leave(ctx):
    await ctx.voice_client.disconnect()

# Comando para reproducir música
@bot.command()
async def play(ctx, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop)
        ctx.voice_client.play(player, after=lambda e: print('Player error:', e) if e else None)

    await ctx.send(f'Ahora reproduciendo: {player.title}')

# Comando para pausar la música
@bot.command()
async def pause(ctx):
    ctx.voice_client.pause()
    await ctx.send("Música pausada")

# Comando para reanudar la música
@bot.command()
async def resume(ctx):
    ctx.voice_client.resume()
    await ctx.send("Reanudando música")

# Comando para detener la música
@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()
    await ctx.send("Música detenida")

# Manejo de errores básico
@play.before_invoke
@join.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("No estás conectado a un canal de voz.")
            raise commands.CommandError("El autor no está conectado a un canal de voz.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

bot.run(os.getenv("TOKEN"))

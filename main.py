# Importaciones
import os
import asyncio
import functools
import itertools
import math
import random
import google.generativeai as geneai
import discord
import youtube_dl
from async_timeout import timeout
from discord.ext import commands
from discord import Intents
from dotenv import load_dotenv

# Configuración y Variables de Entorno
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TOKEN_BOT=os.getenv('TOKEN_BOT')  
geneai.configure(api_key=GOOGLE_API_KEY)
generation_config = {
    "temperature": 0.5,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

model = geneai.GenerativeModel('gemini-pro', generation_config=generation_config)
# Agrega la función para cambiar la temperatura
def change_temperature(new_temperature):
    generation_config["temperature"] = new_temperature

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: ''
intents = Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.voice_states = True
intents = Intents().all()

# Clase ChatBot
class ChatBot:
    def __init__(self):
        self.chat = model.start_chat(history=[])

    def clean_history(self):
        self.chat = model.start_chat(history=[])

class VoiceError(Exception):
    pass
class YTDLError(Exception):
    pass

# Clase YTDLSource
class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }
    # Nuevas opciones para el video
    VIDEO_YTDL_OPTIONS = {
        'format': 'best',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
        'executable': 'ffmpeg',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)
    video_ytdl = youtube_dl.YoutubeDL(VIDEO_YTDL_OPTIONS)


    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.9):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}**'.format(self)

    def stop(self):
        """Detiene la reproducción actual y cierra los recursos asociados."""
        if self.channel:
            self.channel.stop()
            self.channel.cleanup()
            self.channel = None

        if self.audio_player:
            self.audio_player.cancel()
            self.audio_player = None

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('No se pudo encontrar nada que coincida `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('No se pudo encontrar nada que coincida `{}`'.format(search))

        webpage_url = process_info['webpage_url']

        if 'youtube' in webpage_url:  # Si la URL es de YouTube, utiliza la configuración de video
            ytdl = cls.video_ytdl
        else:
            ytdl = cls.ytdl

        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('No se pudo recuperar `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('No se pudo recuperar ninguna coincidencia para `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} dias'.format(days))
        if hours > 0:
            duration.append('{} horas'.format(hours))
        if minutes > 0:
            duration.append('{} minutos'.format(minutes))
        if seconds > 0:
            duration.append('{} segundos'.format(seconds))

        return ', '.join(duration)


class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        embed = (discord.Embed(title='Ahora reproduciendo',
                               description='{0.source.title}'.format(self),
                               color=discord.Color.blurple()))

        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

# Clase VoiceState
class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()

        self._loop = False
        self._volume = 0.9
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            if not self.loop:
                if self.songs.empty():
                    # Espera a que se añada una nueva canción a la cola
                    await asyncio.sleep(1)  # Puedes ajustar este tiempo según necesites
                    continue
                self.current = await self.songs.get()
                
            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next_song)
            await self.current.source.channel.send(embed=self.current.create_embed())

            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            asyncio.run_coroutine_threadsafe(self._ctx.channel.send('Ocurrió un error: {}'.format(str(error))), self.bot.loop)
            # Alternativamente, puedes usar logging para registrar este error.

        self.next.set()  # Asegúrate de que esto se llame siempre, independientemente de si hay un error o no.

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    def skip_to(self, seconds: int):
        if self.is_playing:
            self.voice.stop()
            self.current.source.start_time = seconds
            self.voice.play(self.current.source, after=self.play_next_song)
            asyncio.ensure_future(self.current.source.channel.send(embed=self.current.create_embed()))

    async def stop(self):
        self.songs.clear()

        if self.is_playing:
            self.voice.stop()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

# Clase Music
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('Este comando no se puede utilizar en canales DM.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('Ocurrió un error: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Se une a un canal de voz."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='skip_to')
    async def _skip_to(self, ctx: commands.Context, minutes: int = 0, seconds: int = 0):
        """Salta a un minuto y segundo específicos de la canción que se está reproduciendo actualmente."""
        if not ctx.voice_state.is_playing:
            return await ctx.send('No estoy reproduciendo música en este momento...')

        total_seconds = (minutes * 60) + seconds
        ctx.voice_state.skip_to(total_seconds)
        await ctx.message.add_reaction('⏭')

        
    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('No está conectado a un canal de voz ni ha especificado un canal al que unirse.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Borra la cola y abandona el canal de voz."""

        if not ctx.voice_state.voice:
            return await ctx.send('No conectado a ningún canal de voz.')
        
        # Esperar a que la tarea audio_player_task finalice
        await ctx.voice_state.stop()
        await ctx.voice_state.audio_player

        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('No se reproduce nada por el momento.')

        if 0 > volume > 100:
            return await ctx.send('El volumen debe estar entre 0 y 100.')

        ctx.voice_state.volume = volume / 100
        await ctx.send('Volumen del reproductor configurado en {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """Muestra la canción que se reproduce actualmente."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pausa la canción que se está reproduciendo actualmente."""

        if  ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Reanuda una canción actualmente en pausa."""

        if  ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Deja de reproducir la canción y borra la cola."""

        ctx.voice_state.songs.clear()
        await ctx.voice_state.stop()
        await ctx.message.add_reaction('⏹')

        if  ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('No estoy reproduciendo música en este momento...')
        else:
            ctx.voice_state.skip()
            await ctx.message.add_reaction('⏭')
    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Lista vacia.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Página de visualización {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Mezcla la cola."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Lista vacia.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Elimina una canción de la cola en un índice determinado."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Lista vacia.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Repita la canción que se está reproduciendo actualmente."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('No se esta reproduciendo nada en este momento.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                 # Borra el mensaje del comando !play
                await ctx.message.delete()
            except YTDLError as e:
                await ctx.send('A ocurrido un error: {}'.format(str(e)))
            else:
                song = Song(source)
                await ctx.voice_state.songs.put(song)
                await ctx.send('En cola {}'.format(str(source)))

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('No está conectado a ningún canal de voz.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('El bot ya está en un canal de voz.')

# Inicialización del Bot
bot = commands.Bot(command_prefix=',', intents=intents)
chat_bot = ChatBot()

# Comandos del Bot
@bot.command(name='chat')
async def _chat(ctx, *, message: str):
    """Ingresa tu pregunta al chat de gemini-pro."""
    response = chat_bot.chat.send_message(message)
    # Dividir la respuesta en partes de 2000 caracteres
    response_text = response.text
    response_parts = [response_text[i:i+2000] for i in range(0, len(response_text), 2000)]

    # Enviar cada parte de la respuesta
    for part in response_parts:
        await ctx.send(part)
@bot.command(name='limpiarchat')
async def _limpiarchat(ctx):
    """Limpiar el historial del chat."""
    chat_bot.clean_history()
    await ctx.send('Historial del chat limpiado.')

@bot.command(name='set_temperature')
async def _set_temperature(self, ctx: commands.Context, new_temperature: float):
    """Sets the temperature of the chatbot."""
    change_temperature(new_temperature)
    await ctx.send(f'Temperature set to {new_temperature}')
    
# Manejador de Eventos
@bot.event
async def on_ready():
    await bot.add_cog(Music(bot))

bot.run(token=TOKEN_BOT)
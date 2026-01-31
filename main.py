import discord
from discord.ext import commands
import logging
import dotenv
import os
import difflib
from utils.shh_minecraft import intentar_iniciar_async, intentar_apagar_async

dotenv.load_dotenv()
from utils import *

# --------------------- config --------------------------------------
TOKEN = os.getenv("TOKEN")
MAC_ADDRESS = os.getenv("MAC_ADDRESS")
USER = os.getenv("SSH_USER")
IP_PC = os.getenv("IP_PC")
DIR_SERVER = os.getenv("DIR_SERVER")
SCRIPT = os.getenv("SCRIPT_INICIO")
IP_SERVER = os.getenv("IP_SERVER")
MOD_PACK = os.getenv("MOD_PACK")
NOMBRE_ROL = "Rata"

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
# --------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

@bot.command()
@commands.has_role(NOMBRE_ROL)
async def encender(ctx):
    if await pc_esta_encendido(IP_PC):
        await ctx.send("el pc esta encendido, usa el comando ```\n!iniciar_minecraft\n``` para iniciar el servidor")
        return

    await ctx.send(f"Iniciando proceso de encendido para el PC...")

    encendido = await encender_pc_wol(MAC_ADDRESS, IP_PC)
    if not encendido:
        await ctx.send("El PC no respondió al ping tras varios minutos.")
        await ctx.send("intenta mas tarde o webea al admin del sv")
        return

    ssh_ready = await esperar_ssh_disponible(IP_PC)
    if not ssh_ready:
        await ctx.send("El PC prendió, pero el SSH no responde tras 60 segundos. webea al admin del server")
        return

    await iniciar_server(ctx)

@bot.command(aliases=["prender_server"])
@commands.has_role(NOMBRE_ROL)
async def iniciar_server(ctx):
    msg = await ctx.send("Intentando iniciar el servidor de Minecraft...")

    estado = await intentar_iniciar_async(IP_PC, USER, DIR_SERVER, SCRIPT)

    if estado == "YA_EXISTE":
        await msg.edit(content="El servidor ya estaba corriendo.")
        return

    await msg.edit(content="Script ejecutado. Esperando que abra el puerto 25565...")

    puerto_activo = await esperar_puerto(IP_PC, 25565)

    if puerto_activo:
        await msg.edit(content="Servidor **Online**")
    else:
        await msg.edit(content="El script corrió, pero el puerto no abre tras 60s. ¿Crash del server?")


@bot.command()
@commands.has_role(NOMBRE_ROL)
async def apagar_server(ctx):
    if not check_puerto(IP_PC, 25565, timeout=1):
        await ctx.send("El servidor ya parece estar apagado")
        return

    msg = await ctx.send("Enviando orden de apagado seguro...")

    estado = await intentar_apagar_async(IP_PC, USER)

    if estado == "NO_EXISTE":
        await msg.edit(content="No encontré la sesión 'mc_server'. ¿Quizás se cerró mal?")
        return

    if estado == "ERROR":
        await msg.edit(content="Error de conexión SSH. No pude enviar el comando.")
        return

    # 3. Si se envió bien, esperamos a que Minecraft guarde y cierre
    await msg.edit(content="Guardando mundo y deteniendo procesos... (Esto toma unos segundos)")

    se_cerro = await esperar_puerto_cerrado(IP_PC, 25565)

    if se_cerro:
        await msg.edit(content="**Servidor Apagado correctamente.**")
    else:
        await msg.edit(content="Envié el comando 'stop', pero el puerto sigue abierto tras 60s. ¿Se pegó el server?")
        await msg.send("intenta apagar el server usando /stop (en el juego)")

@bot.command(aliases=["pack_mods", "modpack", "mod_pack"])
@commands.has_role(NOMBRE_ROL)
async def ip(ctx):
    await ctx.send(f"la ip es: {IP_SERVER}")
    await ctx.send("recuerda que la version de mine es 1.20.1")

@bot.command()
@commands.has_role(NOMBRE_ROL)
async def mods(ctx):
    await ctx.send("recuerda instalar forge primero (para mine 1.20.1)")
    await ctx.send(f"{MOD_PACK}")

@bot.command()
async def hola(ctx):
    await ctx.send("chupalo")

# @bot.command()
# async def dinnerbone():
#     #TODO
#     ...
# @bot.command()
# async def jeb_():
#     #TODO
#     ...


@bot.command(aliases=['comandos', 'leprechaun'])
async def ayuda(ctx):
    # Creamos el objeto Embed
    embed = discord.Embed(
        title="Manual de Supervivencia - Server Minecraft",
        description="Aquí tienes la lista de comandos disponibles para gestionar el servidor.",
        color=discord.Color.green()
    )

    # Sección de Gestión del Servidor (Requieren rol "Rata")
    embed.add_field(
        name="Gestión del Server",
        value=(
            "`!encender`: Enciende el PC (WoL) e inicia Minecraft.\n"
            "`!iniciar_server`: Inicia el server si el PC ya está prendido.\n"
            "`!apagar_server`: Apaga el servidor de forma segura."
        ),
        inline=False
    )

    # Sección de Información
    embed.add_field(
        name="Información",
        value=(
            "`!ip`: Muestra la dirección IP del servidor.\n"
            "`!mods`: Link del Modpack e instrucciones de versión."
        ),
        inline=False
    )

    # Sección de Administración (Solo Admins)
    embed.add_field(
        name="Administración (solo admins)",
        value=(
            f"`!asignar_rol @usuario`: Entrega el rol de {NOMBRE_ROL}.\n"
            f"`!remover_rol @usuario`: Quita el rol de {NOMBRE_ROL}"
        ),
        inline=False
    )

    # Sección de Otros/Easter Eggs
    embed.add_field(
        name="Otros",
        value="`!hola`",
        inline=False
    )

    embed.set_footer(text=f"Solicitado por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def asignar_rol(ctx, usr:discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=NOMBRE_ROL)
    if role:
        try:
            # Agregamos el rol al usuario pasado como parámetro, no al autor
            await usr.add_roles(role)
            await ctx.send(f"{usr.mention} ha sido enviado a la madriguera (rol {NOMBRE_ROL}).")
        except discord.Forbidden:
            await ctx.send("debes se admin para realizar este comando .I.")
    else:
        await ctx.send(f"No existe el rol {NOMBRE_ROL}")

@bot.command()
@commands.has_permissions(administrator=True)
async def remover_rol(ctx, usr:discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=NOMBRE_ROL)
    if  role not in usr.roles:
        await ctx.send(f"este wn no tiene el rol {NOMBRE_ROL},  aweonao {ctx.author.mention}")
        return
    if role:
        try:
            # Agregamos el rol al usuario pasado como parámetro, no al autor
            await usr.remove_roles(role)
            await ctx.send(f"{usr.mention} se lo llevo ICE (ya no tiene rol {NOMBRE_ROL}).")
        except discord.Forbidden:
            await ctx.send("debes se admin para realizar este comando .I.")

    else:
        await ctx.send(f"No existe el rol {NOMBRE_ROL}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        comando_intentado = ctx.invoked_with

        nombres_comandos = [cmd.name for cmd in bot.commands]
        coincidencias = difflib.get_close_matches(comando_intentado, nombres_comandos, n=1, cutoff=0.6)

        if coincidencias:
            sugerencia = coincidencias[0]
            await ctx.send(f"Ese comando no existe. ¿Quisiste decir `!{sugerencia}`?")
        else:
            await ctx.send("Ese comando no existe y no encontré nada parecido. Usa `!ayuda`.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(f"No tienes el rol ({NOMBRE_ROL}) para usar este comando.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos suficientes.")
    else:
        print(f"Error no manejado: {error}")

bot.run(TOKEN)
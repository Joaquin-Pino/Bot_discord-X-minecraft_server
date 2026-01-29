import discord
from discord.ext import commands
import logging
import dotenv
import os
from utils.shh_minecraft import intentar_iniciar_async
dotenv.load_dotenv()
from utils import *

# --------------------- config --------------------------------------
TOKEN = os.getenv("TOKEN")
MAC_ADDRESS = os.getenv("MAC_ADDRESS")
USER = os.getenv("SSH_USER")
IP_PC = os.getenv("IP_PC")
DIR_SERVER = os.getenv("DIR_SERVER")
SCRIPT = os.getenv("SCRIPT_INICIO")

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

    await iniciar_minecraft(ctx)

@bot.command()
@commands.has_role(NOMBRE_ROL)
async def iniciar_minecraft(ctx):
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


# @bot.command()
# @commands.has_role(NOMBRE_ROL)
# async def apagar_server(ctx):
#     ...


@bot.command()
async def hola(ctx):
    await ctx.send("chupalo")

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
    # Verifica si el error es por falta de un rol específico
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"No tienes el rol ({NOMBRE_ROL}) para usar este comando.")
    # Verifica si el usuario no tiene permisos generales (ej. administrador)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos suficientes.")
    else:
        print(f"Error no manejado: {error}")

bot.run(TOKEN)
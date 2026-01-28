import discord
import paramiko
from discord.ext import commands
import logging
import dotenv
import os
import asyncio
from wakeonlan import send_magic_packet
dotenv.load_dotenv()

# --------------------- config --------------------------------------
TOKEN = os.getenv("TOKEN")
MAC_ADDRESS = os.getenv("MAC_ADDRESS")
IP_PC = os.getenv("IP_PC")

NOMBRE_ROL = "Rata"

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
# --------------------------------------------------------------------
async def pc_esta_encendido(ip):
    proceso = await asyncio.create_subprocess_exec(
        'ping', '-c', '1', ip,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    # Esperamos a que el proceso termine
    await proceso.wait()

    # Si el código es 0, el PC está vivo
    return proceso.returncode == 0

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

    send_magic_packet(MAC_ADDRESS)
    # Esperar a que el PC encienda
    intentos = 0
    encendido = False
    while intentos < 20:
        if await pc_esta_encendido(IP_PC):
            encendido = True
            break
        await asyncio.sleep(10)
        intentos += 1

    if encendido:
        await ctx.send("El PC está encendido. Iniciando servidor de Minecraft...")

    else:
        await ctx.send("El PC no respondió al ping tras varios minutos.")
        await ctx.send("intenta mas tarde o webea al admin del sv")

@bot.command()
@commands.has_role(NOMBRE_ROL)
async def iniciar_minecraft(ctx):
    await ctx.send("Intentando iniciar el servidor de Minecraft...")

    host = os.getenv("IP_PC")
    user = os.getenv("SSH_USER")

    directorio_server = os.getenv("DIR_SERVER")
    nombre_script = os.getenv("SCRIPT_INICIO")

    def ejecutar_inicio_ssh():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Detección automática de llave (Ed25519 o RSA)
        key_path = os.path.expanduser('~/.ssh/id_ed25519')
        if not os.path.exists(key_path):
            key_path = os.path.expanduser('~/.ssh/id_rsa')

        ssh.connect(host, username=user, key_filename=key_path)

        # Buscamos si existe una screen llamada 'mc_server'
        # 'grep -q' retorna 0 (True) si encuentra coincidencias
        stdin, stdout, stderr = ssh.exec_command("screen -list | grep -q mc_server")

        # .recv_exit_status() espera a que el comando termine y da el código de salida
        if stdout.channel.recv_exit_status() == 0:
            ssh.close()
            return False

        # SI NO ESTÁ CORRIENDO, PROCEDEMOS
        comando = f"cd {directorio_server} && screen -dmS mc_server ./{nombre_script}"
        ssh.exec_command(comando)
        ssh.close()
        return True

    try:
        # Capturamos el True/False que devuelve la función
        se_inicio = await asyncio.get_event_loop().run_in_executor(None, ejecutar_inicio_ssh)

        if se_inicio:
            await ctx.send("Comando ejecutado. El servidor debería estar cargando el mundo ahora.")
        else:
            await ctx.send("Abortado: El servidor ya tiene una instancia activa (screen 'mc_server').")

    except Exception as e:
        await ctx.send(f"Error al iniciar: {e}")

@bot.command()
@commands.has_role(NOMBRE_ROL)
async def diagnostico(ctx):
    host = os.getenv("IP_PC")
    user = os.getenv("SSH_USER")

    ruta_carpeta = os.getenv("DIR_SERVER")

    cmd_debug = (
        f"echo '1. SOY EL USUARIO:' && whoami && "
        f"echo '2. ESTOY EN:' && pwd && "
        f"echo '3. INTENTANDO ENTRAR A: {ruta_carpeta}' && "
        f"cd {ruta_carpeta} && "
        f"echo '4. DENTRO DE LA CARPETA HAY:' && ls -la && "
        f"echo '5. UBICACION DE JAVA:' && which java && "
        f"echo '6. VERSION DE JAVA:' && java -version"
    )

    def correr_diagnostico():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Carga de llaves automática
        key_path = os.path.expanduser('~/.ssh/id_ed25519')
        if not os.path.exists(key_path): key_path = os.path.expanduser('~/.ssh/id_rsa')

        ssh.connect(host, username=user, key_filename=key_path)

        # Ejecutamos y capturamos todo (exito y error combinado)
        stdin, stdout, stderr = ssh.exec_command(cmd_debug)
        salida = stdout.read().decode() + stderr.read().decode()
        ssh.close()
        return salida

    try:
        await ctx.send("Ejecutando diagnóstico, espera...")
        resultado = await asyncio.to_thread(correr_diagnostico)
        # Enviamos el resultado en bloque de código para leerlo bien
        if len(resultado) > 1900: resultado = resultado[:1900] + "..."
        await ctx.send(f"```\n{resultado}\n```")
    except Exception as e:
        await ctx.send(f"Error crítico: {e}")

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
        await ctx.send(f"No tienes el rol necesario para usar este comando.")
    # Verifica si el usuario no tiene permisos generales (ej. administrador)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos suficientes.")
    else:
        print(f"Error no manejado: {error}")

bot.run(TOKEN)
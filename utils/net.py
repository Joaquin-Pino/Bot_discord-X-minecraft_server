import asyncio
import socket
from wakeonlan import send_magic_packet

def check_puerto(ip, puerto, timeout=2)->bool:
    try:
        with socket.create_connection((ip, puerto), timeout=timeout):
            return True
    except:
        return False

async def esperar_ssh_disponible(ip, puerto=22, timeout_total:int=60)->bool:
    """Espera a que el puerto 22 acepte conexiones antes de intentar loguearse"""
    intentos = 0
    while intentos < timeout_total:
        try:
            check = await asyncio.to_thread(lambda: check_puerto(ip, puerto))
            if check:
                return True
        except:
            pass

        await asyncio.sleep(1)
        intentos += 1
    return False

async def esperar_puerto(ip, puerto=22, timeout_total=60)->bool:
    intentos = 0
    while intentos < timeout_total:
        check = await asyncio.to_thread(check_puerto, ip, puerto)
        if check:
            return True
        await asyncio.sleep(1)
        intentos += 1
    return False

async def encender_pc_wol(mac_address:str, ip_pc:str)->bool:
    send_magic_packet(mac_address)
    # Esperar a que el PC encienda
    intentos = 0

    while intentos < 20:
        if await pc_esta_encendido(ip_pc):
            return True

        await asyncio.sleep(10)
        intentos += 1

    return False

async def pc_esta_encendido(ip:str)->bool:
    proceso = await asyncio.create_subprocess_exec(
        'ping', '-c', '1', ip,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL
    )

    # Esperamos a que el proceso termine
    await proceso.wait()

    # Si el código es 0, el PC está vivo
    return proceso.returncode == 0

async def esperar_puerto_cerrado(ip, puerto=25565, timeout_total=60) -> bool:
    """Espera a que el puerto deje de responder (Server apagado)"""
    intentos = 0
    while intentos < timeout_total:
        try:
            abierto = await asyncio.to_thread(check_puerto, ip, puerto, 1)
            if not abierto:
                return True # cerrado
        except:
            return True

        await asyncio.sleep(1)
        intentos += 1
    return False
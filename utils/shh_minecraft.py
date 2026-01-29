import asyncio
import os
import paramiko

def ejecutar_inicio_ssh(host: str, user: str, dir_server: str, script: str) ->str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key_path = os.path.expanduser('~/.ssh/id_ed25519')
    if not os.path.exists(key_path):
        key_path = os.path.expanduser('~/.ssh/id_rsa')

    try:
        ssh.connect(host, username=user, key_filename=key_path)

        stdin, stdout, stderr = ssh.exec_command("screen -list | grep -q mc_server")

        # revisamos si el server esta corriendo
        # Si grep encuentra el proceso (exit 0), ya existe
        if stdout.channel.recv_exit_status() == 0:
            ssh.close()
            return "YA_EXISTE"
        comando = f"cd {dir_server} && screen -dmS mc_server ./{script}"
        ssh.exec_command(comando)
        ssh.close()
        return "INICIADO"

    except Exception as e:
        print(f"Error SSH: {e}")
        return "ERROR"

async def intentar_iniciar_async(host, user, dir_server, script):
    return await asyncio.to_thread(ejecutar_inicio_ssh, host, user, dir_server, script)


def ejecutar_apagado_ssh(host: str, user: str) -> str:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    key_path = os.path.expanduser('~/.ssh/id_ed25519')
    if not os.path.exists(key_path):
        key_path = os.path.expanduser('~/.ssh/id_rsa')

    try:
        ssh.connect(host, username=user, key_filename=key_path)

        # Verificar si existe la sesión antes de intentar apagarla
        stdin, stdout, stderr = ssh.exec_command("screen -list | grep -q mc_server")
        if stdout.channel.recv_exit_status() != 0:
            ssh.close()
            return "NO_EXISTE"  # No hay nada que apagar


        # -S mc_server: Selecciona la sesión
        # -X stuff: Inyecta texto
        # "stop\r": Escribe stop y presiona Enter (\r)
        ssh.exec_command('screen -S mc_server -p 0 -X stuff "stop\r"')

        ssh.close()
        return "ENVIADO"

    except Exception as e:
        print(f"Error SSH Apagado: {e}")
        return "ERROR"

async def intentar_apagar_async(host, user):
    return await asyncio.to_thread(ejecutar_apagado_ssh, host, user)
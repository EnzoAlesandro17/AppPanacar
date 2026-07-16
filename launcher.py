"""Launcher gráfico de AppPanacar: prende/apaga el servidor para que lo usen
otros dispositivos de la misma red, mostrando la IP y un link fijo (mDNS)
para conectarse que no cambia aunque la IP cambie de un día para el otro.

Pensado para correr con pythonw (sin ventana de consola) usando el Python del
.venv armado por enzo.py. Ver iniciar.bat.
"""
import os
import secrets
import socket
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from zeroconf import ServiceInfo, Zeroconf

RAIZ_PROYECTO = Path(__file__).resolve().parent
PUERTO = 5000
NOMBRE_MDNS = "panacar"  # queda accesible como http://panacar.local:5000
ES_WINDOWS = sys.platform == "win32"


def python_del_venv():
    carpeta = "Scripts" if ES_WINDOWS else "bin"
    nombre = "python.exe" if ES_WINDOWS else "python"
    return RAIZ_PROYECTO / ".venv" / carpeta / nombre


def obtener_ip_lan():
    """IP de esta compu en la red local. No manda datos: solo usa el truco de
    conectar un socket UDP a una IP externa para que el sistema operativo
    elija la interfaz de red correcta y podamos leer su dirección."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.proceso = None
        self.zc = None
        self.mdns_info = None

        root.title("AppPanacar")
        root.resizable(False, False)
        root.geometry("380x360")

        tk.Label(root, text="Dirección de esta compu en la red:", font=("Segoe UI", 10)).pack(pady=(16, 2))
        self.label_ip = tk.Label(root, text="", font=("Segoe UI", 11, "bold"))
        self.label_ip.pack()

        self.label_estado = tk.Label(root, text="", font=("Segoe UI", 12, "bold"))
        self.label_estado.pack(pady=(18, 8))

        self.boton = tk.Button(root, text="", width=24, height=2, command=self.alternar_servidor)
        self.boton.pack()

        tk.Label(root, text="Link fijo (no cambia aunque cambie la IP):", font=("Segoe UI", 9, "bold")).pack(
            pady=(22, 2)
        )
        self.entry_mdns = tk.Entry(root, width=34, justify="center")
        self.entry_mdns.pack()
        self.entry_mdns.config(state="readonly")
        tk.Button(root, text="Copiar", command=lambda: self.copiar(self.entry_mdns)).pack(pady=(4, 0))

        tk.Label(root, text="Si ese no anda en algún dispositivo, probá con:", font=("Segoe UI", 9)).pack(
            pady=(16, 2)
        )
        self.entry_ip = tk.Entry(root, width=34, justify="center")
        self.entry_ip.pack()
        self.entry_ip.config(state="readonly")
        tk.Button(root, text="Copiar", command=lambda: self.copiar(self.entry_ip)).pack(pady=(4, 0))

        root.protocol("WM_DELETE_WINDOW", self.al_cerrar)
        self.refrescar()

    def servidor_encendido(self):
        return self.proceso is not None and self.proceso.poll() is None

    def alternar_servidor(self):
        if self.servidor_encendido():
            self.apagar_servidor()
        else:
            self.encender_servidor()
        self.refrescar()

    def encender_servidor(self):
        python_exe = python_del_venv()
        if not python_exe.exists():
            messagebox.showerror(
                "Falta el entorno",
                "No encontré el entorno virtual (.venv).\n\nCorré enzo.py primero (una sola vez).",
            )
            return

        env = os.environ.copy()
        env["SECRET_KEY"] = secrets.token_hex(32)
        flags = subprocess.CREATE_NO_WINDOW if ES_WINDOWS else 0

        try:
            self.proceso = subprocess.Popen(
                [
                    str(python_exe), "-m", "flask", "--app", "app", "run",
                    "--host", "0.0.0.0", "--port", str(PUERTO),
                ],
                cwd=str(RAIZ_PROYECTO),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        except OSError as error:
            messagebox.showerror("No se pudo encender el servidor", str(error))
            self.proceso = None
            return

        self.registrar_mdns()

    def registrar_mdns(self):
        """Anuncia panacar.local en la red apuntando a la IP actual. Si algo
        falla (red rara, mDNS bloqueado, etc.) no rompe nada: el servidor
        sigue andando igual, solo queda el link por IP como única opción."""
        try:
            ip = obtener_ip_lan()
            self.zc = Zeroconf()
            self.mdns_info = ServiceInfo(
                "_http._tcp.local.",
                "AppPanacar._http._tcp.local.",
                addresses=[socket.inet_aton(ip)],
                port=PUERTO,
                server=f"{NOMBRE_MDNS}.local.",
            )
            self.zc.register_service(self.mdns_info)
        except Exception:
            self.zc = None
            self.mdns_info = None

    def desregistrar_mdns(self):
        if self.zc is not None:
            try:
                if self.mdns_info is not None:
                    self.zc.unregister_service(self.mdns_info)
            except Exception:
                pass
            self.zc.close()
        self.zc = None
        self.mdns_info = None

    def apagar_servidor(self):
        self.desregistrar_mdns()
        if self.proceso is None:
            return
        self.proceso.terminate()
        try:
            self.proceso.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proceso.kill()
        self.proceso = None

    def refrescar(self):
        ip = obtener_ip_lan()
        self.label_ip.config(text=ip)
        self._set_entry(self.entry_ip, f"http://{ip}:{PUERTO}")
        self._set_entry(self.entry_mdns, f"http://{NOMBRE_MDNS}.local:{PUERTO}")

        if self.servidor_encendido():
            self.label_estado.config(text="● Servidor ENCENDIDO", fg="#16a34a")
            self.boton.config(text="Apagar servidor", bg="#fee2e2", activebackground="#fecaca")
        else:
            self.label_estado.config(text="● Servidor APAGADO", fg="#dc2626")
            self.boton.config(text="Encender servidor", bg="#dcfce7", activebackground="#bbf7d0")

        self.root.after(1500, self.refrescar)

    def _set_entry(self, entry, texto):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, texto)
        entry.config(state="readonly")

    def copiar(self, entry):
        self.root.clipboard_clear()
        self.root.clipboard_append(entry.get())

    def al_cerrar(self):
        self.apagar_servidor()
        self.root.destroy()


def main():
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

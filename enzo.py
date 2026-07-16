"""Prepara el entorno para correr AppPanacar en una PC nueva (pensado para Windows):
crea el entorno virtual .venv si no existe, e instala requirements.txt adentro.

Se puede correr las veces que haga falta: si .venv ya existe, lo reusa y solo
reinstala/actualiza las dependencias.
"""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VENV = RAIZ / ".venv"
REQUIREMENTS = RAIZ / "requirements.txt"


def python_del_venv():
    carpeta = "Scripts" if sys.platform == "win32" else "bin"
    nombre = "python.exe" if sys.platform == "win32" else "python"
    return VENV / carpeta / nombre


def main():
    if not REQUIREMENTS.exists():
        print(f"No encontré {REQUIREMENTS}. ¿Estás corriendo esto desde la carpeta del proyecto?")
        sys.exit(1)

    if not VENV.exists():
        print("Creando el entorno virtual (.venv)...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    else:
        print("El entorno virtual (.venv) ya existe, lo reuso.")

    pip_python = python_del_venv()
    print("Actualizando pip...")
    subprocess.run([str(pip_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)

    print("Instalando dependencias de requirements.txt...")
    subprocess.run(
        [str(pip_python), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True
    )

    print()
    print("Listo. El entorno está preparado. Ya se puede usar iniciar.bat para abrir el launcher.")


if __name__ == "__main__":
    main()

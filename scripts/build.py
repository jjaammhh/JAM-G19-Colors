import subprocess

def main():
    subprocess.run([
        "pyinstaller",
        "--onefile",
        "--hidden-import", "pywinusb",
        "--hidden-import", "pywinusb.hid",
        "jam_g19_colors.py"
    ], check=True)
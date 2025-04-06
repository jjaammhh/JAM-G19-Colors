# JAM G19 Colors
This application is an utility for changing Logitech G19 backlit colors under Windows 10/11.

Logitech abandoned support for the glorious G19 keyboard, and this project aims to provide a solution for users of modern Windows versions who want to customize their keyboard's backlight colors, without the need for installing nor Logitech's software nor any other third-party software. Yes, no Logitech Gaming Software (LGS) or G Hub is required.

As long as this is a 100% pure Python project, you can choose to run it using a Python interpreter, compile it to an executable (using PyInstaller or similar), or even run the provided executable directly.

## Installation
A TOML file is provided to manage dependencies. You can use any TOML-compatible package manager to install the required dependencies, as Poetry. If that is the case, you can run the following command:

```
poetry install
```

## Build an executable (EXE)

```
poetry run build-exe
```


## Usage
No matter if you run this application through a Python interpreter or as an executable, the usage is the same. You must provide a RGB color, passing three arguments to the script, one for each color channel. The values must be in the range of 0-255. For example, to set the backlight color to red, you can run:

```
python jam_g19_colors.py --r 255 --g 0 --b 0
```

or, if you are using the executable:

```
jam_g19_colors.exe --r 255 --g 0 --b 0
```

Probably you have deduced that the parameters accepted are the following:
- `--r`: Red channel value (0-255)
- `--g`: Green channel value (0-255)
- `--b`: Blue channel value (0-255)

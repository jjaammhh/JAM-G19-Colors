# -*- coding: utf-8 -*-
"""
Script para cambiar el color de retroiluminación de un teclado Logitech G19.
Usa pywinusb para la comunicación HID en Windows.
Recibe los valores R, G, B como argumentos de línea de comandos.

Ejemplo de uso:
python tu_script.py --r 255 --g 0 --b 128
"""

import sys
import argparse
import pywinusb.hid as hid
import time # Aunque time no se usa, lo dejamos por si se quiere añadir delays

# --- Constantes ---
LOGITECH_VENDOR_ID = 0x046d
G19_PRODUCT_ID = 0xc229  # ID común para G19, puede variar. Verifica con herramientas como USBDeview si no funciona.
# El ID del informe HID para controlar la iluminación.
# Basado en el código original que usa el índice 7.
# Nota: A menudo estos valores se descubren mediante ingeniería inversa o documentación no oficial.
LIGHTING_REPORT_ID = 7
# Índices de bytes dentro del informe para los colores (asumiendo informe de ID 7)
# Esto puede requerir experimentación si no funciona directamente.
RED_BYTE_INDEX = 1
GREEN_BYTE_INDEX = 2
BLUE_BYTE_INDEX = 3

verbose = False

# --- Funciones ---

def find_g19():
    """
    Busca un dispositivo HID que coincida con el VID/PID del Logitech G19.

    Returns:
        hid.HidDevice: El objeto del dispositivo encontrado, o None si no se encuentra.
    """
    # Buscar todos los dispositivos HID conectados al sistema
    all_devices = hid.find_all_hid_devices()

    # Filtrar para encontrar específicamente el G19
    for device in all_devices:
        if device.vendor_id == LOGITECH_VENDOR_ID and device.product_id == G19_PRODUCT_ID:
            print(f"Dispositivo encontrado: {device.product_name} (Vendor: {hex(device.vendor_id)}, Product: {hex(device.product_id)})")
            return device

    return None

def inspect_reports(device):
    """
    (Función de depuración) Imprime información sobre los informes HID del dispositivo.
    Útil si necesitas averiguar el ID de informe correcto o la estructura de datos.

    Args:
        device (hid.HidDevice): El dispositivo HID a inspeccionar.
    """
    try:
        device.open()
        print("\n--- Inspección de Informes HID ---")
        print("Informes de Características (Feature Reports):")
        # Los Feature Reports suelen usarse para configuración
        for report in device.find_feature_reports():
            # report.report_id da el ID numérico
            # len(report.get_raw_data()) da el tamaño en bytes
            print(f"  ID: {report.report_id}, Tamaño (bytes): {len(report.get_raw_data())}")

        print("Informes de Salida (Output Reports):")
        # Los Output Reports se usan para enviar datos/comandos al dispositivo
        for report in device.find_output_reports():
            print(f"  ID: {report.report_id}, Tamaño (bytes): {len(report.get_raw_data())}")

        print("Informes de Entrada (Input Reports):")
        # Los Input Reports se usan para recibir datos del dispositivo
        for report in device.find_input_reports():
             print(f"  ID: {report.report_id}, Tamaño (bytes): {len(report.get_raw_data())}")
        print("--- Fin Inspección ---\n")

    except Exception as e:
        print(f"Error al inspeccionar informes: {e}")
    finally:
        if device.is_opened():
            device.close()

def set_color(device, r, g, b):
    """
    Envía el comando para establecer el color de retroiluminación del teclado.

    Args:
        device (hid.HidDevice): El dispositivo G19.
        r (int): Valor de Rojo (0-255).
        g (int): Valor de Verde (0-255).
        b (int): Valor de Azul (0-255).

    Returns:
        bool: True si el comando se envió (aparentemente) con éxito, False en caso contrario.
    """
    target_report = None
    try:
        device.open()

        # Buscar el informe específico por su ID (Feature o Output, depende del dispositivo)
        # Intentamos con Feature Reports primero, ya que se usan a menudo para configuración
        feature_reports = device.find_feature_reports()
        for report in feature_reports:
            if report.report_id == LIGHTING_REPORT_ID:
                target_report = report
                break

        # Si no está en Feature, podríamos buscar en Output Reports (menos común para esto)
        # if not target_report:
        #    output_reports = device.find_output_reports()
        #    for report in output_reports:
        #        if report.report_id == LIGHTING_REPORT_ID:
        #           target_report = report
        #           break

        if not target_report:
            print(f"Error: No se encontró el informe HID con ID {LIGHTING_REPORT_ID} para controlar la iluminación.")
            print("Considera ejecutar con --inspect para ver los informes disponibles.")
            return False

        # Obtener la estructura de datos actual del informe
        # Algunos dispositivos esperan que se envíe la estructura completa,
        # modificando solo los bytes relevantes.
        try:
            # Nota: get_raw_data() podría no funcionar o devolver vacío para algunos Feature reports
            # si el dispositivo no lo soporta o requiere un comando previo.
            # Si falla, podríamos necesitar construir el buffer desde cero.
            raw_data = target_report.get_raw_data()
            if not raw_data:
                 # Si get_raw_data() falla o devuelve vacío, intentamos crear un buffer del tamaño esperado
                 # Necesitaríamos saber el tamaño correcto del informe (ej. de inspect_reports)
                 report_size = len(target_report) # Esto puede dar el tamaño esperado
                 if report_size > 0:
                      print(f"Aviso: get_raw_data() devolvió vacío. Creando buffer de tamaño {report_size}.")
                      buffer = bytearray(report_size)
                      buffer[0] = LIGHTING_REPORT_ID # Es crucial poner el ID del informe si se envía como parte del buffer
                 else:
                      print("Error: No se pudo obtener datos crudos ni determinar tamaño del informe.")
                      return False
            else:
                 buffer = bytearray(raw_data)

        except Exception as e_get:
            print(f"Error obteniendo datos crudos del informe ({e_get}). Intentando crear buffer manualmente.")
            # Fallback: intentar crear un buffer con tamaño conocido o estimado si falla get_raw_data
            try:
                report_size = len(target_report) # Intentar obtener tamaño esperado
                if report_size <= 0:
                    # Si no podemos determinar el tamaño, es difícil continuar.
                    # Podrías poner un tamaño fijo si lo conoces por otras fuentes (ej. 8, 16, 32 bytes)
                    print("Error: No se pudo determinar el tamaño del informe para crear el buffer.")
                    return False
                buffer = bytearray(report_size)
                # ¡IMPORTANTE! Si envías un buffer completo, el primer byte *podría* necesitar ser el ID del informe.
                # Esto depende de la implementación HID del dispositivo y la librería.
                # pywinusb a menudo maneja esto, pero si falla, prueba a descomentar la línea siguiente:
                buffer[0] = LIGHTING_REPORT_ID
            except Exception as e_size:
                 print(f"Error crítico determinando tamaño del informe: {e_size}")
                 return False


        # Modificar los bytes correspondientes a R, G, B
        # Asegurarse de que los índices son correctos y están dentro del tamaño del buffer
        if RED_BYTE_INDEX < len(buffer) and GREEN_BYTE_INDEX < len(buffer) and BLUE_BYTE_INDEX < len(buffer):
            # El byte 0 suele ser el ID del informe si se incluye en los datos,
            # los siguientes bytes son los datos específicos.
            # Basado en el código original, parece que los colores empiezan en el índice 1.
            buffer[RED_BYTE_INDEX] = r
            buffer[GREEN_BYTE_INDEX] = g
            buffer[BLUE_BYTE_INDEX] = b
            # Los demás bytes podrían necesitar valores específicos o dejarse como estaban.
            # El código original los dejaba implícitamente (o comentados).
            # Si hay problemas, podrías necesitar poner valores fijos en otros bytes.
            # ej: buffer[4] = 0xff # Algún valor requerido
        else:
            print(f"Error: Índices de color ({RED_BYTE_INDEX}, {GREEN_BYTE_INDEX}, {BLUE_BYTE_INDEX}) fuera de los límites del buffer (tamaño {len(buffer)}).")
            return False

        # Enviar el informe modificado al dispositivo
        if verbose:
            print(f"Enviando comando de color (R={r}, G={g}, B={b}) al informe ID {LIGHTING_REPORT_ID}...")
            print(f"Buffer a enviar (hex): {' '.join(f'{x:02x}' for x in buffer)}")
          

        target_report.send(buffer)

        print("Comando de color enviado.")
        return True

    except Exception as e:
        print(f"Error al intentar establecer el color: {e}")
        # Imprimir más detalles si es un error de pywinusb
        if hasattr(e, 'winerror'):
            print(f"WinError: {e.winerror}")
        return False
    finally:
        # Asegurarse de que el dispositivo se cierra siempre
        if device and device.is_opened():
            device.close()
            #print("Dispositivo cerrado.") # Descomentar para depuración

# --- Función Principal ---

def main():
    """
    Función principal del script.
    Parsea argumentos, busca el teclado y establece el color.
    """
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(
        description="Controla la retroiluminación de un teclado Logitech G19.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Muestra valores por defecto
    )
    parser.add_argument(
        '--r', type=int, required=True, choices=range(0, 256), metavar='[0-255]',
        help="Componente Rojo del color."
    )
    parser.add_argument(
        '--g', type=int, required=True, choices=range(0, 256), metavar='[0-255]',
        help="Componente Verde del color."
    )
    parser.add_argument(
        '--b', type=int, required=True, choices=range(0, 256), metavar='[0-255]',
        help="Componente Azul del color."
    )
    parser.add_argument(
        '--inspect', action='store_true',
        help="Inspecciona los informes HID del dispositivo encontrado y sale. Útil para depuración."
    )

    # Parsear los argumentos de la línea de comandos
    args = parser.parse_args()

    print("Buscando teclado Logitech G19...")
    g19_device = find_g19()

    if g19_device:
        print("¡Teclado Logitech G19 encontrado!")

        if args.inspect:
            inspect_reports(g19_device)
            sys.exit(0) # Salir después de inspeccionar

        print(f"Intentando establecer color a R={args.r}, G={args.g}, B={args.b}...")
        success = set_color(g19_device, args.r, args.g, args.b)

        if success:
            print("Color configurado exitosamente.")
            sys.exit(0) # Éxito
        else:
            print("Falló la configuración del color.")
            sys.exit(1) # Error

    else:
        print("Teclado Logitech G19 no encontrado.")
        print("Asegúrate de que está conectado, encendido (con su adaptador de corriente si lo requiere) y que los drivers están instalados.")
        print("También verifica que los IDs de Vendedor/Producto (VID/PID) son correctos para tu modelo.")
        sys.exit(1) # Error

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()
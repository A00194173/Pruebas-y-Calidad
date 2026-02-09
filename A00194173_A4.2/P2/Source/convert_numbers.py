"""
Ejercicio de Programación 2: Conversión de números

Lee un archivo de texto con un elemento por línea (presumiblemente números)
y convierte cada número a:
- base binaria
- base hexadecimal

- Reporta errores de datos inválidos y continúa la ejecución.
- Imprime resultados en pantalla y guarda resultados en archivos individuales por caso de prueba.
- Reporta el tiempo total de ejecución.

Nota:
- Todas las conversiones se realizan con algoritmos básicos (divisiones sucesivas),
  sin usar funciones/librerías como bin(), hex(), format(), etc.
- Los renglones inválidos NO se descartan: se conservan y se muestran con #VALUE!
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List


ARCHIVO_RESULTADOS = "ConvertionResults.txt"
MARCADOR_INVALIDO = "#VALUE!"


@dataclass(frozen=True)
class DatosEntrada:
    """
    Agrupa los datos leídos del archivo de entrada.

    - Se conservan TODOS los renglones en la lista 'items' para mantener trazabilidad.
    - Si un renglón no es entero válido, se registra el error y ese renglón se mostrará
      con #VALUE! en BIN y HEX.
    """
    ruta_archivo: Path
    items: List[str]
    errores: List[str]


def leer_items(ruta_archivo: Path) -> DatosEntrada:
    """
    Lee el archivo de entrada línea por línea.

    Reglas:
    - Conserva todas las líneas (incluyendo inválidas), para que aparezcan en la salida.
    - Los errores se reportan en consola y la ejecución continúa.
    """
    items: List[str] = []
    errores: List[str] = []

    try:
        with ruta_archivo.open("r", encoding="utf-8") as archivo:
            for numero_linea, linea in enumerate(archivo, start=1):
                texto = linea.strip()

                # Conservamos el token aunque sea vacío; se tratará como inválido.
                items.append(texto)

                if texto == "":
                    errores.append(f"Línea {numero_linea}: línea vacía.")
                    continue

                # Valida si los números de entrada son enteros
                # para poder convertirlos con ops básicas
                try:
                    int(texto)
                except ValueError:
                    errores.append(f"Línea {numero_linea}: dato inválido '{texto}'.")

    except OSError as exc:
        raise OSError(f"No se pudo abrir el archivo '{ruta_archivo}': {exc}") from exc

    return DatosEntrada(ruta_archivo=ruta_archivo, items=items, errores=errores)


def invertir_cadena(s: str) -> str:
    """
    Invierte una cadena usando un proceso básico (sin slicing).
    """
    resultado = ""
    indice = len(s) - 1
    while indice >= 0:
        resultado += s[indice]
        indice -= 1
    return resultado


def convertir_base_positiva(valor: int, base: int, digitos: str) -> str:
    """
    Convierte un entero >= 0 a la base indicada usando divisiones sucesivas.
    """
    if valor == 0:
        return "0"

    resultado = ""
    n = valor
    while n > 0:
        residuo = n % base
        resultado += digitos[residuo]
        n = n // base

    return invertir_cadena(resultado)


def convertir_binario_token(token: str) -> str:
    """
    Convierte el token a BIN.

    - Si el token es inválido: #VALUE!
    - Si el número es negativo: complemento a dos en 10 bits (según resultados esperados).
    - Si es positivo: conversión normal.
    """

    x = token

    if x == "":
        return MARCADOR_INVALIDO

    try:
        numero = int(x)
    except ValueError:
        return MARCADOR_INVALIDO

    if numero >= 0:
        return convertir_base_positiva(numero, 2, "01")

    # Complemento a dos de 10 bits
    bits = 10
    valor_tc = (1 << bits) + numero
    binario = convertir_base_positiva(valor_tc, 2, "01")

    if len(binario) < bits:
        binario = ("0" * (bits - len(binario))) + binario

    return binario


def convertir_hex_token(token: str) -> str:
    """
    Convierte el token a HEX (mayúsculas).

    - Si el token es inválido: #VALUE!
    - Si el número es negativo: complemento a dos en 40 bits (10 dígitos hex).
    - Si es positivo: conversión normal.
    """
    digitos_hex = "0123456789ABCDEF"

    if token == "":
        return MARCADOR_INVALIDO

    try:
        numero = int(token)
    except ValueError:
        return MARCADOR_INVALIDO

    if numero >= 0:
        return convertir_base_positiva(numero, 16, digitos_hex)

    # Complemento a dos de 40 bits (10 dígitos hex)
    bits = 40
    valor_tc = (1 << bits) + numero
    hexa = convertir_base_positiva(valor_tc, 16, digitos_hex)

    if len(hexa) < 10:
        hexa = ("0" * (10 - len(hexa))) + hexa

    return hexa


def formatear_segundos(valor: float) -> str:
    """Formatea segundos con seis decimales."""
    return f"{valor:.6f}"


def construir_reporte(nombre_tc: str, items: List[str], invalidos: int, tiempo_seg: float) -> str:
    """
    Construye el texto del reporte con 4 columnas:

    1) ITEM: numerador consecutivo desde 1
    2) nombre_tc: columna con el valor original (tal cual viene en el archivo)
    3) BIN: conversión a binario
    4) HEX: conversión a hexadecimal
    """
    lineas: List[str] = []
    lineas.append(f"ITEM\t{nombre_tc}\tBIN\tHEX")

    contador = 0
    for token in items:
        contador += 1
        binario = convertir_binario_token(token)
        hexa = convertir_hex_token(token)
        lineas.append(f"{contador}\t{token}\t{binario}\t{hexa}")

    lineas.append("")
    lineas.append(f"Líneas inválidas detectadas: {invalidos}")
    lineas.append(f"Tiempo de ejecución (segundos): {formatear_segundos(tiempo_seg)}")

    return "\n".join(lineas) + "\n"


def guardar_resultados(texto_reporte: str, ruta_salida: Path) -> None:
    """Guarda el reporte en un archivo de texto."""
    ruta_salida.write_text(texto_reporte, encoding="utf-8")


def ruta_salida_por_tc(ruta_archivo_entrada: Path) -> Path:
    """
    Construye la ruta de salida en P2/Results usando el nombre del archivo de prueba.
    Ejemplo: TC1.txt -> ConvertionResultsTC1.txt
    """
    carpeta_results = Path(__file__).resolve().parent.parent / "Results"
    carpeta_results.mkdir(parents=True, exist_ok=True)

    sufijo_tc = ruta_archivo_entrada.stem  # TC1, TC2, ...
    nombre_base = ARCHIVO_RESULTADOS.replace(".txt", "")
    nombre_salida = f"{nombre_base}{sufijo_tc}.txt"

    return carpeta_results / nombre_salida


def ejecutar(ruta_archivo_entrada: Path) -> int:
    """
    Ejecuta el flujo principal del programa:
    lectura -> validación -> conversión -> reporte -> guardado.
    """
    inicio = time.perf_counter()

    try:
        entrada = leer_items(ruta_archivo_entrada)
    except OSError as exc:
        print(str(exc))
        return 2

    for mensaje in entrada.errores:
        print(f"ERROR: {mensaje}")

    ruta_resultados = ruta_salida_por_tc(ruta_archivo_entrada)

    tiempo = time.perf_counter() - inicio
    nombre_tc = ruta_archivo_entrada.stem
    invalidos = len(entrada.errores)

    texto_reporte = construir_reporte(nombre_tc, entrada.items, invalidos, tiempo)

    print(texto_reporte, end="")
    guardar_resultados(texto_reporte, ruta_resultados)
    print(f"Resultados guardados en: {ruta_resultados}")

    return 0


def main(argumentos: List[str]) -> int:
    """Valida argumentos y ejecuta el programa."""
    if len(argumentos) != 2:
        print("Uso correcto: python convert_numbers.py archivoConDatos.txt")
        return 1

    ruta_entrada = Path(argumentos[1]).expanduser()
    return ejecutar(ruta_entrada)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

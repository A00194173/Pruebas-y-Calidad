"""
Ejercicio de Programación 3: Conteo de palabras

Lee un archivo de texto y cuenta la frecuencia de cada palabra distinta.

- Reporta errores de datos inválidos y continúa la ejecución.
- Imprime resultados en pantalla y guarda resultados en archivos individuales por caso de prueba.
- Reporta el tiempo total de ejecución.

Nota:
- Todo se realiza con algoritmos básicos (sin Counter, sin regex).
- Las palabras se detectan como "tokens" separados por espacios/blancos, como indica el Req1
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


ARCHIVO_RESULTADOS = "WordCountResults.txt"


@dataclass(frozen=True)
class DatosEntrada:
    """
    Agrupa los datos leídos del archivo de entrada.

    - Se conservan los tokens detectados.
    - Se registran errores para tokens inválidos (por ejemplo vacíos o que
      después de limpiar quedan vacíos).
    """
    ruta_archivo: Path
    tokens: List[str]
    errores: List[str]


def leer_archivo_como_texto(ruta_archivo: Path) -> str:
    """Lee el archivo completo como texto."""
    try:
        return ruta_archivo.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"No se pudo abrir el archivo '{ruta_archivo}': {exc}") from exc


def tokenizar_por_espacios(texto: str) -> List[str]:
    """
    Separa el texto en tokens por espacios/blancos, usando un proceso básico
    (sin usar split()).
    """
    tokens: List[str] = []
    actual = ""

    for ch in texto:
        if ch in (" ", "\n", "\t", "\r"):
            if actual != "":
                tokens.append(actual)
                actual = ""
            else:
                # blanco consecutivo -> no agregamos token
                pass
        else:
            actual += ch

    if actual != "":
        tokens.append(actual)

    return tokens


def limpiar_token(token: str) -> str:
    """
    Normaliza un token para tratarlo como "palabra":

    - minúsculas
    - elimina signos comunes al inicio/fin (.,;:!? etc.)
    - conserva letras y números dentro de la palabra
    """
    signos = ".,;:!?\"'()[]{}<>/\\|@#$%^&*_+=~`"

    palabra = token.lower()

    # quitar signos al inicio
    while len(palabra) > 0 and palabra[0] in signos:
        palabra = palabra[1:]

    # quitar signos al final
    while len(palabra) > 0 and palabra[-1] in signos:
        palabra = palabra[:-1]

    return palabra

def leer_tokens(ruta_archivo: Path) -> DatosEntrada:
    """
    Lee el archivo y devuelve tokens + errores.
    """
    errores: List[str] = []

    texto = leer_archivo_como_texto(ruta_archivo)
    tokens_crudos = tokenizar_por_espacios(texto)

    tokens_limpios: List[str] = []
    for i, tok in enumerate(tokens_crudos, start=1):
        palabra = limpiar_token(tok)

        if palabra == "":
            errores.append(f"Token {i}: '{tok}' se considera inválido tras limpieza.")
            continue

        tokens_limpios.append(palabra)

    return DatosEntrada(ruta_archivo=ruta_archivo, tokens=tokens_limpios, errores=errores)


def contar_frecuencias(tokens: List[str]) -> Dict[str, int]:
    """Cuenta frecuencias."""
    conteos: Dict[str, int] = {}
    for palabra in tokens:
        if palabra in conteos:
            conteos[palabra] += 1
        else:
            conteos[palabra] = 1
    return conteos


def ordenar_resultados(conteos: Dict[str, int]) -> List[Tuple[str, int]]:
    """
    Ordena resultados de manera ascendente por palabra 
    """
    pares = list(conteos.items())
    pares.sort(key=lambda t: t[0])
    return pares


def formatear_segundos(valor: float) -> str:
    """Formatea segundos con seis decimales."""
    return f"{valor:.6f}"


def construir_reporte(nombre_tc: str,
                      resultados: List[Tuple[str, int]],
                      invalidos: int,
                      tiempo_seg: float,
                      tokens_validos: int
                     ) -> str:
    """
    Construye el reporte con dos columnas: Label y Count.
    """
    lineas: List[str] = []
    lineas.append(f"Label\tCount ({nombre_tc})")

    for palabra, count in resultados:
        lineas.append(f"{palabra}\t{count}")

    lineas.append("")
    lineas.append(f"Palabras distintas: {len(resultados)}")
    lineas.append(f"Tokens válidos: {tokens_validos}")
    lineas.append(f"Tokens inválidos detectados: {invalidos}")
    lineas.append(f"Tiempo de ejecución (segundos): {formatear_segundos(tiempo_seg)}")

    return "\n".join(lineas) + "\n"


def guardar_resultados(texto_reporte: str, ruta_salida: Path) -> None:
    """Guarda el reporte en un archivo de texto."""
    ruta_salida.write_text(texto_reporte, encoding="utf-8")


def ruta_salida_por_tc(ruta_archivo_entrada: Path) -> Path:
    """
    Construye la ruta de salida en P3/Results usando el nombre del archivo de prueba.
    Ejemplo: TC1.txt -> WordCountResultsTC1.txt
    """
    carpeta_results = Path(__file__).resolve().parent.parent / "Results"
    carpeta_results.mkdir(parents=True, exist_ok=True)

    sufijo_tc = ruta_archivo_entrada.stem  # TC1, TC2, ...
    nombre_base = ARCHIVO_RESULTADOS.replace(".txt", "")
    nombre_salida = f"{nombre_base}{sufijo_tc}.txt"

    return carpeta_results / nombre_salida


def ejecutar(ruta_archivo_entrada: Path) -> int:
    """
    Flujo principal:
    lectura -> tokenización -> limpieza -> conteo -> orden -> reporte -> guardado.
    """
    inicio = time.perf_counter()

    try:
        entrada = leer_tokens(ruta_archivo_entrada)
    except OSError as exc:
        print(str(exc))
        return 2

    for mensaje in entrada.errores:
        print(f"ERROR: {mensaje}")

    conteos = contar_frecuencias(entrada.tokens)
    resultados_ordenados = ordenar_resultados(conteos)

    tiempo = time.perf_counter() - inicio
    nombre_tc = ruta_archivo_entrada.stem
    invalidos = len(entrada.errores)

    ruta_resultados = ruta_salida_por_tc(ruta_archivo_entrada)
    tokens_validos = len(entrada.tokens)
    texto_reporte = construir_reporte(nombre_tc, 
                                      resultados_ordenados, 
                                      invalidos, 
                                      tiempo,
                                      tokens_validos
                                     )

    print(texto_reporte, end="")
    guardar_resultados(texto_reporte, ruta_resultados)
    print(f"Resultados guardados en: {ruta_resultados}")

    return 0


def main(argumentos: List[str]) -> int:
    """Valida argumentos y ejecuta el programa."""
    if len(argumentos) != 2:
        print("Uso correcto: python word_count.py archivoConDatos.txt")
        return 1

    ruta_entrada = Path(argumentos[1]).expanduser()
    return ejecutar(ruta_entrada)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

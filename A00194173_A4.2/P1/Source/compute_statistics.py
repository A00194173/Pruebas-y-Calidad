"""
Ejercicio de Programación 1: Cálculo de estadísticas (versión refactorizada)

Lee un archivo de texto con un elemento por línea (presumiblemente números)
y calcula estadísticas descriptivas usando algoritmos básicos:
media, mediana, moda, varianza (poblacional) y desviación estándar (poblacional).

- Reporta errores de datos inválidos y continúa la ejecución.
- Imprime resultados en pantalla y guarda resultados en archivos individuales por caso de prueba.
- Reporta el tiempo total de ejecución.

Nota:
- Se calcula VARIANZA POBLACIONAL (división entre N)
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


ARCHIVO_RESULTADOS = "StatisticsResults.txt"


@dataclass(frozen=True)
class DatosEntrada:
    """Agrupa los datos leídos del archivo de entrada."""
    ruta_archivo: Path
    numeros: List[float]
    errores: List[str]


@dataclass(frozen=True)
class Estadisticas:
    """Agrupa las estadísticas calculadas."""
    media: float
    mediana: float
    modas: List[float]
    varianza_poblacional: float
    desviacion_estandar_poblacional: float


@dataclass(frozen=True)
class Reporte:
    """Agrupa todo lo necesario para construir un reporte."""
    archivo_entrada: Path
    total_items_leidos: int
    cantidad_validos: int
    cantidad_invalidos: int
    estadisticas: Estadisticas
    tiempo_segundos: float


def leer_numeros(ruta_archivo: Path) -> DatosEntrada:
    """
    Lee números desde un archivo de texto (un elemento por línea).

    Regresa una estructura con:
    - números válidos
    - lista de mensajes de error para datos inválidos
    """
    numeros: List[float] = []
    errores: List[str] = []

    try:
        with ruta_archivo.open("r", encoding="utf-8") as archivo:
            for numero_linea, linea in enumerate(archivo, start=1):
                texto = linea.strip()

                if not texto:
                    errores.append(f"Línea {numero_linea}: línea vacía (ignorada).")
                    continue

                try:
                    numeros.append(float(texto))
                except ValueError:
                    errores.append(
                        f"Línea {numero_linea}: dato inválido '{texto}' (ignorado)."
                    )
    except OSError as exc:
        raise OSError(f"No se pudo abrir el archivo '{ruta_archivo}': {exc}") from exc

    return DatosEntrada(ruta_archivo=ruta_archivo, numeros=numeros, errores=errores)


def calcular_media(valores: List[float]) -> float:
    """Calcula la media aritmética usando un algoritmo básico."""
    suma = 0.0
    contador = 0
    for valor in valores:
        suma += valor
        contador += 1
    return suma / contador


def calcular_mediana(valores_ordenados: List[float]) -> float:
    """Calcula la mediana a partir de una lista previamente ordenada."""
    cantidad = len(valores_ordenados)
    mitad = cantidad // 2

    if cantidad % 2 == 1:
        return valores_ordenados[mitad]

    return (valores_ordenados[mitad - 1] + valores_ordenados[mitad]) / 2.0


def calcular_frecuencias(valores: List[float]) -> Dict[float, int]:
    """Calcula la frecuencia de aparición de cada valor."""
    frecuencias: Dict[float, int] = {}
    for valor in valores:
        frecuencias[valor] = frecuencias.get(valor, 0) + 1
    return frecuencias


def calcular_moda(valores: List[float]) -> List[float]:
    """
    Calcula la moda.

    Si existe empate en la frecuencia máxima, se reporta SOLO una moda:
    la primera que aparece en el archivo/entrada.
    Si todos los valores aparecen una sola vez, no hay moda.
    """
    frecuencias = calcular_frecuencias(valores)

    frecuencia_maxima = 0
    for frecuencia in frecuencias.values():
        frecuencia_maxima = max(frecuencia_maxima, frecuencia)

    if frecuencia_maxima <= 1:
        return []

    # Empate: elegir la primera que aparece en la entrada
    for valor in valores:
        if frecuencias[valor] == frecuencia_maxima:
            return [valor]

    return []


def calcular_varianza_poblacional(valores: List[float], media: float) -> float:
    """
    Calcula la varianza poblacional usando un algoritmo básico.

    NOTA:
    - Se utiliza la definición de varianza poblacional.
    - La suma de los cuadrados de las diferencias se divide entre N.
    - No se utiliza la corrección de Bessel (N - 1).
    """
    cantidad = len(valores)
    suma_cuadrados = 0.0

    for valor in valores:
        diferencia = valor - media
        suma_cuadrados += diferencia * diferencia

    return suma_cuadrados / cantidad


def calcular_estadisticas(numeros: List[float]) -> Estadisticas:
    """Calcula todas las estadísticas requeridas usando algoritmos básicos."""
    numeros_ordenados = sorted(numeros)

    media = calcular_media(numeros)
    mediana = calcular_mediana(numeros_ordenados)
    modas = calcular_moda(numeros)

    # Se calcula la varianza poblacional (división entre N)
    varianza_poblacional = calcular_varianza_poblacional(numeros, media)
    desviacion_poblacional = math.sqrt(varianza_poblacional)

    return Estadisticas(
        media=media,
        mediana=mediana,
        modas=modas,
        varianza_poblacional=varianza_poblacional,
        desviacion_estandar_poblacional=desviacion_poblacional,
    )


def formatear_numero(valor: float) -> str:
    """Formatea números con seis decimales."""
    return f"{valor:.6f}"


def construir_reporte(reporte: Reporte) -> str:
    """Construye el texto del reporte de resultados."""
    estad = reporte.estadisticas
    texto_modas = (
        "NA"
        if not estad.modas
        else ", ".join(formatear_numero(moda) for moda in estad.modas)
    )

    lineas = [
        "Resultados del cálculo de estadísticas",
        "-------------------------------------",
        f"Archivo de entrada: {reporte.archivo_entrada}",
        f"Total de elementos leídos: {reporte.total_items_leidos}",
        f"Números válidos: {reporte.cantidad_validos}",
        f"Datos inválidos: {reporte.cantidad_invalidos}",
        "",
        "Estadísticas descriptivas:",
        f"Media: {formatear_numero(estad.media)}",
        f"Mediana: {formatear_numero(estad.mediana)}",
        f"Moda(s): {texto_modas}",
        (
            "Desviación estándar (poblacional): "
            f"{formatear_numero(estad.desviacion_estandar_poblacional)}"
        ),
        f"Varianza (poblacional): {formatear_numero(estad.varianza_poblacional)}",
        "",
        f"Tiempo de ejecución (segundos): {formatear_numero(reporte.tiempo_segundos)}",
    ]
    return "\n".join(lineas) + "\n"


def guardar_resultados(texto_reporte: str, ruta_salida: Path) -> None:
    """Guarda el reporte en un archivo de texto."""
    ruta_salida.write_text(texto_reporte, encoding="utf-8")


def ruta_salida_por_tc(ruta_archivo_entrada: Path) -> Path:
    """
    Construye la ruta de salida en P1/Results usando el nombre del archivo de prueba.
    Ejemplo: TC1.txt -> StatisticsResultsTC1.txt
    """
    # __file__ apunta a .../P1/Source/compute_statistics.py
    # Results está en .../P1/Results/
    carpeta_results = Path(__file__).resolve().parent.parent / "Results"
    carpeta_results.mkdir(parents=True, exist_ok=True)

    sufijo_tc = ruta_archivo_entrada.stem  # TC1, TC2, ...
    nombre_salida = f"{ARCHIVO_RESULTADOS.replace('.txt', '')}{sufijo_tc}.txt"
    return carpeta_results / nombre_salida


def ejecutar(ruta_archivo_entrada: Path) -> int:
    """
    Ejecuta el flujo principal del programa:
    lectura -> validación -> cálculo -> reporte -> guardado.
    """
    inicio = time.perf_counter()

    try:
        entrada = leer_numeros(ruta_archivo_entrada)
    except OSError as exc:
        print(str(exc))
        return 2

    for mensaje in entrada.errores:
        print(f"ERROR: {mensaje}")

    ruta_resultados = ruta_salida_por_tc(ruta_archivo_entrada)

    if not entrada.numeros:
        tiempo = time.perf_counter() - inicio
        print("No se encontraron datos numéricos válidos.")
        print(f"Tiempo de ejecución (segundos): {formatear_numero(tiempo)}")

        texto = (
            "No se encontraron datos numéricos válidos.\n"
            f"Archivo de entrada: {ruta_archivo_entrada}\n"
            f"Tiempo de ejecución (segundos): {formatear_numero(tiempo)}\n"
        )
        guardar_resultados(texto, ruta_resultados)
        print(f"Resultados guardados en: {ruta_resultados}")
        return 3

    estadisticas = calcular_estadisticas(entrada.numeros)
    tiempo = time.perf_counter() - inicio

    total_items = len(entrada.numeros) + len(entrada.errores)
    reporte = Reporte(
        archivo_entrada=entrada.ruta_archivo,
        total_items_leidos=total_items,
        cantidad_validos=len(entrada.numeros),
        cantidad_invalidos=len(entrada.errores),
        estadisticas=estadisticas,
        tiempo_segundos=tiempo,
    )

    texto_reporte = construir_reporte(reporte)

    print(texto_reporte, end="")

    guardar_resultados(texto_reporte, ruta_resultados)
    print(f"Resultados guardados en: {ruta_resultados}")

    return 0


def main(argumentos: List[str]) -> int:
    """Valida argumentos y ejecuta el programa."""
    if len(argumentos) != 2:
        print("Uso correcto: python compute_statistics.py archivoConDatos.txt")
        return 1

    ruta_entrada = Path(argumentos[1]).expanduser()
    return ejecutar(ruta_entrada)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

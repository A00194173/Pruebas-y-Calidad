"""
Programa: Cálculo de ventas (compute_sales.py)

Recibe dos archivos JSON:
1) Catálogo de productos con precios (title, price)
2) Registro de ventas (Product, Quantity)

Relaciona por la llave (en cada archivo):
- Catálogo: title
- Ventas: Product

Calcula el total de ventas sumando price * Quantity por renglón válido.

Manejo de errores:
- Si un renglón de ventas trae Quantity negativa ->
  se considera devolución y SI se suma como negativo
- Si un producto no existe en el catálogo -> inválido y NO se suma
- Si hay campos faltantes o tipos inválidos -> inválido y NO se suma
- El programa continúa con el resto de renglones

Salida:
- Imprime el reporte en consola
- Guarda el reporte en Results/ como SalesResults<TC>.txt
  usando el TC del archivo de ventas.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List  # , Tuple


ARCHIVO_RESULTADOS = "SalesResults.txt"


@dataclass(frozen=True)
class DatosCatalogo:
    """
    Representa el catálogo de productos.

    Contiene:
    - ruta_archivo: archivo origen
    - precios_por_titulo: diccionario title -> price
    - errores: lista de errores detectados
    """
    ruta_archivo: Path
    precios_por_titulo: Dict[str, float]
    errores: List[str]


@dataclass(frozen=True)
class DatosVentas:
    """
    Representa el archivo de ventas.

    Contiene:
    - ruta_archivo: archivo origen
    - registros: lista de registros JSON válidos
    - errores: lista de errores estructurales detectados
    """
    ruta_archivo: Path
    registros: List[Dict[str, Any]]
    errores: List[str]


@dataclass(frozen=True)
class ResultadoCalculo:
    """Agrupa el resultado del cálculo del total de ventas."""
    total: float
    validas: int
    invalidas: int
    devoluciones: int
    errores: List[str]


@dataclass(frozen=True)
class ReporteVentas:
    """Agrupa los datos necesarios para generar el reporte final."""
    total: float
    total_lineas: int
    validas: int
    invalidas: int
    devoluciones: int
    tiempo_seg: float


def imprimir_errores(errores: List[str]) -> None:
    """Imprime en consola una lista de errores."""
    for msg in errores:
        print(f"ERROR: {msg}")


def leer_json(ruta: Path) -> Any:
    """Lee un JSON desde disco y devuelve la estructura parseada."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"No se pudo abrir el archivo '{ruta}': {exc}") from exc

    try:
        return json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ValueError(f"El archivo '{ruta}' "
                         f"no es JSON válido: {exc}") from exc


def cargar_catalogo(ruta_catalogo: Path) -> DatosCatalogo:
    """
    Carga el catálogo y construye un diccionario title -> price.
    Registra errores por registros inválidos y continúa.
    """
    errores: List[str] = []
    precios: Dict[str, float] = {}

    data = leer_json(ruta_catalogo)
    if not isinstance(data, list):
        raise ValueError("El catálogo debe ser una"
                         " lista de objetos JSON (arreglo).")

    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errores.append(f"Catálogo renglón {idx}: no es un objeto JSON.")
            continue

        title = item.get("title")
        price = item.get("price")

        if not isinstance(title, str) or title.strip() == "":
            errores.append(f"Catálogo renglón {idx}: "
                           "title faltante o inválido.")
            continue

        # precio debe ser numérico y >= 0
        try:
            precio_float = float(price)
        except (TypeError, ValueError):
            errores.append(f"Catálogo renglón {idx}: "
                           f"price inválido para '{title}'.")
            continue

        if precio_float < 0:
            errores.append(f"Catálogo renglón {idx}: "
                           f"price negativo para '{title}'.")
            continue

        # si se repite el título, nos quedamos con el último (y lo reportamos)
        if title in precios:
            errores.append(f"Catálogo renglón {idx}: "
                           f"title duplicado '{title}'.")

        precios[title] = precio_float

    return DatosCatalogo(ruta_archivo=ruta_catalogo,
                         precios_por_titulo=precios,
                         errores=errores)


def cargar_ventas(ruta_ventas: Path) -> DatosVentas:
    """
    Carga el archivo de ventas como lista de registros.
    Registra errores estructurales por renglón y continúa.
    """
    errores: List[str] = []
    data = leer_json(ruta_ventas)

    if not isinstance(data, list):
        raise ValueError("El archivo de ventas debe ser"
                         " una lista de objetos JSON (arreglo).")

    registros: List[Dict[str, Any]] = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errores.append(f"Ventas renglón {i}: no es un objeto JSON.")
            continue
        registros.append(item)

    return DatosVentas(ruta_archivo=ruta_ventas,
                       registros=registros,
                       errores=errores)


def _tc_desde_archivo_ventas(ruta_ventas: Path) -> str:
    """
    Extrae el TC desde el nombre del archivo de ventas.
    Ejemplos:
      TC1.Sales.json -> TC1
      TC2.Sales.json -> TC2
    """
    nombre = ruta_ventas.name
    if "." in nombre:
        return nombre.split(".", maxsplit=1)[0]
    return ruta_ventas.stem


def ruta_salida_por_tc(ruta_archivo_ventas: Path) -> Path:
    """
    Construye la ruta de salida en Results/ usando el TC del archivo de ventas.
    Ejemplo: TC1.Sales.json -> SalesResultsTC1.txt
    """
    carpeta_results = Path(__file__).resolve().parent.parent / "Results"
    carpeta_results.mkdir(parents=True, exist_ok=True)

    tc = _tc_desde_archivo_ventas(ruta_archivo_ventas)
    nombre_base = ARCHIVO_RESULTADOS.replace(".txt", "")
    nombre_salida = f"{nombre_base}{tc}.txt"

    return carpeta_results / nombre_salida


def calcular_total_ventas(precios_por_titulo: Dict[str, float],
                          ventas: List[Dict[str, Any]]) -> ResultadoCalculo:
    """
    Calcula el total de ventas recorriendo cada renglón.

    Regresa:
    - total
    - cantidad_validas
    - cantidad_invalidas
    - cantidad de devoluciones
    - lista de mensajes de error
    """
    errores: List[str] = []
    total = 0.0
    validas = 0
    invalidas = 0
    devoluciones = 0

    for idx, registro in enumerate(ventas, start=1):
        producto = registro.get("Product")
        quantity = registro.get("Quantity")

        if not isinstance(producto, str) or producto.strip() == "":
            errores.append(f"Ventas renglón {idx}: "
                           f"Product faltante o inválido.")
            invalidas += 1
            continue

        # Quantity debe ser entero (sin decimales)
        try:
            cantidad_int = int(quantity)
        except (TypeError, ValueError):
            errores.append(f"Ventas renglón {idx}: "
                           f"Quantity inválido para '{producto}'.")
            invalidas += 1
            continue

        if str(quantity) != str(cantidad_int) and not isinstance(quantity,
                                                                 int):
            # si venía como '3.0' o float 3.0,
            # lo consideramos inválido (para mantener enteros puros)
            errores.append(f"Ventas renglón {idx}: "
                           f"Quantity no entero para '{producto}'.")
            invalidas += 1
            continue

        if cantidad_int < 0:
            # Devolución: es válida y se suma tal cual (resta al total)
            devoluciones += 1

        if producto not in precios_por_titulo:
            errores.append(
                f"Ventas renglón {idx}: Producto '{producto}' "
                "no existe en el catálogo.")
            invalidas += 1
            continue

        precio = precios_por_titulo[producto]
        total += precio * cantidad_int
        validas += 1

    return ResultadoCalculo(
        total=total,
        validas=validas,
        invalidas=invalidas,
        devoluciones=devoluciones,
        errores=errores)


def formatear_segundos(valor: float) -> str:
    """Formatea un valor en segundos con seis decimales."""
    return f"{valor:.6f}"


def construir_reporte(reporte: ReporteVentas) -> str:
    """
    Construye el reporte final con:
    - total de ventas
    - líneas leídas
    - válidas
    - inválidas
    - devoluciones
    - tiempo de ejecución
    """
    lineas = []
    lineas.append(f"Total de ventas: {reporte.total:.2f}")
    lineas.append(f"Líneas leídas: {reporte.total_lineas}")
    lineas.append(f"Ventas válidas: {reporte.validas}")
    lineas.append(f"Ventas inválidas: {reporte.invalidas}")
    lineas.append(f"Devoluciones: {reporte.devoluciones}")
    lineas.append("Tiempo de ejecución (segundos): "
                  f"{formatear_segundos(reporte.tiempo_seg)}")
    return "\n".join(lineas) + "\n"


def guardar_resultados(texto: str, ruta_salida: Path) -> None:
    """Guarda el texto del reporte en el archivo indicado."""
    ruta_salida.write_text(texto, encoding="utf-8")


def ejecutar(ruta_catalogo: Path, ruta_ventas: Path) -> int:
    """
    Flujo principal:
    cargar catálogo -> cargar ventas -> calcular total -> reporte -> guardar.
    """
    inicio = time.perf_counter()

    try:
        catalogo = cargar_catalogo(ruta_catalogo)
    except (OSError, ValueError) as exc:
        print(str(exc))
        return 2

    try:
        ventas = cargar_ventas(ruta_ventas)
    except (OSError, ValueError) as exc:
        print(str(exc))
        return 2

    imprimir_errores(catalogo.errores)
    imprimir_errores(ventas.errores)

    resultado = calcular_total_ventas(
        catalogo.precios_por_titulo, ventas.registros)

    imprimir_errores(resultado.errores)

    tiempo = time.perf_counter() - inicio
    invalidas_total = resultado.invalidas + len(ventas.errores)
    total_lineas = len(ventas.registros) + len(ventas.errores)

    reporte = ReporteVentas(
        total=resultado.total,
        total_lineas=total_lineas,
        validas=resultado.validas,
        invalidas=invalidas_total,
        devoluciones=resultado.devoluciones,
        tiempo_seg=tiempo,
    )

    texto_reporte = construir_reporte(reporte)
    print(texto_reporte, end="")

    ruta_salida = ruta_salida_por_tc(ruta_ventas)
    guardar_resultados(texto_reporte, ruta_salida)
    print(f"Resultados guardados en: {ruta_salida}")

    return 0


def main(argv: List[str]) -> int:
    """
    Valida los argumentos de línea de comandos y ejecuta el programa.
    """
    if len(argv) != 3:
        print("Uso correcto: python compute_sales.py priceCatalogue.json "
              "salesRecord.json")
        return 1

    ruta_catalogo = Path(argv[1]).expanduser()
    ruta_ventas = Path(argv[2]).expanduser()
    return ejecutar(ruta_catalogo, ruta_ventas)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

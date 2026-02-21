"""
Persistencia en archivos: load/save + CRUD + manejo de inválidos (Req 2, Req 5)

Capa de persistencia "file-based" para el Sistema de Reservaciones de Hotel.

Responsabilidades:
- Inicializar Results/Store/ y archivos JSON si no existen
- Leer/escribir JSON de forma robusta (continuar ante errores)
- CRUD de Hotels y Customers
- Create/Cancel/Get de Reservations

Requerimiento 5:
- Si hay datos inválidos o JSON corrupto, reporta en consola y la ejecución continúa
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from Source.models import Customer, Hotel, Reservation


_FILES = {
    "hotels": "hotels.json",
    "customers": "customers.json",
    "reservations": "reservations.json",
}

_REQUIRED_KEYS = {
    "hotels": ["hotel_id", "name", "location", "rooms_total", "rooms_available"],
    "customers": ["customer_id", "name", "email"],
    "reservations": ["reservation_id", "hotel_id", "customer_id", "status"],
}

_STATUS_ALLOWED = {"active", "cancelled"}


def get_store_dir() -> Path:
    """
    Obtiene el directorio base donde se almacenan los archivos persistentes

    Se puede sobreescribir con la variable de entorno A6_STORE_DIR (útil en pruebas)

    Returns:
        Path: Ruta al directorio del store
    """
    override = os.getenv("A6_STORE_DIR", "").strip()
    if override:
        return Path(override)

    # Calcula ruta por defecto en función de la ubicación del proyecto:
    # .../A00194173_A6.2/Source/storage.py -> .../A00194173_A6.2/Results/Store
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "Results" / "Store"


def _store_file(entity_name: str) -> Path:
    """
    Construye la ruta del archivo JSON correspondiente a una entidad

    Args:
        entity_name (str): Nombre lógico de entidad ("hotels", "customers", "reservations")

    Returns:
        Path: Ruta completa del archivo JSON
    """
    return get_store_dir() / _FILES[entity_name]


def ensure_store() -> None:
    """
    Inicializa el almacenamiento persistente

    - Crea el directorio Results/Store si no existe
    - Crea los 3 archivos JSON con contenido [] si no existen

    Política Req 5:
    - Si ocurre un error de IO, se reporta en consola y el programa continúa
    """
    store_dir = get_store_dir()
    try:
        store_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[storage] Error creando directorio store: {exc}")

    for entity in _FILES:
        path = _store_file(entity)
        if not path.exists():
            try:
                path.write_text("[]", encoding="utf-8")
            except OSError as exc:
                print(f"[storage] Error creando archivo {path.name}: {exc}")


def _is_dict(value: Any) -> bool:
    """
    Determina si un valor es un diccionario

    Args:
        value (Any): Valor a evaluar

    Returns:
        bool: True si es dict, False en caso contrario
    """
    return isinstance(value, dict)


def _has_required_keys(record: dict[str, Any], required: list[str]) -> bool:
    """
    Verifica si un registro contiene todas las llaves requeridas

    Args:
        record (dict): Registro a validar.
        required (list[str]): Lista de llaves obligatorias

    Returns:
        bool: True si contiene todas las llaves, False si falta alguna
    """
    for k in required:
        if k not in record:
            return False
    return True


def _validate_record(entity_name: str, record: dict[str, Any]) -> tuple[bool, str]:
    """
    Valida un registro a nivel estructural

    Nota:
    - No valida reglas cruzadas entre archivos (eso se gestiona en app.py)

    Args:
        entity_name (str): Entidad a la que corresponde el registro
        record (dict[str, Any]): Registro a validar

    Returns:
        tuple[bool, str]: (es_valido, motivo_si_invalido)
    """
    required = _REQUIRED_KEYS.get(entity_name, [])
    if not _has_required_keys(record, required):
        return False, "faltan llaves requeridas"

    if entity_name == "hotels":
        if not isinstance(record.get("rooms_total"), int) and not str(
            record.get("rooms_total")
        ).isdigit():
            return False, "rooms_total no es entero"
        if not isinstance(record.get("rooms_available"), int) and not str(
            record.get("rooms_available")
        ).isdigit():
            return False, "rooms_available no es entero"

    if entity_name == "reservations":
        status = record.get("status")
        if isinstance(status, str) and status not in _STATUS_ALLOWED:
            return False, "status inválido"

    return True, ""


def load_list(entity_name: str) -> list[dict[str, Any]]:
    """
    Carga una lista de registros (lista de dicts) desde el JSON de una entidad

    Política Req 5:
    - JSON corrupto -> reporta y retorna []
    - Raíz no lista -> reporta y retorna []
    - Registro inválido -> reporta, lo ignora y continúa

    Args:
        entity_name (str): "hotels" | "customers" | "reservations"

    Returns:
        list[dict[str, Any]]: Lista de registros saneada
    """
    ensure_store()
    path = _store_file(entity_name)

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[storage] Error al leer {path.name}: {exc}. Se usará lista vacía.")
        return []

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"[storage] Error al leer {path.name}: JSON inválido. Se usará lista vacía.")
        return []
    except TypeError as exc:
        print(f"[storage] Error al leer {path.name}: {exc}. Se usará lista vacía.")
        return []

    if not isinstance(data, list):
        print(
            f"[storage] Error al leer {path.name}: se esperaba lista. Se usará lista vacía."
        )
        return []

    cleaned: list[dict[str, Any]] = []
    invalid_count = 0

    for idx, item in enumerate(data):
        if not _is_dict(item):
            invalid_count += 1
            print(
                f"[storage] {entity_name}: registro inválido ignorado en índice {idx} "
                "(no es objeto)"
            )
            continue

        ok, reason = _validate_record(entity_name, item)
        if not ok:
            invalid_count += 1
            print(
                f"[storage] {entity_name}: registro inválido ignorado en índice {idx} "
                f"({reason})"
            )
            continue

        cleaned.append(item)

    if invalid_count > 0:
        print(f"[storage] {entity_name}: {invalid_count} registros inválidos ignorados")

    return cleaned


def save_list(entity_name: str, records: list[dict[str, Any]]) -> None:
    """
    Guarda una lista de registros al archivo JSON correspondiente

    Política Req 5:
    - Si hay error de escritura, se reporta en consola y la ejecución continúa

    Args:
        entity_name (str): "hotels" | "customers" | "reservations"
        records (list[dict[str, Any]]): Registros a persistir.
    """
    ensure_store()
    path = _store_file(entity_name)
    try:
        path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        print(f"[storage] Error al escribir {path.name}: {exc}")


def _find_index(records: list[dict[str, Any]], key_name: str, key_value: str) -> int:
    """
    Busca el índice de un registro en una lista por llave

    Args:
        records (list[dict]): Lista de registros
        key_name (str): Nombre de la llave (ej. "hotel_id")
        key_value (str): Valor a buscar

    Returns:
        int: Índice si existe; -1 si no se encuentra
    """
    for i, r in enumerate(records):
        if str(r.get(key_name, "")) == key_value:
            return i
    return -1


# --------------------------
# Hotels
# --------------------------


def create_hotel(hotel: Hotel) -> None:
    """
    Crea un hotel persistiendo su registro en hotels.json

    Si el hotel_id ya existe, reporta el error y no modifica el archivo

    Args:
        hotel (Hotel): Instancia del hotel a guardar
    """
    records = load_list("hotels")
    idx = _find_index(records, "hotel_id", hotel.hotel_id)
    if idx != -1:
        print(f"[storage] hotels: hotel_id duplicado: {hotel.hotel_id}. Se ignora create.")
        return
    records.append(hotel.to_dict())
    save_list("hotels", records)


def get_hotel(hotel_id: str) -> Hotel | None:
    """
    Obtiene un hotel por hotel_id desde hotels.json

    Args:
        hotel_id (str): Identificador del hotel

    Returns:
        Hotel | None: Hotel si existe y es válido; None si no existe o hay error
    """
    records = load_list("hotels")
    idx = _find_index(records, "hotel_id", hotel_id)
    if idx == -1:
        return None
    try:
        return Hotel.from_dict(records[idx])
    except (KeyError, TypeError, ValueError) as exc:
        print(f"[storage] hotels: error al construir Hotel desde dict: {exc}")
        return None


def update_hotel(hotel: Hotel) -> None:
    """
    Actualiza un hotel existente por hotel_id

    Si no existe, reporta y no modifica el archivo

    Args:
        hotel (Hotel): Instancia con datos actualizados
    """
    records = load_list("hotels")
    idx = _find_index(records, "hotel_id", hotel.hotel_id)
    if idx == -1:
        print(f"[storage] hotels: no existe hotel_id {hotel.hotel_id}. Se ignora update.")
        return
    records[idx] = hotel.to_dict()
    save_list("hotels", records)


def delete_hotel(hotel_id: str) -> None:
    """
    Elimina físicamente un hotel de hotels.json

    Si no existe, reporta y no modifica el archivo

    Args:
        hotel_id (str): Identificador del hotel a eliminar
    """
    records = load_list("hotels")
    idx = _find_index(records, "hotel_id", hotel_id)
    if idx == -1:
        print(f"[storage] hotels: no existe hotel_id {hotel_id}. Se ignora delete.")
        return
    del records[idx]
    save_list("hotels", records)


# --------------------------
# Customers
# --------------------------


def create_customer(customer: Customer) -> None:
    """
    Crea un cliente persistiendo su registro en customers.json

    Si customer_id ya existe, reporta el error y no modifica el archivo

    Args:
        customer (Customer): Instancia del cliente
    """
    records = load_list("customers")
    idx = _find_index(records, "customer_id", customer.customer_id)
    if idx != -1:
        print(
            f"[storage] customers: customer_id duplicado: {customer.customer_id}. "
            "Se ignora create."
        )
        return
    records.append(customer.to_dict())
    save_list("customers", records)


def get_customer(customer_id: str) -> Customer | None:
    """
    Obtiene un cliente por customer_id desde customers.json

    Args:
        customer_id (str): Identificador del cliente

    Returns:
        Customer | None: Cliente si existe y es válido; None si no existe o hay error
    """
    records = load_list("customers")
    idx = _find_index(records, "customer_id", customer_id)
    if idx == -1:
        return None
    try:
        return Customer.from_dict(records[idx])
    except (KeyError, TypeError, ValueError) as exc:
        print(f"[storage] customers: error al construir Customer desde dict: {exc}")
        return None


def update_customer(customer: Customer) -> None:
    """
    Actualiza un cliente existente por customer_id

    Si no existe, reporta y no modifica el archivo

    Args:
        customer (Customer): Instancia con datos actualizados
    """
    records = load_list("customers")
    idx = _find_index(records, "customer_id", customer.customer_id)
    if idx == -1:
        print(
            f"[storage] customers: no existe customer_id {customer.customer_id}. "
            "Se ignora update."
        )
        return
    records[idx] = customer.to_dict()
    save_list("customers", records)


def delete_customer(customer_id: str) -> None:
    """
    Elimina físicamente un cliente de customers.json

    Si no existe, reporta y no modifica el archivo

    Args:
        customer_id (str): Identificador del cliente a eliminar
    """
    records = load_list("customers")
    idx = _find_index(records, "customer_id", customer_id)
    if idx == -1:
        print(f"[storage] customers: no existe customer_id {customer_id}. Se ignora delete.")
        return
    del records[idx]
    save_list("customers", records)


# --------------------------
# Reservations
# --------------------------


def create_reservation(reservation: Reservation) -> None:
    """
    Crea una reservación persistiendo su registro en reservations.json

    Si reservation_id ya existe, reporta y no modifica el archivo

    Args:
        reservation (Reservation): Reservación a persistir
    """
    records = load_list("reservations")
    idx = _find_index(records, "reservation_id", reservation.reservation_id)
    if idx != -1:
        print(
            f"[storage] reservations: reservation_id duplicado: {reservation.reservation_id}. "
            "Se ignora create."
        )
        return
    records.append(reservation.to_dict())
    save_list("reservations", records)


def get_reservation(reservation_id: str) -> Reservation | None:
    """
    Obtiene una reservación por reservation_id desde reservations.json

    Args:
        reservation_id (str): Identificador de la reservación

    Returns:
        Reservation | None: Reservación si existe y es válida; None si no existe o hay error
    """
    records = load_list("reservations")
    idx = _find_index(records, "reservation_id", reservation_id)
    if idx == -1:
        return None
    try:
        return Reservation.from_dict(records[idx])
    except (KeyError, TypeError, ValueError) as exc:
        print(f"[storage] reservations: error al construir Reservation desde dict: {exc}")
        return None


def cancel_reservation(reservation_id: str) -> None:
    """
    Cancela una reservación (cambia status a "cancelled") y persiste el cambio

    Regla:
    - Solo se cancela si el status actual es "active".
    - Si no existe o no está activa, se reporta y no se modifica el archivo

    Args:
        reservation_id (str): Identificador de la reservación a cancelar
    """
    records = load_list("reservations")
    idx = _find_index(records, "reservation_id", reservation_id)
    if idx == -1:
        print(
            f"[storage] reservations: no existe reservation_id {reservation_id}. "
            "Se ignora cancel."
        )
        return

    record = records[idx]
    status = str(record.get("status", ""))
    if status != "active":
        print(
            f"[storage] reservations: reservation_id {reservation_id} no está activa. "
            "Se ignora cancel."
        )
        return

    record["status"] = "cancelled"
    records[idx] = record
    save_list("reservations", records)

"""
Casos de uso/orquestación + main() para ejecución en consola (reservar/cancelar, etc.)

Este módulo implementa la **lógica de negocio** que coordina:
- Validaciones cruzadas entre entidades (Hotel/Customer/Reservation)
- Operaciones atómicas a nivel aplicación: reservar habitación y cancelar reservación

Nota:
La capa de persistencia (storage.py) ya maneja:
- Lectura/Escritura robusta en archivos (Req 5)
- CRUD de hoteles y clientes
- Create/Cancel/Get de reservaciones (persistencia)

Aquí (app.py) se agregan reglas de negocio, por ejemplo:
- No se puede reservar si el hotel no existe o no tiene disponibilidad
- No se puede reservar si el cliente no existe
- Al reservar: decrementa rooms_available del hotel
- Al cancelar una reservación activa: incrementa rooms_available del hotel (sin exceder rooms_total)
"""
from __future__ import annotations

import re
from typing import Optional

from Source import storage
from Source.models import Hotel, Reservation


_RES_ID_RE = re.compile(r"^R(\d{3})$")


def _next_reservation_id() -> str:
    """
    Genera el siguiente reservation_id en el formato R###

    La función consulta el store persistente para encontrar el máximo numérico
    usado hasta el momento y devuelve el siguiente

    Política Req 5:
    - Si el archivo contiene datos inválidos, storage.load_list ya los ignora
    - Si no hay ninguna reservación válida, el contador inicia en 1

    Returns:
        str: Nuevo ID en formato "R###"
    """
    records = storage.load_list("reservations")
    max_n = 0

    for r in records:
        rid = str(r.get("reservation_id", ""))
        m = _RES_ID_RE.fullmatch(rid)
        if m is None:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        max_n = max(max_n, n)

    return f"R{max_n + 1:03d}"


def reserve_room(hotel_id: str, customer_id: str) -> Optional[str]:
    """
    Reserva una habitación para un cliente en un hotel

    Reglas de negocio:
    - El hotel debe existir
    - El cliente debe existir
    - El hotel debe tener rooms_available > 0
    - Se crea una reservación con status="active"
    - Se decrementa rooms_available del hotel y se persiste

    Args:
        hotel_id (str): Identificador del hotel
        customer_id (str): Identificador del cliente

    Returns:
        Optional[str]: reservation_id si se creó la reservación; None si falla
    """
    hotel = storage.get_hotel(hotel_id)
    if hotel is None:
        print(f"[app] No se puede reservar: hotel_id no existe: {hotel_id}")
        return None

    customer = storage.get_customer(customer_id)
    if customer is None:
        print(f"[app] No se puede reservar: customer_id no existe: {customer_id}")
        return None

    if hotel.rooms_available <= 0:
        print(f"[app] No se puede reservar: sin disponibilidad en hotel {hotel_id}")
        return None

    reservation_id = _next_reservation_id()
    reservation = Reservation(
        reservation_id=reservation_id,
        hotel_id=hotel.hotel_id,
        customer_id=customer.customer_id,
        status="active",
    )

    # 1) Disminuye disponibilidad en hotel
    updated_hotel = Hotel(
        hotel_id=hotel.hotel_id,
        name=hotel.name,
        location=hotel.location,
        rooms_total=hotel.rooms_total,
        rooms_available=hotel.rooms_available - 1,
    )
    storage.update_hotel(updated_hotel)

    # 2) Crea reservación
    storage.create_reservation(reservation)

    # Verificación para evitar inconsistencias si la persistencia falló
    persisted = storage.get_reservation(reservation_id)
    if persisted is None or persisted.status != "active":
        print(
            "[app] Error creando reservación en persistencia. Se revierte la disponibilidad."
        )
        reverted_hotel = Hotel(
            hotel_id=hotel.hotel_id,
            name=hotel.name,
            location=hotel.location,
            rooms_total=hotel.rooms_total,
            rooms_available=min(hotel.rooms_available, hotel.rooms_total),
        )
        storage.update_hotel(reverted_hotel)
        return None

    print(
        f"[app] Reservación creada: {reservation_id} "
        f"(hotel={hotel_id}, customer={customer_id})"
    )
    return reservation_id


def cancel_reservation(reservation_id: str) -> bool:
    """
    Cancela una reservación existente.

    Reglas de negocio:
    - La reservación debe existir
    - Solo se cancela si está en status="active"
    - Si el hotel asociado existe, se incrementa rooms_available sin exceder rooms_total

    Args:
        reservation_id (str): Identificador de la reservación

    Returns:
        bool: True si se canceló; False si no se pudo cancelar
    """
    reservation = storage.get_reservation(reservation_id)
    if reservation is None:
        print(f"[app] No se puede cancelar: reservation_id no existe: {reservation_id}")
        return False

    if reservation.status != "active":
        print(f"[app] No se puede cancelar: reservación no está activa: {reservation_id}")
        return False

    hotel = storage.get_hotel(reservation.hotel_id)
    if hotel is None:
        print(
            f"[app] Aviso: hotel asociado no existe ({reservation.hotel_id}). "
            "Se cancelará la reservación sin restaurar disponibilidad."
        )
        storage.cancel_reservation(reservation_id)
        return storage.get_reservation(reservation_id) is not None and (
            storage.get_reservation(reservation_id).status == "cancelled"
        )

    new_available = hotel.rooms_available + 1
    if new_available > hotel.rooms_total:
        print(
            f"[app] Aviso: rooms_available excede rooms_total en hotel {hotel.hotel_id}. "
            "Se ajusta al máximo permitido."
        )
        new_available = hotel.rooms_total

    updated_hotel = Hotel(
        hotel_id=hotel.hotel_id,
        name=hotel.name,
        location=hotel.location,
        rooms_total=hotel.rooms_total,
        rooms_available=new_available,
    )
    storage.update_hotel(updated_hotel)

    storage.cancel_reservation(reservation_id)

    persisted = storage.get_reservation(reservation_id)
    if persisted is None or persisted.status != "cancelled":
        print(f"[app] Error cancelando reservación: {reservation_id}")
        return False

    print(f"[app] Reservación cancelada: {reservation_id}")
    return True


def main() -> None:
    """
    Punto de entrada para ejecución manual en consola

    Este main es intencionalmente simple para la demostración (Functional tests)
    En unit tests se invocan directamente reserve_room/cancel_reservation

    Opciones:
        1) Reservar habitación
        2) Cancelar reservación
        0) Salir
    """
    storage.ensure_store()

    while True:
        print("\n=== Sistema de Reservaciones A6.2 ===")
        print("1) Reservar habitación")
        print("2) Cancelar reservación")
        print("0) Salir")
        option = input("Selecciona una opción: ").strip()

        if option == "0":
            print("Saliendo...")
            return

        if option == "1":
            hotel_id = input("hotel_id (H###): ").strip()
            customer_id = input("customer_id (C###): ").strip()
            reserve_room(hotel_id=hotel_id, customer_id=customer_id)
            continue

        if option == "2":
            reservation_id = input("reservation_id (R###): ").strip()
            cancel_reservation(reservation_id=reservation_id)
            continue

        print("Opción inválida.")


if __name__ == "__main__":
    main()

"""
Clases del dominio para el Sistema de Reservaciones de Hotel.

Este módulo define las entidades principales (Hotel, Customer, Reservation)
junto con validaciones básicas de consistencia local por entidad.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_id_hotel_re = re.compile(r"^H\d{3}$")
_id_customer_re = re.compile(r"^C\d{3}$")
_id_reservation_re = re.compile(r"^R\d{3}$")

_RESERVATION_STATUS = {"active", "cancelled"}


def _require_non_empty_str(value: str, field_name: str) -> None:
    """
    Valida que el valor proporcionado sea un string no vacío.

    Args:
        value (str): Valor a validar.
        field_name (str): Nombre del campo para mensajes de error.

    Raises:
        TypeError: Si el valor no es string.
        ValueError: Si el string está vacío o contiene solo espacios.
    """
    if not isinstance(value, str):
        raise TypeError(f"{field_name} debe ser str")
    if value.strip() == "":
        raise ValueError(f"{field_name} no debe estar vacío")


def _require_int(value: int, field_name: str) -> None:
    """
    Valida que el valor proporcionado sea un entero.

    Args:
        value (int): Valor a validar.
        field_name (str): Nombre del campo para mensajes de error.

    Raises:
        TypeError: Si el valor no es un entero.
    """
    if not isinstance(value, int):
        raise TypeError(f"{field_name} debe ser int")


def _require_id(pattern: re.Pattern[str], value: str, field_name: str) -> None:
    """
    Valida que un identificador cumpla con el patrón requerido.

    Args:
        pattern (re.Pattern): Expresión regular que define el formato válido.
        value (str): Identificador a validar.
        field_name (str): Nombre del campo para mensajes de error.

    Raises:
        ValueError: Si el identificador no cumple el formato esperado.
    """
    _require_non_empty_str(value, field_name)
    if pattern.fullmatch(value) is None:
        raise ValueError(f"{field_name} tiene formato inválido: {value}")


def _safe_int(value: Any, default: int) -> int:
    """
    Convierte un valor a int con un default.

    Args:
        value (Any): Valor a convertir.
        default (int): Valor por defecto.

    Returns:
        int: Entero resultante.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class Hotel:
    """
    Representa un hotel dentro del sistema.

    Atributos:
        hotel_id (str): Identificador único del hotel.
        name (str): Nombre del hotel.
        location (str): Ubicación del hotel.
        rooms_total (int): Número total de habitaciones.
        rooms_available (int): Número de habitaciones disponibles.
    """

    hotel_id: str
    name: str
    location: str
    rooms_total: int
    rooms_available: int

    def __post_init__(self) -> None:
        """
        Ejecuta validaciones básicas después de la inicialización.

        Verifica:
        - Formato del hotel_id.
        - Campos string no vacíos.
        - Tipos correctos.
        - Consistencia entre rooms_total y rooms_available.

        Raises:
            TypeError: Si algún tipo es incorrecto.
            ValueError: Si alguna restricción no se cumple.
        """
        _require_id(_id_hotel_re, self.hotel_id, "hotel_id")
        _require_non_empty_str(self.name, "name")
        _require_non_empty_str(self.location, "location")

        self.rooms_total = _safe_int(self.rooms_total, 0)
        self.rooms_available = _safe_int(self.rooms_available, 0)

        if self.rooms_total <= 0:
            raise ValueError("rooms_total debe ser > 0")
        if self.rooms_available < 0:
            raise ValueError("rooms_available debe ser >= 0")
        if self.rooms_available > self.rooms_total:
            raise ValueError("rooms_available no debe exceder rooms_total")

    def to_dict(self) -> dict[str, object]:
        """
        Convierte la instancia Hotel en un diccionario serializable.

        Returns:
            dict: Representación del hotel compatible con JSON.
        """
        return {
            "hotel_id": self.hotel_id,
            "name": self.name,
            "location": self.location,
            "rooms_total": self.rooms_total,
            "rooms_available": self.rooms_available,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Hotel":
        """
        Crea una instancia Hotel a partir de un diccionario.

        Args:
            data (dict): Diccionario con los datos del hotel.

        Returns:
            Hotel: Instancia creada a partir del diccionario.
        """
        return cls(
            hotel_id=str(data.get("hotel_id", "")),
            name=str(data.get("name", "")),
            location=str(data.get("location", "")),
            rooms_total=data.get("rooms_total", 0),
            rooms_available=data.get("rooms_available", 0),
        )


@dataclass
class Customer:
    """
    Representa un cliente del sistema.

    Atributos:
        customer_id (str): Identificador único del cliente.
        name (str): Nombre del cliente.
        email (str): Correo electrónico del cliente.
    """

    customer_id: str
    name: str
    email: str

    def __post_init__(self) -> None:
        """
        Ejecuta validaciones básicas después de la inicialización.

        Verifica:
        - Formato del customer_id.
        - Campos string no vacíos.

        Raises:
            TypeError: Si los tipos son incorrectos.
            ValueError: Si alguna restricción no se cumple.
        """
        _require_id(_id_customer_re, self.customer_id, "customer_id")
        _require_non_empty_str(self.name, "name")
        _require_non_empty_str(self.email, "email")

    def to_dict(self) -> dict[str, object]:
        """
        Convierte la instancia Customer en un diccionario serializable.

        Returns:
            dict: Representación del cliente compatible con JSON.
        """
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Customer":
        """
        Crea una instancia Customer a partir de un diccionario.

        Args:
            data (dict): Diccionario con los datos del cliente.

        Returns:
            Customer: Instancia creada a partir del diccionario.
        """
        return cls(
            customer_id=str(data.get("customer_id", "")),
            name=str(data.get("name", "")),
            email=str(data.get("email", "")),
        )


@dataclass
class Reservation:
    """
    Representa una reservación realizada por un cliente.

    Atributos:
        reservation_id (str): Identificador único de la reservación.
        hotel_id (str): Identificador del hotel asociado.
        customer_id (str): Identificador del cliente asociado.
        status (str): Estado de la reservación ("active" o "cancelled").
    """

    reservation_id: str
    hotel_id: str
    customer_id: str
    status: str

    def __post_init__(self) -> None:
        """
        Ejecuta validaciones básicas después de la inicialización.

        Verifica:
        - Formato de reservation_id.
        - Formato de hotel_id y customer_id.
        - Estado válido de la reservación.

        Raises:
            TypeError: Si los tipos son incorrectos.
            ValueError: Si el estado o los identificadores son inválidos.
        """
        _require_id(_id_reservation_re, self.reservation_id, "reservation_id")
        _require_id(_id_hotel_re, self.hotel_id, "hotel_id")
        _require_id(_id_customer_re, self.customer_id, "customer_id")
        _require_non_empty_str(self.status, "status")

        if self.status not in _RESERVATION_STATUS:
            raise ValueError(f"status inválido: {self.status}")

    def to_dict(self) -> dict[str, object]:
        """
        Convierte la instancia Reservation en un diccionario serializable.

        Returns:
            dict: Representación de la reservación compatible con JSON.
        """
        return {
            "reservation_id": self.reservation_id,
            "hotel_id": self.hotel_id,
            "customer_id": self.customer_id,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Reservation":
        """
        Crea una instancia Reservation a partir de un diccionario.

        Args:
            data (dict): Diccionario con los datos de la reservación.

        Returns:
            Reservation: Instancia creada a partir del diccionario.
        """
        return cls(
            reservation_id=str(data.get("reservation_id", "")),
            hotel_id=str(data.get("hotel_id", "")),
            customer_id=str(data.get("customer_id", "")),
            status=str(data.get("status", "")),
        )

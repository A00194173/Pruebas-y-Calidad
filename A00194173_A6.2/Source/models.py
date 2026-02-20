"""
Clases del dominio para el Sistema de Reservaciones de Hotel.
"""

from dataclasses import dataclass


@dataclass
class Hotel:
    """
    Representa un hotel dentro del sistema.
    """
    hotel_id: str
    name: str
    location: str
    rooms_total: int
    rooms_available: int


@dataclass
class Customer:
    """
    Representa un cliente del sistema.
    """
    customer_id: str
    name: str
    email: str


@dataclass
class Reservation:
    """
    Representa una reservación realizada por un cliente.
    """
    reservation_id: str
    hotel_id: str
    customer_id: str
    status: str
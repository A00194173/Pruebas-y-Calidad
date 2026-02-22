"""
Pruebas unitarias para models.py (entidades del dominio).

Cubre:
- Creación válida de Hotel, Customer y Reservation
- Validaciones de formato de IDs (H###, C###, R###)
- Reglas de consistencia de Hotel (rooms_total > 0, rooms_available >= 0,
  rooms_available <= rooms_total)
- Validación de status en Reservation
"""

# pylint: disable=duplicate-code

import unittest

from Source.models import Customer, Hotel, Reservation


class TestModels(unittest.TestCase):
    """Suite de pruebas para validar reglas locales de las entidades."""

    def test_hotel_valid(self):
        """Crea un hotel válido y verifica atributos."""
        h = Hotel(
            hotel_id="H001",
            name="Hotel Central",
            location="Monterrey",
            rooms_total=10,
            rooms_available=10,
        )
        self.assertEqual(h.hotel_id, "H001")
        self.assertEqual(h.rooms_total, 10)
        self.assertEqual(h.rooms_available, 10)

    def test_hotel_invalid_id(self):
        """Verifica que hotel_id inválido dispare ValueError."""
        with self.assertRaises(ValueError):
            Hotel(
                hotel_id="HX01",
                name="Hotel X",
                location="MTY",
                rooms_total=10,
                rooms_available=10,
            )

    def test_hotel_rooms_total_must_be_gt_zero(self):
        """rooms_total debe ser > 0."""
        with self.assertRaises(ValueError):
            Hotel(
                hotel_id="H002",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=0,
                rooms_available=0,
            )

    def test_hotel_rooms_available_not_negative(self):
        """rooms_available debe ser >= 0."""
        with self.assertRaises(ValueError):
            Hotel(
                hotel_id="H003",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=5,
                rooms_available=-1,
            )

    def test_hotel_rooms_available_not_exceed_total(self):
        """rooms_available no debe exceder rooms_total."""
        with self.assertRaises(ValueError):
            Hotel(
                hotel_id="H004",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=5,
                rooms_available=6,
            )

    def test_customer_valid(self):
        """Crea un cliente válido."""
        c = Customer(customer_id="C001", name="Ana", email="ana@example.com")
        self.assertEqual(c.customer_id, "C001")
        self.assertEqual(c.email, "ana@example.com")

    def test_customer_invalid_id(self):
        """Verifica que customer_id inválido dispare ValueError."""
        with self.assertRaises(ValueError):
            Customer(customer_id="1", name="Ana", email="ana@example.com")

    def test_reservation_valid(self):
        """Crea una reservación válida."""
        r = Reservation(
            reservation_id="R001",
            hotel_id="H001",
            customer_id="C001",
            status="active",
        )
        self.assertEqual(r.status, "active")

    def test_reservation_invalid_status(self):
        """status inválido debe disparar ValueError."""
        with self.assertRaises(ValueError):
            Reservation(
                reservation_id="R002",
                hotel_id="H001",
                customer_id="C001",
                status="pending",
            )

    def test_reservation_invalid_ids(self):
        """IDs inválidos en reservación deben disparar ValueError."""
        with self.assertRaises(ValueError):
            Reservation(
                reservation_id="RXXX",
                hotel_id="H001",
                customer_id="C001",
                status="active",
            )
        with self.assertRaises(ValueError):
            Reservation(
                reservation_id="R003",
                hotel_id="H1",
                customer_id="C001",
                status="active",
            )
        with self.assertRaises(ValueError):
            Reservation(
                reservation_id="R004",
                hotel_id="H001",
                customer_id="C1",
                status="active",
            )


if __name__ == "__main__":
    unittest.main()

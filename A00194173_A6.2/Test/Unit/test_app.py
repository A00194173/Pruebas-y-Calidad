"""
Unit tests para la lógica de negocio en app.py (reservar/cancelar habitación).

Objetivo:
- Cubrir reglas de negocio en reserve_room() y cancel_reservation()
- Cubrir ramas de error/avisos y el menú main() para elevar coverage de app.py

Nota:
- Se usa un store temporal por prueba (A6_STORE_DIR) para aislar persistencia.
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from Source import app, storage
from Source.models import Customer, Hotel, Reservation


class TestAppBusinessLogic(unittest.TestCase):
    """Suite de pruebas para reglas de negocio en app.py."""

    def setUp(self):
        """Configura un store temporal aislado con un hotel y un cliente base."""
        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        os.environ["A6_STORE_DIR"] = str(Path(self.temp_dir.name) / "Store")
        storage.ensure_store()

        storage.create_hotel(
            Hotel(
                hotel_id="H001",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=2,
                rooms_available=2,
            )
        )
        storage.create_customer(
            Customer(customer_id="C001", name="Ana", email="ana@x.com")
        )

    def tearDown(self):
        """Limpia el store temporal y restaura variables de entorno."""
        self.temp_dir.cleanup()
        os.environ.pop("A6_STORE_DIR", None)

    def test_reserve_room_success_creates_reservation_and_decrements_rooms(self):
        """Verifica que una reserva válida crea la reservación y reduce rooms_available en 1."""
        out = io.StringIO()
        with redirect_stdout(out):
            rid = app.reserve_room("H001", "C001")

        self.assertIsNotNone(rid)
        got_hotel = storage.get_hotel("H001")
        self.assertIsNotNone(got_hotel)
        self.assertEqual(got_hotel.rooms_available, 1)

        got_res = storage.get_reservation(rid)
        self.assertIsNotNone(got_res)
        self.assertEqual(got_res.status, "active")

    def test_reserve_room_fails_when_no_availability(self):
        """Verifica que no se cree reservación cuando rooms_available es 0."""
        app.reserve_room("H001", "C001")
        app.reserve_room("H001", "C001")

        out = io.StringIO()
        with redirect_stdout(out):
            rid3 = app.reserve_room("H001", "C001")

        self.assertIsNone(rid3)
        self.assertIn("sin disponibilidad", out.getvalue())

    def test_reserve_room_fails_when_hotel_missing(self):
        """Verifica que la reserva falle si el hotel no existe."""
        out = io.StringIO()
        with redirect_stdout(out):
            rid = app.reserve_room("H404", "C001")

        self.assertIsNone(rid)
        self.assertIn("hotel_id no existe", out.getvalue())

    def test_reserve_room_fails_when_customer_missing(self):
        """Verifica que la reserva falle si el cliente no existe."""
        out = io.StringIO()
        with redirect_stdout(out):
            rid = app.reserve_room("H001", "C404")

        self.assertIsNone(rid)
        self.assertIn("customer_id no existe", out.getvalue())

    def test_reserve_room_rolls_back_when_persistence_does_not_confirm(self):
        """Verifica rollback de disponibilidad si la reservación no queda persistida como active."""
        # Reducimos disponibilidad a 1 para ver claramente el rollback a 2
        storage.update_hotel(
            Hotel(
                hotel_id="H001",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=2,
                rooms_available=2,
            )
        )

        # Simula falla de verificación: get_reservation regresa None justo después del create
        with patch("Source.app.storage.get_reservation", return_value=None):
            out = io.StringIO()
            with redirect_stdout(out):
                rid = app.reserve_room("H001", "C001")

        self.assertIsNone(rid)
        self.assertIn("Se revierte la disponibilidad", out.getvalue())

        # Debe quedar revertida a 2
        hotel_after = storage.get_hotel("H001")
        self.assertIsNotNone(hotel_after)
        self.assertEqual(hotel_after.rooms_available, 2)

    def test_next_reservation_id_skips_invalid_ids_and_handles_value_error(self):
        """Verifica que _next_reservation_id ignore IDs inválidos y continúe ante ValueError."""
        # Prepara lista con un id inválido (no coincide con patrón) y uno válido.
        fake_records = [
            {"reservation_id": "BAD"},
            {"reservation_id": "R001"},
        ]

        # 1) Cubre la rama m is None (continue)
        with patch("Source.app.storage.load_list", return_value=fake_records):
            rid = app._next_reservation_id()  # pylint: disable=protected-access
        self.assertEqual(rid, "R002")

        # 2) Cubre la rama except ValueError en int(...)
        with patch("Source.app.storage.load_list", return_value=[{"reservation_id": "R001"}]):
            with patch("builtins.int", side_effect=ValueError):
                rid2 = app._next_reservation_id()  # pylint: disable=protected-access
        # Si int falla, max_n se queda 0 -> R001
        self.assertEqual(rid2, "R001")

    def test_cancel_reservation_success_increments_rooms_and_cancels(self):
        """Verifica que cancelar una reservación activa restaure disponibilidad y cambie status."""
        rid = app.reserve_room("H001", "C001")
        hotel_after_reserve = storage.get_hotel("H001")
        self.assertEqual(hotel_after_reserve.rooms_available, 1)

        out = io.StringIO()
        with redirect_stdout(out):
            ok = app.cancel_reservation(rid)

        self.assertTrue(ok)
        hotel_after_cancel = storage.get_hotel("H001")
        self.assertEqual(hotel_after_cancel.rooms_available, 2)

        res_after_cancel = storage.get_reservation(rid)
        self.assertIsNotNone(res_after_cancel)
        self.assertEqual(res_after_cancel.status, "cancelled")
        self.assertIn("cancelada", out.getvalue())

    def test_cancel_reservation_fails_when_nonexistent(self):
        """Verifica que cancelar una reservación inexistente retorne False y reporte error."""
        out = io.StringIO()
        with redirect_stdout(out):
            ok = app.cancel_reservation("R999")

        self.assertFalse(ok)
        self.assertIn("no existe", out.getvalue())

    def test_cancel_reservation_fails_when_not_active(self):
        """Verifica que no se cancele una reservación cuyo status no es 'active'."""
        storage.create_reservation(
            Reservation(
                reservation_id="R010",
                hotel_id="H001",
                customer_id="C001",
                status="cancelled",
            )
        )
        out = io.StringIO()
        with redirect_stdout(out):
            ok = app.cancel_reservation("R010")

        self.assertFalse(ok)
        self.assertIn("no está activa", out.getvalue())

    def test_cancel_reservation_when_hotel_missing(self):
        """Verifica que se cancele aunque el hotel asociado
           no exista (sin restaurar disponibilidad)."""
        storage.create_reservation(
            Reservation(
                reservation_id="R020",
                hotel_id="H404",
                customer_id="C001",
                status="active",
            )
        )
        out = io.StringIO()
        with redirect_stdout(out):
            ok = app.cancel_reservation("R020")

        self.assertTrue(ok)
        self.assertIn("hotel asociado no existe", out.getvalue())

        res_after = storage.get_reservation("R020")
        self.assertIsNotNone(res_after)
        self.assertEqual(res_after.status, "cancelled")

    def test_cancel_reservation_adjusts_rooms_when_exceeds_total(self):
        """Verifica que rooms_available se ajuste al máximo si excede rooms_total al cancelar."""
        # Hotel inconsistente: rooms_available ya al máximo
        storage.update_hotel(
            Hotel(
                hotel_id="H001",
                name="Hotel Central",
                location="Monterrey",
                rooms_total=2,
                rooms_available=2,
            )
        )
        storage.create_reservation(
            Reservation(
                reservation_id="R030",
                hotel_id="H001",
                customer_id="C001",
                status="active",
            )
        )
        out = io.StringIO()
        with redirect_stdout(out):
            ok = app.cancel_reservation("R030")

        self.assertTrue(ok)
        self.assertIn("excede rooms_total", out.getvalue())

        hotel_after = storage.get_hotel("H001")
        self.assertIsNotNone(hotel_after)
        self.assertEqual(hotel_after.rooms_available, 2)

    def test_cancel_reservation_reports_failure_when_not_persisted_as_cancelled(self):
        """Verifica que cancel_reservation falle si la reservación no queda
           persistida como cancelled."""
        storage.create_reservation(
            Reservation(
                reservation_id="R040",
                hotel_id="H001",
                customer_id="C001",
                status="active",
            )
        )

        # get_reservation devolverá siempre active para simular que no se persistió el cambio
        fake_active = Reservation(
            reservation_id="R040",
            hotel_id="H001",
            customer_id="C001",
            status="active",
        )
        with patch("Source.app.storage.get_reservation", return_value=fake_active):
            out = io.StringIO()
            with redirect_stdout(out):
                ok = app.cancel_reservation("R040")

        self.assertFalse(ok)
        self.assertIn("Error cancelando", out.getvalue())

    def test_main_invalid_option_then_exit(self):
        """Verifica que main reporte opción inválida y permita salir con opción 0."""
        with patch("builtins.input", side_effect=["x", "0"]):
            out = io.StringIO()
            with redirect_stdout(out):
                app.main()
        self.assertIn("Opción inválida", out.getvalue())
        self.assertIn("Saliendo", out.getvalue())

    def test_main_option_1_calls_reserve_room_then_exit(self):
        """Verifica que main ejecute la ruta de reservar (opción 1) y luego salga."""
        with patch("Source.app.reserve_room") as mock_reserve:
            with patch("builtins.input", side_effect=["1", "H001", "C001", "0"]):
                out = io.StringIO()
                with redirect_stdout(out):
                    app.main()
        mock_reserve.assert_called_once_with(hotel_id="H001", customer_id="C001")

    def test_main_option_2_calls_cancel_reservation_then_exit(self):
        """Verifica que main ejecute la ruta de cancelar (opción 2) y luego salga."""
        with patch("Source.app.cancel_reservation") as mock_cancel:
            with patch("builtins.input", side_effect=["2", "R001", "0"]):
                out = io.StringIO()
                with redirect_stdout(out):
                    app.main()
        mock_cancel.assert_called_once_with(reservation_id="R001")


if __name__ == "__main__":
    unittest.main()

"""
Pruebas unitarias básicas para la capa de persistencia (storage).

Cubre:
- Creación del store en un directorio temporal
- Lectura robusta ante JSON corrupto
- Ignorar registros inválidos (Req 5: reportar y continuar)
- CRUD básico de hoteles y clientes
- Crear y cancelar reservaciones (persistencia)
"""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from Source import storage
from Source.models import Customer, Hotel, Reservation

# --- Configuración de rutas para fixtures ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"


class TestStorageBasic(unittest.TestCase):
    """Suite de pruebas para validar comportamientos base de storage.py."""

    def setUp(self):
        """Prepara un store aislado usando un directorio temporal por prueba."""
        self.temp_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        os.environ["A6_STORE_DIR"] = str(Path(self.temp_dir.name) / "Store")
        storage.ensure_store()

    def tearDown(self):
        """Limpia recursos del store temporal y restaura variables de entorno."""
        self.temp_dir.cleanup()
        os.environ.pop("A6_STORE_DIR", None)

    def _write_store_file(self, filename: str, content: str) -> Path:
        """
        Escribe contenido directamente en un archivo del store temporal.

        Args:
            filename (str): Nombre del archivo JSON dentro del store (p.ej. 'hotels.json').
            content (str): Contenido a escribir.

        Returns:
            Path: Ruta al archivo escrito.
        """
        path = Path(os.environ["A6_STORE_DIR"]) / filename
        path.write_text(content, encoding="utf-8")
        return path

    def test_ensure_store_creates_files(self):
        """Verifica que ensure_store cree los 3 archivos persistentes si no existen."""
        store_dir = Path(os.environ["A6_STORE_DIR"])
        self.assertTrue(store_dir.exists())

        for filename in ["hotels.json", "customers.json", "reservations.json"]:
            self.assertTrue((store_dir / filename).exists())

    def test_load_list_with_corrupt_json_continues(self):
        """Verifica que JSON corrupto no detenga ejecución y regrese lista vacía."""
        self._write_store_file("hotels.json", "{")

        f = io.StringIO()
        with redirect_stdout(f):
            data = storage.load_list("hotels")

        self.assertEqual(data, [])
        self.assertIn("JSON inválido", f.getvalue())

    def test_load_list_root_not_list_continues(self):
        """Verifica que si el JSON no es lista, se reporte y se regrese []."""
        self._write_store_file("hotels.json", "{}")

        f = io.StringIO()
        with redirect_stdout(f):
            data = storage.load_list("hotels")

        self.assertEqual(data, [])
        self.assertIn("se esperaba lista", f.getvalue())

    def test_load_list_skips_invalid_records(self):
        """Verifica que registros inválidos sean ignorados y se reporte en consola."""
        data_path = DATA_DIR / "hotels_invalid.json"
        text = data_path.read_text(encoding="utf-8")
        self._write_store_file("hotels.json", text)

        f = io.StringIO()
        with redirect_stdout(f):
            cleaned = storage.load_list("hotels")

        self.assertIsInstance(cleaned, list)
        self.assertEqual(len(cleaned), 0)
        self.assertIn("registros inválidos ignorados", f.getvalue())

    def test_hotel_crud_basic(self):
        """Prueba flujo CRUD básico de hoteles usando la capa de persistencia."""
        h = Hotel(
            hotel_id="H001",
            name="Hotel Central",
            location="Monterrey",
            rooms_total=10,
            rooms_available=10,
        )
        storage.create_hotel(h)

        got = storage.get_hotel("H001")
        self.assertIsNotNone(got)
        self.assertEqual(got.hotel_id, "H001")

        h2 = Hotel(
            hotel_id="H001",
            name="Hotel Central 2",
            location="Monterrey",
            rooms_total=10,
            rooms_available=9,
        )
        storage.update_hotel(h2)

        got2 = storage.get_hotel("H001")
        self.assertIsNotNone(got2)
        self.assertEqual(got2.name, "Hotel Central 2")

        storage.delete_hotel("H001")
        got3 = storage.get_hotel("H001")
        self.assertIsNone(got3)

    def test_create_hotel_duplicate_is_ignored(self):
        """Verifica que un create con ID duplicado no agrega un segundo registro."""
        h = Hotel(
            hotel_id="H001",
            name="Hotel Central",
            location="Monterrey",
            rooms_total=10,
            rooms_available=10,
        )
        storage.create_hotel(h)

        f = io.StringIO()
        with redirect_stdout(f):
            storage.create_hotel(h)

        self.assertIn("duplicado", f.getvalue())

        records = storage.load_list("hotels")
        self.assertEqual(len(records), 1)

    def test_delete_hotel_nonexistent_is_ignored(self):
        """Verifica que delete de hotel inexistente no truene y reporte."""
        f = io.StringIO()
        with redirect_stdout(f):
            storage.delete_hotel("H999")
        self.assertIn("no existe", f.getvalue())

    def test_get_hotel_returns_none_when_not_found(self):
        """Verifica que get_hotel regrese None si no existe."""
        got = storage.get_hotel("H404")
        self.assertIsNone(got)

    def test_customer_crud_basic(self):
        """Prueba flujo CRUD básico de clientes usando la capa de persistencia."""
        c = Customer(customer_id="C001", name="Ana", email="ana@example.com")
        storage.create_customer(c)

        got = storage.get_customer("C001")
        self.assertIsNotNone(got)

        c2 = Customer(customer_id="C001", name="Ana P", email="ana@example.com")
        storage.update_customer(c2)

        got2 = storage.get_customer("C001")
        self.assertIsNotNone(got2)
        self.assertEqual(got2.name, "Ana P")

        storage.delete_customer("C001")
        got3 = storage.get_customer("C001")
        self.assertIsNone(got3)

    def test_get_customer_returns_none_when_not_found(self):
        """Verifica que get_customer regrese None si no existe."""
        got = storage.get_customer("C404")
        self.assertIsNone(got)

    def test_update_customer_nonexistent_is_ignored(self):
        """Verifica que update de cliente inexistente no truene y reporte."""
        c = Customer(customer_id="C999", name="X", email="x@example.com")

        f = io.StringIO()
        with redirect_stdout(f):
            storage.update_customer(c)
        self.assertIn("no existe", f.getvalue())

    def test_delete_customer_nonexistent_is_ignored(self):
        """Verifica que delete de cliente inexistente no truene y reporte."""
        f = io.StringIO()
        with redirect_stdout(f):
            storage.delete_customer("C999")
        self.assertIn("no existe", f.getvalue())

    def test_reservation_create_and_cancel(self):
        """Prueba creación y cancelación de reservación a nivel persistencia."""
        r = Reservation(
            reservation_id="R001",
            hotel_id="H001",
            customer_id="C001",
            status="active",
        )
        storage.create_reservation(r)

        got = storage.get_reservation("R001")
        self.assertIsNotNone(got)
        self.assertEqual(got.status, "active")

        storage.cancel_reservation("R001")

        got2 = storage.get_reservation("R001")
        self.assertIsNotNone(got2)
        self.assertEqual(got2.status, "cancelled")

    def test_cancel_reservation_not_active_is_ignored(self):
        """Verifica que no se cancele si la reservación no está activa."""
        r = Reservation(
            reservation_id="R010",
            hotel_id="H001",
            customer_id="C001",
            status="cancelled",
        )
        storage.create_reservation(r)

        f = io.StringIO()
        with redirect_stdout(f):
            storage.cancel_reservation("R010")

        self.assertIn("no está activa", f.getvalue())

    def test_cancel_reservation_nonexistent_is_ignored(self):
        """Verifica que cancel de reservación inexistente no truene y reporte."""
        f = io.StringIO()
        with redirect_stdout(f):
            storage.cancel_reservation("R999")
        self.assertIn("no existe", f.getvalue())

    def test_create_reservation_duplicate_is_ignored(self):
        """Verifica que create de reservación duplicada no agregue un segundo registro."""
        r = Reservation(
            reservation_id="R050",
            hotel_id="H001",
            customer_id="C001",
            status="active",
        )
        storage.create_reservation(r)

        f = io.StringIO()
        with redirect_stdout(f):
            storage.create_reservation(r)

        self.assertIn("duplicado", f.getvalue())
        records = storage.load_list("reservations")
        self.assertEqual(len(records), 1)

    def test_cancel_reservation_not_active_message(self):
        """Verifica mensaje al intentar cancelar una reservación que no está activa."""
        r = Reservation(
            reservation_id="R051",
            hotel_id="H001",
            customer_id="C001",
            status="cancelled",
        )
        storage.create_reservation(r)

        f = io.StringIO()
        with redirect_stdout(f):
            storage.cancel_reservation("R051")

        self.assertIn("no está activa", f.getvalue())

    def test_get_reservation_returns_none_when_not_found(self):
        """Verifica que get_reservation regrese None si no existe."""
        got = storage.get_reservation("R404")
        self.assertIsNone(got)


if __name__ == "__main__":
    unittest.main()

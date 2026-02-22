# A6.2 – Hotel Reservation System

## Estructura
A00194173_A6.2/		<-- Raíz de la tarea A6.2
  Source/		<-- Código fuente del sistema
    models.py		<-- Clases: Hotel, Customer, Reservation
    storage.py		<-- Persistencia en archivos: load/save + CRUD + manejo de inválidos (Req 2, Req 5)
    app.py		<-- Casos de uso/orquestación + main() para ejecución en consola (reservar/cancelar, etc.)
  Test/			<-- Todo lo relacionado con pruebas
    Unit/		<-- Unit tests (Req 3)
      test_*.py		<-- Archivos de pruebas unitarias por bloque (hotel/customer/reservation/invalid data)
      Data/		<-- Fixtures JSON visibles para unit tests (válidos/ inválidos), NO se modifican en ejecución
    Functional/		<-- Pruebas funcionales manuales (demostración desde consola)
      SampleData/	<-- Inputs de ejemplo para correr el programa manualmente
      Expected/		<-- Salidas esperadas
      Notes.md		<-- Pasos para ejecutar pruebas manuales + qué validar
  Results/		<-- Salidas generadas por ejecuciones
    Store/		<-- “Base de datos” file-based persistente del sistema
          		<-- hotels.json / customers.json / reservations.json (se crean/actualizan al ejecutar)
    Coverage Report n/	<-- 1 Folder por cada Reporte de covertura
  requirements.txt	<-- Dependencias de A6.2 (flake8, pylint, coverage, etc.)
  README.md		<-- Cómo ejecutar, cómo correr lint, unit tests, cobertura + contrato de persistencia resumido

---

## Arquitectura

El sistema está organizado en tres capas claramente separadas:

models.py  
Define las entidades del dominio:
- Hotel
- Customer
- Reservation

Responsabilidades:
- Validaciones locales
- Reglas internas de consistencia

storage.py  
Gestiona la persistencia en archivos:
- Inicialización del directorio Results/Store
- Lectura y escritura robusta de JSON
- Operaciones CRUD
- Manejo de datos inválidos (Req 5)

app.py  
Implementa la lógica de negocio:
- Reservar habitación
- Cancelar reservación
- Reglas cruzadas entre entidades (existencia, disponibilidad, etc.)

---

## Trazabilidad de Requerimientos

### Req 1 – Clases del Dominio

Implementado en:
- Source/models.py
Clases:
- Hotel
- Customer
- Reservation

### Req 2 – Comportamientos Persistentes

Hotels  
- Create Hotel → storage.create_hotel()  
- Delete Hotel → storage.delete_hotel()  
- Display Hotel → storage.get_hotel()  
- Modify Hotel → storage.update_hotel()  
- Reserve Room → app.reserve_room()  
- Cancel Reservation → app.cancel_reservation()  

Customers  
- Create Customer → storage.create_customer()  
- Delete Customer → storage.delete_customer()  
- Display Customer → storage.get_customer()  
- Modify Customer → storage.update_customer()  

Reservations  
- Create Reservation → storage.create_reservation() (orquestado desde app.py)  
- Cancel Reservation → storage.cancel_reservation() (orquestado desde app.py)  

### Req 3 – Pruebas Unitarias

Implementadas utilizando unittest.
Archivos de prueba:
- Test/Unit/test_models.py
- Test/Unit/test_storage.py
- Test/Unit/test_app.py

Se prueban los comportamientos principales del sistema.

### Req 4 – Cobertura de Código

Cobertura acumulada ≥ 85%

Comandos:

coverage run -m unittest discover Test/Unit  
coverage report

Los reportes se almacenan en:
Results/Coverage Report n/

### Req 5 – Manejo de Datos Inválidos

Implementado en storage.py:

- JSON corrupto → la ejecución continúa  
- Raíz que no es lista → la ejecución continúa  
- Registros inválidos → se ignoran y se reportan  
- Errores de IO → se reportan en consola  

Validado en test_storage.py.

### Req 6 – Cumplimiento PEP8

Verificado con:
flake8 Source Test

### Req 7 – Sin Advertencias en PyLint

Verificado con:
pylint Source Test

---

## Decisiones de Diseño

- Separación clara entre dominio, persistencia y lógica de negocio.  
- Persistencia configurable mediante variable de entorno.  
- Manejo robusto de errores sin detener la ejecución.  
- Uso de directorios temporales en pruebas para aislar persistencia.  
- Validaciones estrictas a nivel entidad.

---

## Run
python -m Source.app

---

## Lint
flake8 Source
pylint Source

---

## Unit Tests
python -m unittest discover Test/Unit

---

## Coverage
python -m coverage run -m unittest discover Test/Unit
python -m coverage report -m
python -m coverage html

---

## Evidencia y Directorio Results/

El directorio `Results/` forma parte intencional de la entrega.

Contiene:

- `Coverage Report n/`  
  Reportes HTML de cobertura generados mediante la ejecución de pruebas unitarias.

- `Functional/`  
  Evidencia de ejecución manual de pruebas funcionales, incluyendo el archivo:
  `run_manual.txt`.

- `Store/`  
  Archivos JSON persistentes generados durante la ejecución del sistema:
  - hotels.json
  - customers.json
  - reservations.json

El contenido de `Store/` representa el estado final del sistema después de la ejecución
de las pruebas funcionales manuales y se conserva como evidencia académica.

En un entorno productivo estos archivos no se versionarían,
pero en esta entrega se incluyen para demostrar el cumplimiento
de los requisitos de persistencia y pruebas funcionales.
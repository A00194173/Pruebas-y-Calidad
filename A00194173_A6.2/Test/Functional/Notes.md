# A6.2 – Evidencia de Ejecución

## 1. Verificación de estilo (Req 6 y Req 7)

### Flake8

Comando ejecutado:

flake8 Source Test

Resultado:

- Sin errores.
- Sin advertencias.

---

### PyLint

Comando ejecutado:

pylint Source Test

Resultado:

Your code has been rated at 10.00/10

---

## 2. Pruebas Unitarias (Req 3)

Comando ejecutado:

python -m unittest discover Test/Unit -v

Resultado:

Ran 43 tests in 0.164s

---

## 3. Cobertura de Código (Req 4)

Comando ejecutado:

coverage run -m unittest discover Test/Unit
coverage report -m

Resultado:

....[app] Reservación creada: R001 (hotel=H001, customer=C001)
........[app] Reservación creada: R001 (hotel=H001, customer=C001)
[app] Reservación creada: R002 (hotel=H001, customer=C001)
...............................
----------------------------------------------------------------------
Ran 43 tests in 0.165s

OK
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
Source\__init__.py              0      0   100%
Source\app.py                  94      1    99%   242
Source\models.py               81      6    93%   35, 37, 51-52, 85-86
Source\storage.py             198     29    85%   56-57, 86-87, 94-95, 154, 159, 184-186, 193-195, 249-250, 310-312, 327-328, 368-372, 393-395, 479-481
Test\Unit\test_app.py         150      1    99%   295
Test\Unit\test_models.py       42      1    98%   136
Test\Unit\test_storage.py     152      1    99%   290
---------------------------------------------------------
TOTAL                         717     39    95%

El reporte detallado se almacena en:

Results/CoverageReport 2 - app/

---

## 4. Pruebas Funcionales Manuales

La evidencia de ejecución manual se encuentra en:
Results/Functional/run_manual.txt

### Caso 1 – Reserva Exitosa

Entrada:
- hotel_id válido
- customer_id válido
- disponibilidad > 0

Resultado esperado:
- Se crea reservación con status "active"
- rooms_available decrementa en 1

Resultado obtenido:
- Comportamiento correcto.


### Caso 2 – Reserva sin disponibilidad

Entrada:
- hotel_id válido
- customer_id válido
- rooms_available = 0

Resultado esperado:
- No se crea reservación
- Mensaje en consola indicando falta de disponibilidad

Resultado obtenido:
- Comportamiento correcto.


### Caso 3 – Cancelación Exitosa

Entrada:
- reservation_id activo

Resultado esperado:
- status cambia a "cancelled"
- rooms_available incrementa en 1

Resultado obtenido:
- Comportamiento correcto.


### Caso 4 – Cancelación inválida

Entrada:
- reservation_id inexistente o no activo

Resultado esperado:
- No se modifica información
- Se muestra mensaje en consola

Resultado obtenido:
- Comportamiento correcto.


Fecha de ejecución: 21/02/2026  
Entorno: Windows 11, Python 3.11

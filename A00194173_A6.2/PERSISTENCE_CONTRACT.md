# PERSISTENCIA.md

A6.2 -- Sistema de Reservaciones de Hotel\
Definición Formal del Contrato de Persistencia

------------------------------------------------------------------------

## 1. Ubicación de la Persistencia

Todos los datos persistentes del sistema se almacenarán en:

A00194173_A6.2/Results/Store/

El sistema deberá:

- Crear automáticamente la carpeta `Results/Store/` si no existe.
- Crear automáticamente los siguientes archivos con una lista vacía
    `[]` si no existen.
- Garantizar que todos los cambios se reflejen inmediatamente en los
    archivos correspondientes.

Archivos persistentes:

- hotels.json
- customers.json
- reservations.json

------------------------------------------------------------------------

## 2. Formato y Generación de Identificadores (IDs)

Cada entidad debe cumplir el siguiente formato:

  Entidad       Prefijo   Ejemplo
  ------------- --------- ---------
  Hotel         H         H001
  Cliente       C         C001
  Reservación   R         R001

Reglas:

- Formato: 1 letra mayúscula + 3 dígitos.
- IDs deben ser únicos dentro de su entidad.
- Generación incremental por entidad.
- No reutilización después de eliminación.
- IDs inválidos deben reportarse e ignorarse.

------------------------------------------------------------------------

## 3. Definición de Estructuras JSON

Todos los archivos JSON deben contener una lista de objetos.

### 3.1 hotels.json

``` json
[
  {
    "hotel_id": "H001",
    "name": "Hotel Central",
    "location": "Monterrey",
    "rooms_total": 50,
    "rooms_available": 50
  }
]
```

Campos obligatorios:

- hotel_id (string)
- name (string)
- location (string)
- rooms_total (integer \> 0)
- rooms_available (integer \>= 0 y \<= rooms_total)

Restricciones:

- rooms_total > 0
- rooms_available >= 0
- rooms_available <= rooms_total
- No se permiten IDs duplicados
- Registros inválidos deben reportarse e ignorarse

------------------------------------------------------------------------

### 3.2 customers.json

``` json
[
  {
    "customer_id": "C001",
    "name": "Ana Perez",
    "email": "ana@example.com"
  }
]
```

Campos obligatorios:

- customer_id (string)
- name (string no vacío)
- email (string no vacío)

Restricciones:

- No se permiten IDs duplicados
- Email debe ser un string no vacío
- Registros inválidos deben reportarse e ignorarse

------------------------------------------------------------------------

### 3.3 reservations.json

``` json
[
  {
    "reservation_id": "R001",
    "hotel_id": "H001",
    "customer_id": "C001",
    "status": "active"
  }
]
```

Campos obligatorios:

- reservation_id (string)
- hotel_id (debe existir en hotels.json)
- customer_id (debe existir en customers.json)
- status: "active" \| "cancelled"

Restricciones:
- hotel_id debe existir en hotels.json
- customer_id debe existir en customers.json
- status solo puede ser:
    - "active"
    - "cancelled"
- No se permiten IDs duplicados
- Registros inconsistentes deben reportarse e ignorarse

------------------------------------------------------------------------

## 4. Reglas de Consistencia

### Reservar una habitación

El sistema deberá:

1. Verificar que el hotel exista.
2. Verificar que el cliente exista.
3. Verificar que rooms_available > 0.
4. Generar un nuevo reservation_id válido.
5. Crear la reservación con estado "active".
6. Disminuir rooms_available en 1.
7. Persistir los cambios en ambos archivos correspondientes.

### Cancelar reservación

1. Verificar reservación activa.
2. Verificar que su estado sea "active"
3. Cambiar estado a "cancelled".
4. Incrementar rooms_available en 1.
5. Persistir cambios.

------------------------------------------------------------------------

## 5. Política de Eliminación

1. Delete Hotel: elimina físicamente el registro del archivo.
2. Delete Customer: elimina físicamente el registro del archivo.
3. Delete Reservation: no aplica (usar cancelación).
4. No se implementará borrado lógico.

------------------------------------------------------------------------

## 6. Política de Manejo de Datos Inválidos

Si se detectan:

- Llaves faltantes
- Tipos de datos incorrectos
- IDs mal formados
- JSON corrupto
- Referencias inválidas

Entonces:

- Reportar error en consola
- Ignorar registro inválido
- Continuar ejecución
- El sistema no debe finalizar abruptamente por un error individual.

------------------------------------------------------------------------

## 7. Garantía de Persistencia

Todas las operaciones deben:

1.  Cargar estado actual desde archivo
2.  Aplicar modificaciones en memoria
3.  Guardar el nuevo estado en el  archivo correspondiente

Los cambios deben permanecer entre ejecuciones.

------------------------------------------------------------------------

## 8. Estrategia de Datos para Pruebas

Pruebas Unitarias:

- Fixtures almacenados en Test/Unit/Data/
- Copia a directorio temporal durante ejecución, no se modifican los fixtures originales

Pruebas Funcionales:

- Datos en Test/Functional/SampleData/
- Resultados generados en Results/

------------------------------------------------------------------------

Fin del Documento

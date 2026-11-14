# Contrato compartido Badi, versión 4: ampliación V2

Proyecto `pastillerobadi`; Realtime Database `https://pastillerobadi-default-rtdb.firebaseio.com`, us-central1, Spark. Paquete Android `mx.edu.badi.pastillero`. Los números son distintos: versión del documento 4, protocolo del programa 2, esquema Room 4 y APK 2.0-simulacion.

## Ruta V2 vigente

Base: `devices/pastillero-01/v2`. Las identidades ownerUid/deviceUid y access/users siguen en sus rutas anteriores; no se duplican cuentas ni se conceden permisos administrativos a clientes. V1 permanece como anexo de compatibilidad y sus reglas previas se conservan semánticamente.

| Ruta relativa V2 | Lee | Escribe | Finalidad y protección |
|---|---|---|---|
| program | Responsable/dispositivo vinculados habilitados | Responsable vinculado habilitado | Transacción revisión +1, token de edición, modo, geometría y ocurrencias validadas |
| state | Ambos vinculados habilitados | Dispositivo vinculado habilitado | Fase, hora, modo, revisión aplicada y estados de periféricos; no confirma ingestión |
| commandRequests/ID | Ambos vinculados habilitados | Responsable vinculado habilitado | Solo PING/APPLY_PLAN, TTL máximo diez minutos, contenido inmutable por ID |
| commandResults/MODO/ID | Ambos vinculados habilitados | Dispositivo vinculado habilitado | Resultado separado y ligado a una solicitud previa del mismo modo; inmutable |
| events/ID | Ambos vinculados habilitados | Dispositivo vinculado habilitado | STARTED/CONFIRMED/MISSED/BLOCKED/RECOVERY/NO_EXIT; ID contiene dosis, marca SIM cuando corresponde y tipo |

En todas las autorizaciones se comprueba auth no nulo, enabled=true, UID vinculado y auth_time posterior a revokedAt. Raíz .read/.write=false. Las cuentas ordinarias no cambian permisos ni se promueven a administrador. Un cambio de modo del programa requiere retirar antes las dosis del modo anterior. La lectura del dispositivo hereda la autorización del padre, no una regla pública nueva.

## Ejemplo de programa, datos didácticos que no se importan

```json
{
  "version": 2,
  "revision": 1,
  "token": "edicion-ejemplo",
  "targetMode": "simulation",
  "positions": 5,
  "windowStart": 1800000000000,
  "windowEnd": 1800086400000,
  "settings": {
    "positions": 5, "horizonDays": 1, "pumpDurationMs": 2000,
    "ledEnabled": true, "buzzerEnabled": true,
    "lcdEnabled": false, "exitSensorEnabled": false,
    "servoEnabled": false, "pumpEnabled": false
  },
  "regimens": {
    "pauta-ejemplo": {
      "id": "pauta-ejemplo", "name": "Material de ensayo",
      "mode": "daily", "times": ["08:00"], "zoneId": "America/Mexico_City",
      "compartment": 4, "intervalMinutes": 480,
      "startAt": 1799990000000, "endAt": 0, "enabled": true
    }
  },
  "doses": {
    "ocurrencia-ejemplo": {
      "scheduledAt": 1800007200000, "compartment": 4,
      "medicationId": "pauta-ejemplo"
    }
  }
}
```

Las fechas/IDs anteriores solo ilustran tipos; los IDs reales se derivan de pauta, instante y compartimento. El ejemplo no afirma corresponder a una expansión real de esa hora. Todos los timestamps son enteros UTC en milisegundos. Cada pauta conserva su zona IANA. startAt es inclusivo, endAt=0 sin fin o límite exclusivo. daily admite 1..6 horas únicas; interval se ancla en su inicio con 15..10080 minutos. Android valida la zona mediante java.time. Las reglas comprueban tipo/longitud de la zona, no la base completa IANA.

Cinco posiciones significan cero vacío y cuatro dosis 1..4. El selector 4 mantiene compatibilidad con tres dosis útiles; nunca habilita cero como dosis. program.settings.positions debe coincidir con program.positions. La ventana es de 1..7 días, con máximo 96 ocurrencias y 12 pautas en Android. Los límites de cantidad se comprueban en clientes/firmware; las reglas no inventan una API numChildren de Realtime Database. El firmware limita el cuerpo a 48000 bytes y rechaza planes que excedan capacidad. No hay publicación continua automática al terminar la ventana.

Una dosis ya existente conserva scheduledAt, compartment y medicationId para el mismo ID. Cambiar esos datos requiere otra identidad. Quitar una definición de una ventana futura no borra eventos ni reservas de NVS. Las listas/objetos vacíos no existen como nodos en RTDB: ausencia de regimens/doses representa programa sin ocurrencias, no una orden de dispensación.

## Estado y eventos V2

state añade protocolVersion=2, positions, exitDetected, pumpActive y servoOpen a phase/calibrated/appliedRevision/updatedAt/simulation/storageHealthy/blisterPresent. Las entradas son tipos estrictos; un dato inválido se rechaza. No se toma un estado antiguo como conexión reciente.

Los eventos conservan doseId, type, scheduledAt, actualAt, compartment y simulation; medicationId enlaza la pauta y puede estar vacío en un evento V1 recuperado desde NVS. NO_EXIT significa ausencia de flanco de salida válido, no omisión confirmada ni ingestión. Las confirmaciones solo provienen del botón; el frontend no puede fabricar eventos del dispositivo. Los resultados de comando y las confirmaciones de dosis son rutas y hechos diferentes.

## Validación y despliegue

Las reglas locales `firebase/database.rules.json` se publicaron en PastilleroBadi tras confirmación. Evidencia: captura `reports/firebase-v2-rules-published.png`, 37 pruebas en emulador de reglas, sondeo REST V2 y SDK Android real registrados en RESULTADOS.md. Los sondeos reales solo escriben PING/resultados qa-* en simulation; no crean horarios ni eventos de dispensación. El firmware ESP32 con red no se ejecutó sobre hardware.

---

# Anexo: contrato V1 conservado

Proyecto dedicado: **PastilleroBadi**, identificador **pastillerobadi**. Base: `https://pastillerobadi-default-rtdb.firebaseio.com`, región `us-central1`. Plan Spark, sin facturación habilitada. Android: `mx.edu.badi.pastillero`. La vista clásica V1 conserva este contrato; la interfaz React móvil usa V2.

Todas las fechas son enteros UTC en milisegundos desde Unix. La interfaz Android muestra la zona horaria del teléfono. Los horarios son ocurrencias de fecha concreta, no recurrencias implícitas. El compartimento 0 es el punto de retorno; los compartimentos 1, 2 y 3 dispensan. No se cambia la secuencia original `1→0, 2→0, 3→0`.

```json
{
  "access": {
    "users": {
      "UID_RESPONSABLE": {"role": "owner", "enabled": true, "revokedAt": 0, "version": 1},
      "UID_ESP32": {"role": "device", "enabled": true, "revokedAt": 0, "version": 1}
    }
  },
  "devices": {
    "pastillero-01": {
      "ownerUid": "UID_RESPONSABLE",
      "deviceUid": "UID_ESP32",
      "plan": {
        "targetMode": "simulation",
        "revision": 1,
        "token": "UUID_DEL_BORRADOR",
        "doses": {
          "UUID_DOSIS": {"scheduledAt": 1800000000000, "compartment": 1}
        }
      },
      "state": {
        "phase": 0, "calibrated": false, "appliedRevision": 1,
        "updatedAt": 1799999999000, "simulation": true,
        "storageHealthy": true, "blisterPresent": true
      },
      "commandRequests": {
        "UUID_COMANDO": {
          "type": "APPLY_PLAN", "requestedBy": "UID_RESPONSABLE",
          "requestedAt": 1799999999000, "expiresAt": 1800000599000,
          "targetMode": "simulation", "planRevision": 1
        }
      },
      "commandResults": {
        "simulation": {
          "UUID_COMANDO": {
            "status": "COMPLETED", "reason": "OK",
            "requestedAt": 1799999999000, "executedAt": 1800000000000,
            "planRevision": 1, "simulation": true
          }
        }
      },
      "events": {
        "UUID_DOSIS-SIM-CONFIRMED": {
          "doseId": "UUID_DOSIS", "type": "CONFIRMED",
          "scheduledAt": 1800000000000, "actualAt": 1800000030000,
          "compartment": 1, "simulation": true
        }
      }
    }
  }
}
```

El JSON es ilustrativo: sus marcadores y fechas no constituyen datos que deban importarse ni pruebas ejecutadas. El archivo de reglas es `firebase/database.rules.json`.

El plan lleva un destino obligatorio. El firmware solo acepta su modo de compilación y cancela su plan futuro almacenado si recibe un plan de otro destino. Para cambiar `targetMode` hay que retirar antes todos los horarios del plan anterior. Room conserva también el destino del borrador; un borrador de simulación no se envía como hardware al cambiar de configuración.

La base Room es versión 3: migración 1→2 agrega comandos y 2→3 agrega el destino del borrador con valor inicial `simulation`. Ninguna borra el historial. Antes de importar la caché del SDK Firebase en Room, Android comprueba que el UID actual coincide con `ownerUid`; así evita importar datos cacheados bajo una cuenta distinta al cambiar de sesión.

## Acceso por ruta

| Ruta bajo `/devices/$device` | Lectura | Escritura desde aplicaciones |
|---|---|---|
| `ownerUid`, `deviceUid` | Las dos identidades vinculadas | Nadie; aprovisionamiento en consola administrativa |
| `plan` | Responsable y dispositivo vinculados | Solo responsable; revisión consecutiva y token estable |
| `state` | Ambos | Solo dispositivo; esquema cerrado |
| `commandRequests/$id` | Ambos | Solo responsable; creación inmutable, repetición idéntica permitida |
| `commandResults/$mode/$id` | Ambos | Solo dispositivo; solicitud existente, modo coincidente e inmutabilidad |
| `events/$id` | Ambos | Solo dispositivo; creación inmutable, repetición idéntica permitida |
| Otras rutas | Denegada | Denegada |

La regla de lectura se concede en el nodo del dispositivo únicamente a sus dos UID. No existe permiso global para cualquier usuario autenticado. Registrarse en Authentication no otorga acceso a un dispositivo. Ningún cliente puede cambiar sus vínculos ni escalar privilegios. La consola utiliza la sesión administrativa del propietario; el APK y el firmware no contienen cuentas de servicio ni claves de administrador.

## Comandos y confirmaciones

`PING` solicita una respuesta de conexión y requiere `planRevision=0`. `APPLY_PLAN` solicita comprobar que el dispositivo ya persistió una revisión igual o posterior a la indicada; requiere revisión positiva. Android lo agrega después de confirmar la transacción del plan. Ninguno inicia movimiento, calibra ni confirma una toma.

Cada comando tiene ID alfanumérico/guion de hasta 36 caracteres, UID solicitante, instante de creación, caducidad máxima de diez minutos y destino `simulation` o `hardware`. Android usa `simulation` por defecto. El firmware espera la aplicación del plan antes de responder. Devuelve `COMPLETED/OK` o `REJECTED` con una causa definida en `firmware/PastilleroESP32/PastilleroESP32.ino`. Los destinos de simulación y físicos son independientes.

Room conserva la solicitud antes del envío. Un reinicio o pérdida de conexión repite el mismo ID y payload. Las reglas rechazan modificaciones y eliminaciones de solicitudes/resultados. El firmware persiste la respuesta en NVS antes de enviarla; solo la retira de su cola después del acuse de Firebase. El resultado en la nube evita reprocesar solicitudes antiguas. Si se pierde una escritura y su acuse, se reintenta exactamente la misma respuesta.

La tarea de red consulta las últimas 32 solicitudes y 64 respuestas, con índices de tiempo. Son límites operativos para un pastillero, no un canal de control masivo: mantener menos de 32 comandos pendientes. Un exceso puede dejar solicitudes antiguas sin atender, hasta caducar. La cola NVS admite 16 respuestas pendientes y deja de aceptar nuevas cuando se llena.

## Eventos, alertas e historial

`events` es el registro histórico inmutable: `STARTED`, `CONFIRMED`, `MISSED`, `BLOCKED` y `RECOVERY`. Las confirmaciones son los eventos `CONFIRMED`; las alertas son `MISSED`, `BLOCKED` y `RECOVERY`. Son vistas por tipo sobre un único registro de eventos, evitando copias inconsistentes entre nodos de confirmaciones, alertas e historial.

ID físico: `doseId-TYPE`; ID de simulación: `doseId-SIM-TYPE`. Un acuse de comando jamás significa confirmación de toma. Los eventos simulados se identifican en pantalla y no suman adherencia médica. Room conserva hasta los eventos recibidos y consulta los últimos 500 para la pantalla; la base no se vacía al cerrar sesión o migrar.

La omisión se registra a los cinco minutos. El controlador exige una nueva pulsación del botón físico; mantenerlo presionado antes de dispensar no confirma automáticamente. Tras reinicio con operación activa se registra recuperación y se requiere revisión/calibración, sin repetir automáticamente la dosis reservada.

## Límites y configuración

Máximo 24 dosis en un plan y diez minutos de separación: Android y el firmware validan estos límites. Las reglas validan campos, revisiones, tiempos e identidad, pero no cuentan todas las dosis ni comparan cada par de horarios. Un cliente autorizado alterado podría publicar un plan que el firmware rechazará. El estado `appliedRevision` es la evidencia de aplicación, no la revisión que muestra el teléfono como enviada.

La misma cuenta de dispositivo puede declarar `simulation=false`; la marca de simulación no es una atestación de hardware. Antes de pruebas físicas, detener simuladores y controlar personalmente el firmware instalado y las credenciales. No hay acceso anónimo a datos ni movimiento remoto directo.

Authentication usa correo/contraseña separado para responsable y ESP32. ESP32 renueva el token mediante REST sobre TLS con certificados raíz, reconecta Wi-Fi y ejecuta la red en una tarea independiente. No se desactiva la verificación TLS. Android usa SDK Firebase asíncrono, Room en un ejecutor y WorkManager con requisito de red y reintentos.

Referencias oficiales: [reglas y autenticación](https://firebase.google.com/docs/database/security/rules-conditions), [migraciones Room que conservan datos](https://developer.android.com/training/data-storage/room/migrating-db-versions).

## Administración y revocación

Cada acceso a un dispositivo requiere UID vinculado, `access/users/<uid>/enabled=true` y `auth.token.auth_time > revokedAt`. `revokedAt` se mide en segundos Unix; las fechas de dosis/eventos siguen en milisegundos. Solo el servidor administrativo o Firebase Console modifica los permisos y los vínculos. El cliente puede leer únicamente su propio registro de acceso, incluso si está bloqueado, para mostrar el motivo. Una cuenta ordinaria no puede administrar usuarios, leer todo `devices` ni consultar `administration`.

El registro admite además `features` opcional (`medications`, `publish`, `deviceSettings`, `diagnostics`, booleanos) escrito solo por el backend administrativo. Un `false` bloquea esa funcionalidad en la app del responsable; ausencia equivale a permitido. Las reglas no lo evalúan: ver ADMINISTRACION_WEB.md.

El backend reservado al dashboard verifica el UID principal y el custom claim `dashboardAdmin`, así como la revocación de la sesión. El SDK Admin opera en el servidor; los clientes web no reciben privilegios de base globales. API, auditoría, protección del administrador y activación pendiente: `ADMINISTRACION_WEB.md`. No se ha desarrollado React.


El modelo de control y el validador de comandos están en el único PastilleroESP32.ino. Las pruebas lo incluyen directamente con PASTILLERO_HOST_TEST; no utilizan cabeceras propias. La unificación conserva el contrato JSON y Room4. Consultar UNIFICACION_FIRMWARE.md y las guías por línea.

## Integración local añadida

INTEGRACION_SOFTWARE.md recorre doce pruebas conectadas de ScheduleEngine (JVM), reglas Firebase locales, Controller del .ino y registro JSON compartido, más seis regresiones de propiedad de cadenas/reservas. Se corrigió la referencia a arreglos const que podía cambiar eventos o IDs reservados al reutilizar la dosis activa. writeDoseEvent/reserveDoseId fuerzan copias con longitud real; los casos verifican varias dosis y restauración del documento. El total acumulado queda en 192, con 27 casos añadidos al cierre de 165. No equivale a ejecutar UI/WorkManager ni ESP32 físico; no cambian las reglas publicadas o el contrato de datos.

La persistencia ESP32 se corrigió además a blobs NVS: snapshot-v2 + marcador snapshot-ver, límite local de 48000 bytes y lectura compatible de la cadena histórica. No se usa putString para documentos grandes ni se vuelve a una copia antigua si falta el bloque marcado. Ocho pruebas nuevas verifican estas funciones compartidas con un doble RAM, incluido un programa de 96 dosis mayor de 4000 bytes; la flash física, cortes de energía y RECOVERY del adaptador Arduino no se ejecutaron. INTEGRACION_SOFTWARE.md detalla la migración conservadora y sus límites.


Revisión del 22 de octubre de 2026: la configuración y los certificados están dentro del .ino; los datos locales se materializan mediante generate_private_firmware.py. La carpeta del sketch contiene solo .ino y partitions.csv. Referencia elegida, procedimiento privado y evidencia: COMPARACION_CRUDSQLITE1.md y UNIFICACION_FIRMWARE.md.

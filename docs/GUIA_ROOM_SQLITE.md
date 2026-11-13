# Guía de Room y SQLite

## 1. Las tres piezas

SQLite almacena tablas en el archivo privado `pastillero.db` del teléfono. Room genera el código que relaciona esas tablas con objetos Java y consultas declaradas. La Activity muestra los datos observados; no ejecuta SQL de disco directamente al pulsar un botón.

| Pieza propia | Función |
|---|---|
| `DoseEvent.java`, `PlanDraft.java`, `CommandRequest.java` | Entidades: columnas y claves |
| `PastilleroDao.java` | Contrato de inserciones, consultas y actualizaciones |
| `PastilleroDatabase.java` | Instancia de base y migraciones 1→2→3→4 |
| `Repository.java` | Trabajo de disco en ejecutor y conexión con LiveData/Firebase |
| `SyncWorker.java`, `CommandWorker.java` | Consumen la cola persistente y registran acuses |
| `RoomOfflineTest.java` | Demuestra conservación y aislamiento con bases temporales |

La relación con CRUDSQLITE1 es deliberada: entidad → DAO → base → ejecutor → callback/pantalla. Allí `RoomManager` concentraba operaciones de sensores; aquí `Repository` y los Workers añaden un protocolo de sincronización y permisos, conservando separación de responsabilidades. Se adopta su lectura por secciones y comentarios en español, sin copiar su proyecto ni modificarlo.

Room genera implementaciones durante la compilación, a partir de entidades y DAO. No hay que escribir ni editar `PastilleroDao_Impl` o `PastilleroDatabase_Impl`. [Referencia oficial de DAOs](https://developer.android.com/training/data-storage/room/accessing-data).

## 2. Tipos básicos

| Java | SQLite usado | Ejemplo del proyecto |
|---|---|---|
| `String` | `TEXT` | UUID, JSON, estado |
| `long` | `INTEGER` | Milisegundos UTC y revisión |
| `int` | `INTEGER` | Compartimento |
| `boolean` | `INTEGER` | 0/1 para simulation, dirty y sent |
| `@NonNull` | `NOT NULL` | La columna no admite SQL NULL |

Una cadena vacía `""` no es NULL: la primera es un texto existente sin caracteres; NULL representa ausencia de valor. Por ejemplo, `resultJson=''` significa que todavía no se almacenó una respuesta final.

Room no añade cifrado de base por sí solo. La base está en el almacenamiento privado de Android y los respaldos automáticos están deshabilitados/excluidos; esta entrega no incluye SQLCipher. No se guarda la contraseña de Firebase en las entidades.

## 3. Tabla dose_events

| Columna | Significado |
|---|---|
| `scope` | Cuenta y dispositivo: `uid:deviceId` |
| `eventId` | Identidad completa de evento, con modo/tipo |
| `doseId` | Identidad común de la dosis |
| `type` | STARTED, CONFIRMED, MISSED, BLOCKED, NO_EXIT o RECOVERY |
| `scheduledAt` | Hora programada, milisegundos UTC |
| `actualAt` | Hora registrada, milisegundos UTC |
| `compartment` | V2: posición 1..4; V1 conserva 1..3 |
| `simulation` | Distingue prueba de evento físico |

Su clave primaria es **(scope, eventId)**. Dos cuentas no comparten filas, y recibir el mismo evento dos veces no debe insertar dos registros. `@Insert(onConflict=IGNORE)` devuelve -1 ante repetición; el repositorio solo notifica cuando la inserción fue nueva.

Ejemplo didáctico: evento programado a 1800000000000 y registrado a 1800000090000 tiene diferencia de 90000 ms, noventa segundos. `PlanCodec.delay()` calcula esa resta. `PlanCodec.confirmed()` exige tipo CONFIRMED y `simulation=false`; una prueba no aumenta el conteo de confirmaciones reales.

## 4. Tabla plan_drafts

| Columna | Significado |
|---|---|
| `scope` | Clave primaria: un borrador por cuenta/dispositivo |
| `json` | Objeto de dosis serializado como texto |
| `token` | UUID de esa edición; aquí no es un token de autenticación |
| `status` | Mensaje visible de pendiente, conflicto o sincronizado |
| `baseRevision` | Revisión remota sobre la que se editó |
| `dirty` | Hay una edición local todavía sin acuse |
| `targetMode` | Destino simulation/hardware; por defecto simulation |

REPLACE se usa para guardar **el borrador**, no para reemplazar el historial. El Worker toma una edición, confirma Firebase y limpia dirty solo si su UUID sigue coincidiendo. Si mientras tanto la persona hizo otra edición, el acuse anterior no la marca erróneamente como enviada.

Un borrador offline puede sobrevivir al cierre y reinicio de Android. Eso no garantiza que una fecha todavía sea futura al volver la red: las reglas y el firmware pueden rechazarla. La persona debe corregir el plan o resolver el conflicto, no dispensar retrospectivamente para compensarlo.

## 5. Tabla command_requests

| Columna | Significado |
|---|---|
| `scope`, `commandId` | Clave primaria compuesta que impide duplicar la solicitud |
| `json` | Tipo PING/APPLY_PLAN, revisión, modo, solicitante y fechas |
| `status` | Estado de envío o resultado visible |
| `resultJson` | Respuesta remota separada de la petición |
| `createdAt` | Orden cronológico de la cola |
| `sent` | La solicitud ya fue enviada/acuse conocido; no significa toma confirmada |

`CommandWorker` comprueba primero si la solicitud ya existe en Firebase. Si coincide el contenido, reconoce el envío anterior; si el UUID tiene otro contenido marca conflicto. Solo vence localmente una solicitud no existente cuya caducidad ya pasó. Los reintentos no crean una identidad nueva.

## 6. Todas las consultas del DAO

### pendingCommands(scope)

```sql
SELECT * FROM command_requests
WHERE scope=:scope AND sent=0
ORDER BY createdAt
```

`SELECT *` recupera todas las columnas de la entidad. `WHERE` exige la cuenta/dispositivo y la marca pendiente. `AND` exige ambas condiciones. Orden ascendente de creación atiende primero lo más antiguo. Devuelve una lista para el Worker, no un observador de pantalla.

### observeCommands(scope)

```sql
SELECT * FROM command_requests
WHERE scope=:scope
ORDER BY createdAt DESC LIMIT 50
```

Devuelve LiveData con cincuenta solicitudes recientes. DESC pone primero la más nueva. LIMIT controla presentación: no ejecuta DELETE ni reduce la tabla. Las solicitudes antiguas siguen guardadas.

### commandStatus(scope, id, status, sent)

```sql
UPDATE command_requests SET status=:status,sent=:sent
WHERE scope=:scope AND commandId=:id AND resultJson=''
```

UPDATE cambia columnas de filas existentes. La pareja scope/ID elige una sola solicitud. El último AND evita que un acuse tardío de envío sustituya el estado final que ya llegó en `resultJson`.

### commandResult(scope, id, status, json)

```sql
UPDATE command_requests SET status=:status,resultJson=:json,sent=1
WHERE scope=:scope AND commandId=:id
```

Guarda la respuesta y deja el envío confirmado. No cambia el JSON de solicitud ni inserta una confirmación de dosis. Un resultado PING/OK prueba el canal de comandos, no una toma.

### observeEvents(scope)

```sql
SELECT * FROM dose_events WHERE scope=:scope
ORDER BY actualAt DESC, eventId DESC LIMIT 500
```

Ordena por fecha registrada; si dos fechas coinciden, la clave del evento decide un orden estable. Devuelve hasta quinientas filas a la pantalla, conservando todas las demás. LiveData comunica cambios sin consultar mediante un bucle del botón.

### draft(scope) y observeDraft(scope)

Ambos métodos usan:

```sql
SELECT * FROM plan_drafts WHERE scope=:scope
```

`draft()` devuelve una instantánea para trabajar en el ejecutor/Worker. `observeDraft()` devuelve LiveData para la pantalla. La misma consulta SQL admite dos usos de ciclo de vida distintos; no se han omitido por ser iguales sus textos.

### acknowledge(scope, token, revision)

```sql
UPDATE plan_drafts
SET dirty=0, baseRevision=:revision, status='Sincronizado con Firebase'
WHERE scope=:scope AND token=:token
```

Solo el borrador todavía identificado por el token enviado recibe el acuse. Un token diferente significa que hubo una edición posterior y esa fila no debe cambiar.

### status(scope, token, status)

```sql
UPDATE plan_drafts SET status=:status
WHERE scope=:scope AND token=:token
```

Informa un error o conflicto sin borrar el JSON, sin limpiar dirty y sin afectar otra edición.

Los parámetros `:scope`, `:id`, `:token` y demás no son sustitución manual de texto SQL: Room enlaza los argumentos. Por eso no se construye una consulta concatenando el correo o datos escritos por la persona.

## 7. Inserciones y claves

`insertEvent()` e `insertCommand()` usan IGNORE para no duplicar eventos/solicitudes. `saveDraft()` usa REPLACE solo sobre scope. INSERT añade una fila, SELECT consulta, UPDATE modifica columnas y una clave primaria prohíbe repetir su identidad. No hay una operación DAO que borre todo el historial para resolver una reconexión.

`@Dao` declara el contrato; `@Entity` define tabla/clave; `@Database` reúne entidades y versión; `@Query` asocia SQL con un método; `@Insert` selecciona su estrategia. Las líneas y argumentos de cada anotación se recorren en `GUIA_ANDROID_LINEA_POR_LINEA.md`.

## 8. Migraciones y conservación

La base actual es versión **4** y el APK es 2.0-simulacion, código 7. Aumenta el esquema porque se incorporaron pautas, preferencias y cola V2; no por los comentarios.

MIGRATION_1_2 crea la tabla `command_requests` con campos no nulos y clave `(scope,commandId)`. No elimina `dose_events` ni `plan_drafts`. MIGRATION_2_3 ejecuta:

```sql
ALTER TABLE plan_drafts
ADD COLUMN targetMode TEXT NOT NULL DEFAULT 'simulation'
```

ALTER amplía la tabla; ADD COLUMN añade la columna; NOT NULL exige valor; DEFAULT rellena las filas antiguas. `.addMigrations(1→2,2→3,3→4)` permite abrir versiones 1 y 2 sin sustituir la base por una vacía. No se utiliza `fallbackToDestructiveMigration()`.

La prueba reconstruye cada esquema antiguo desde `app/schemas/`, inserta historial y borrador de ejemplo, abre la versión actual y verifica fechas, token, dirty y modo. Después prueba solicitudes duplicadas, reapertura y aislamiento. El esquema exportado es generado por Room y sirve de evidencia, no es otra clase escrita a mano. [Referencia de migraciones](https://developer.android.com/training/data-storage/room/migrating-db-versions).

## 9. Hilos, desconexión y permisos

La Activity observa LiveData. Repository usa un ejecutor de un hilo para DAO. Workers ejecutan su trabajo fuera del hilo principal y pueden esperar con límite el acuse asíncrono. No se habilita `allowMainThreadQueries()` para simplificar.

Una cuenta bloqueada pierde acceso remoto y se cancelan sus trabajos observados, pero los datos ya descargados permanecen en SQLite. Cerrar sesión cambia el scope mostrado, no borra el archivo. La caché Firebase y Room cumplen funciones distintas: el historial y la cola deben seguir siendo explícitos, aislados y verificables en Room.

## 10. Ejercicio para la defensa

Explica este caso sin ejecutar hardware: se edita un horario offline, se cierra la app y vuelve la red. Señala el registro `plan_drafts`, dirty, baseRevision y token; después la transacción del Worker, el acuse condicional y la actualización LiveData. Añade qué sucede si otro editor avanzó la revisión: hay conflicto, no reemplazo silencioso.

Segundo caso: llega dos veces el mismo evento. Señala `(scope,eventId)`, IGNORE y el valor -1; se conserva una fila y no se repite el aviso. Tercer caso: se migra de versión 1; identifica los tres pasos sin borrar historial. Las evidencias ejecutadas están en `RESULTADOS.md`.

## 11. Ampliación V2: Room 4, seis entidades

`Medication`/medications conserva (scope,medicationId), name, mode, timesJson, zoneId, compartment, intervalMinutes, startAt, endAt y enabled. El historial añade medicationId con DEFAULT ''. No se crea una clave foránea con borrado en cascada: quitar una pauta no destruye las evidencias de entregas anteriores.

`DevicePreferences`/device_preferences conserva un registro por scope: positions=5, horizonDays=7, pumpDurationMs=2000, LED y buzzer habilitados, periféricos nuevos deshabilitados. `ProgramOutbox`/program_outbox conserva scope, json, token, status, baseRevision, dirty y edited. edited distingue una edición local de una ventana ya preparada para publicar (dirty). El token de edición no es una credencial Firebase.

MIGRATION_3_4 añade protocolVersion INTEGER NOT NULL DEFAULT 1 a command_requests y medicationId TEXT NOT NULL DEFAULT '' a dose_events; después crea las tres tablas nuevas. Las filas antiguas siguen siendo V1. Los esquemas 1, 2 y 3 permanecen idénticos; el compilador exporta 4. No se recrea pastillero.db.

### Consultas V2, en orden del DAO

| Método | Operación y significado |
|---|---|
| saveMedication | INSERT/REPLACE de una sola pauta con clave compuesta |
| medications / observeMedications | SELECT del scope, ORDER BY name,medicationId; instantánea de trabajo / LiveData |
| deleteMedication | DELETE exclusivamente en medications WHERE scope=:scope AND medicationId=:id; no toca dose_events |
| savePreferences / preferences | INSERT/REPLACE y SELECT del registro de ajustes de esa cuenta |
| saveProgram / program / observeProgram | Guarda y consulta únicamente la cola V2, separada de plan_drafts |
| acknowledgeProgram | UPDATE dirty=0, revisión y estado WHERE scope=:scope AND token=:token; protege una edición nueva |
| programStatus | UPDATE del estado solo para ese scope/token |
| events | SELECT de las 500 filas recientes por actualAt,eventId; LIMIT no borra las restantes |
| latestV2Command | SELECT protocolVersion=2 ORDER BY createdAt DESC LIMIT 1 para mostrar el último acuse V2 |

DashboardRepository serializa operaciones en un ejecutor; ProgramWorker espera el acuse en el hilo Worker. La pantalla React nunca ejecuta SQL. La reconciliación reload/rebase solo cambia definiciones/base de revisión tras la elección de la persona. Las dos pruebas RoomVersionTwoTest demuestran migración desde 3 con historial/borrador/comando y reapertura de pautas/ajustes/cola, aislamiento y borrado de pauta sin pérdida de eventos. Las tres pruebas RoomOfflineTest siguen cubriendo las versiones anteriores.


Revisión del 22 de octubre de 2026: la configuración y los certificados están dentro del .ino; los datos locales se materializan mediante generate_private_firmware.py. La carpeta del sketch contiene solo .ino y partitions.csv. Referencia elegida, procedimiento privado y evidencia: COMPARACION_CRUDSQLITE1.md y UNIFICACION_FIRMWARE.md.

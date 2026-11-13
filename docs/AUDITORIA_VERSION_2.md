# Auditoría de implementación: PastilleroBadi 1.5 frente a requisitos 2.0

Inspección inicial: 20 de octubre de 2026. Cierre 2.0: 21 de octubre de 2026; unificación: 22 de octubre de 2026. Raíz: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

Se inspeccionaron fuentes Java, XML, Gradle, firmware, reglas JSON y pruebas C++/Java/Node. El estado inicial siguiente corresponde al respaldo previo a cambios registrado en `reports/version2-backup.json`. Los informes de compilación anteriores sirven como evidencia histórica; no se consideran pruebas de funciones que no existían. «Probado» indica el entorno concreto, nunca un movimiento físico inferido de una compilación.

## Diagnóstico de 1.5, antes de implementar 2.0

| # | Requisito | Clasificación inicial | Evidencia en fuentes y límites |
|---:|---|---|---|
| 1 | React + TypeScript en Android y puente seguro | NO IMPLEMENTADO | No había web/, TSX, assets web, WebView, puente ni dependencia androidx.webkit. `MainActivity.java/onCreate()` infla `res/layout/activity_main.xml`. |
| 2 | Liquid Glass, temas, animaciones y navegación | NO IMPLEMENTADO | `res/values/styles.xml` define un tema nativo básico; `activity_main.xml` es una pantalla desplazable con controles. El vector `ic_pastillero.xml` no constituye una interfaz ni un sistema de navegación. |
| 3 | Calendario semanal con fechas reales | IMPLEMENTADO PARCIALMENTE | `MainActivity.chooseDate()` usa Calendar/DatePickerDialog/TimePickerDialog y guarda una fecha real; no existe vista semanal, selección por día ni agrupación semanal. |
| 4 | Medicamentos con horarios e intervalos independientes | NO IMPLEMENTADO | `PlanCodec.doses()` valida únicamente scheduledAt y compartment. `PlanDraft` guarda un JSON de dosis; no hay entidad de medicamento ni regla de recurrencia. |
| 5 | Cuatro o cinco compartimentos configurables | IMPLEMENTADO PARCIALMENTE | `PastilleroESP32.ino/STEPS_PER_SLOT`, `Controller.manualStart()/tick()` y `validDose()` fijan cuatro posiciones, cero reservado y tres dosis. `PlanCodec` y `database.rules.json/plan/doses` limitan compartment a 3. No hay selector 4/5. |
| 6 | Máquina de estados ESP32 | IMPLEMENTADO Y PROBADO | `.ino/pill::Controller::tick()` define Idle, Outward, Drop, Returning, Awaiting, Alert, ManualGap y Fault. `tests/controller_test.cpp` prueba transiciones en PC sin GPIO; no prueba un ESP32 ejecutándose. |
| 7 | NEMA 17 y preparación de servo | IMPLEMENTADO PARCIALMENTE | `.ino/configurarMotorYSensores()`, `AdaptadorMotor.move()/reached()` y `loop()` usan AccelStepper, PUL25/DIR26. No hay pin, PWM, estado ni adaptación de servo. Variantes compiladas; motor físico pendiente. |
| 8 | LCD 16×2 | NO IMPLEMENTADO | No hay Wire, driver LCD, dirección I²C ni funciones de pantalla en las fuentes del firmware. |
| 9 | LED/buzzer configurables | IMPLEMENTADO PARCIALMENTE | `config.h/PIN_BUZZER/PIN_READY/PIN_ALERT` y `.ino/actualizarIndicadores()` usan pines y patrón fijos; no hay preferencias configurables. |
| 10 | Confirmación física por botón | IMPLEMENTADO Y PROBADO | `.ino/leerBotonConfirmacion()` filtra rebotes; `Controller.tick()` exige liberar y volver a pulsar. `controller_test.cpp` verifica botón mantenido y omisión con entrada simulada. Comprobación eléctrica pendiente. |
| 11 | Sensor de salida de pastillas | NO IMPLEMENTADO | `hayBlister()` lee GPIO34 para presencia, no detecta una pastilla saliendo. No debe confundirse presencia con salida ni salida con ingestión. |
| 12 | Bomba de agua opcional | NO IMPLEMENTADO | No hay salida de bomba, habilitación, temporización, enclavamiento ni prueba correspondiente. |
| 13 | Room y migraciones | IMPLEMENTADO Y PROBADO | `PastilleroDatabase` versión3, migraciones1→2→3; `PastilleroDao` y entidades DoseEvent/PlanDraft/CommandRequest. `RoomOfflineTest` prueba migraciones, reapertura, aislamiento y duplicados en API24. |
| 14 | Firebase y offline | IMPLEMENTADO PARCIALMENTE | `Repository`, `SyncWorker`, `CommandWorker`, `.ino/tareaFirebase()/mantenerSesionFirebase()/sincronizarConFirebase()` y NVS. `FirebaseConnectionTest` comprueba SDK Android real, `rules.test.mjs` y sondeo REST permisos/cola. Falta ejecución Wi-Fi/TLS en chip y caída de radio real. |
| 15 | Evitar dispensación duplicada | IMPLEMENTADO Y PROBADO | `.ino/AdaptadorMotor.record()` reserva STARTED y done antes de mover; `restaurarMemoriaPersistente()` registra RECOVERY. `controller_test.cpp`, reglas inmutables en `rules.test.mjs`, claves IGNORE y pruebas Room verifican los componentes con simulación. Persistencia NVS real pendiente. |
| 16 | Pruebas específicas de nuevas funciones | NO IMPLEMENTADO | Existían 74 casos de referencia y 20 comprobaciones REST; no había casos de React, calendario semanal, recurrencias, LCD, servo, salida o bomba. Los casos antiguos no prueban funciones ausentes. |

## Criterios de implementación y conservación

La versión 2.0 conserva Activity/XML, Repository, Room y Workers como capa nativa. React/TypeScript se incorpora como interfaz local del APK; Java mantiene la autoridad sobre Firebase, validación y persistencia. No se entregan tokens ni contraseñas al frontend. Las órdenes remotas no dispensan ni confirman tomas. El sketch original y sus comandos a/r/c/s permanecen recuperables; los cambios del firmware se validarán en PC y compilación, manteniendo simulación.

El punto cero es ciego/de retorno en el modelo anterior. La distinción entre posiciones totales y compartimentos útiles se registra explícitamente: no se supondrá un montaje físico nuevo por cambiar una cifra en pantalla. Periféricos nuevos quedan deshabilitados por defecto y sus niveles/pines requieren validación física posterior.

## Resultado posterior a la implementación

Las referencias siguientes corresponden a las fuentes finales. «IMPLEMENTADO Y PROBADO» siempre especifica el entorno de software; no acredita hardware físico. Se mantiene una clasificación parcial en los requisitos cuyo tramo eléctrico/mecánico o runtime ESP32 sigue sin ejecutarse. No quedan filas clasificadas solo por documentación: los componentes nuevos citados existen en fuentes y tienen pruebas de sus modelos o integración de software.

### 1. React + TypeScript integrado y comunicación Java segura

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `web/src/App.tsx:357`; `app/src/main/java/mx/edu/badi/pastillero/DashboardActivity.java:27`; `app/src/main/java/mx/edu/badi/pastillero/BridgeProtocol.java:16`. Recursos HTTPS locales, un origen permitido, marco principal, tipos y acciones estrictos.
- Pruebas ejecutadas: DashboardBridgeTest (3) sobre APK real, VersionTwoTest: messageFromAnotherOriginIsRejected/iframeIsRejectedEvenAtTrustedOrigin/unknownActionAndAdminFieldsAreRejected; api.test.ts.
- Alcance/límite: WebView antiguo usa alternativa clásica segura; ninguna credencial llega a React.

### 2. Liquid Glass, temas, animaciones y navegación

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `web/src/App.tsx:31`; `web/src/tokens.css`, `web/src/styles.css`, `web/src/Icon.tsx`. Cinco vistas, tema persistente, diálogos y navegación Atrás.
- Pruebas ejecutadas: App.test.tsx (10), seis recorridos Playwright escritorio/Pixel 7; capturas reports/v2-*.png revisadas.
- Alcance/límite: Probado en Chromium y WebView moderno del AVD; no se instaló en el teléfono físico.

### 3. Calendario semanal sincronizado con fechas reales

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `web/src/calendar.ts:6`; `web/src/calendar.ts:21`; `app/src/main/java/mx/edu/badi/pastillero/ScheduleEngine.java:64`. Semana/día reales; Java expande fechas y el repositorio sincroniza definiciones remotas.
- Pruebas ejecutadas: calendar.test.ts (10); VersionTwoTest.dailyWeekHasRealSevenDates/springGapIsSkippedRatherThanShifted/autumnRepeatedHourRunsOnce; Playwright navegación semanal.
- Alcance/límite: La edición online de pautas entre dos APK y el recorrido completo hasta ESP32 no se ejecutaron en nube real; sí reglas/transacciones locales y SDK PING real.

### 4. Medicamentos con horarios e intervalos independientes

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `app/src/main/java/mx/edu/badi/pastillero/Medication.java:10`; `app/src/main/java/mx/edu/badi/pastillero/ScheduleEngine.java:36`; `web/src/App.tsx/MedicationForm`. Horas diarias o intervalo anclado individual, zona, fin y pausa.
- Pruebas ejecutadas: VersionTwoTest.independentDailyTimesArePreserved/intervalIsAnchoredToItsOwnStart/twoMedicinesAtSameTimeRemainIndependent; formularios React y puente real a Room.
- Alcance/límite: Ventana explícita de 1..7 días, máximo 96 ocurrencias/12 pautas; no renovación ilimitada automática.

### 5. Cuatro/cinco posiciones y cero vacío

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:743`; `firmware/PastilleroESP32/PastilleroESP32.ino:945`; `app/src/main/java/mx/edu/badi/pastillero/DevicePreferences.java:11`. Predeterminado confirmado: 5 totales, cuatro dosis y cero vacío.
- Pruebas ejecutadas: version2_test.cpp: geometría, cambio exige recalibrar, destino 2560 y retorno; secuencia completa 640→0/1280→0/1920→0/2560→0. VersionTwoTest.fivePositionsAllowFourthDosePosition y ajustes React.
- Alcance/límite: Alineación/microstepping/precisión mecánica pendientes. Cuatro posiciones solo compatibilidad seleccionable.

### 6. Máquina de estados para dispensación

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:928`; `firmware/PastilleroESP32/PastilleroESP32.ino:972`. Idle, Outward, Drop, Returning, Awaiting, Alert, ManualGap y Fault; loop no espera por red.
- Pruebas ejecutadas: 24 casos históricos C++ y 20 V2, incluyendo dosis simultáneas atendidas en serie y retorno tras cada entrega.
- Alcance/límite: Modelo ejecutado en PC; firmware compilado, no ejecutado en un ESP32.

### 7. Motor NEMA 17 principal y preparación del servo

**IMPLEMENTADO PARCIALMENTE.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:1176`; `AdaptadorMotor.move()/reached()`, configurarMotorYSensores()/actualizarIndicadores(); `PastilleroESP32.ino/PIN_SERVO`. NEMA 17 + TB6600 conserva PUL25/DIR26; servo opcional PWM solo Drop.
- Pruebas ejecutadas: Control en modelos C++, apertura/cierre del servo en version2_test.cpp y compilación de ambas variantes.
- Alcance/límite: NEMA 17 sigue siendo el motor principal; el servo es accesorio de compuerta. Drivers escritos/compilados, señales/potencia/topes y movimiento físicos sin probar.

### 8. LCD 16×2 con alertas/dispensación

**IMPLEMENTADO PARCIALMENTE.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:800`; `firmware/PastilleroESP32/PastilleroESP32.ino:1724`; driver LCD PCF8574/Wire, cola de cuadros separada de loop. Mensajes de entrega, omisión, salida y recuperación.
- Pruebas ejecutadas: version2_test.cpp verifica texto de 16 caracteres y causas NO_EXIT/MISSED; ambas variantes compilan con Wire/driver.
- Alcance/límite: No se ejecutó el bus I2C ni se validaron dirección/mapa/tensión del backpack. Disponibilidad local=0.

### 9. LED y buzzer configurables

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:775`; `firmware/PastilleroESP32/PastilleroESP32.ino:800`; `DashboardRepository/savePreferences`, ajustes React y reglas V2.
- Pruebas ejecutadas: version2_test.cpp: toggles y patrón temporal; VersionTwoTest/preferencias; reglas rechazan flags de tipo inválido.
- Alcance/límite: Salidas calculadas en PC; LEDs/buzzer físicos pendientes. Los pines históricos se conservaron.

### 10. Confirmación física por botón

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:1643`; `Controller.tick()/released`, registro CONFIRMED.
- Pruebas ejecutadas: controller_test.cpp: botón sostenido/liberación/nueva pulsación y omisión; pruebas V2 impiden confirmar NO_EXIT.
- Alcance/límite: Probado con entradas simuladas. El botón real, rebote eléctrico y registro desde chip siguen pendientes; no hay confirmación remota.

### 11. Sensor de salida

**IMPLEMENTADO PARCIALMENTE.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:822`; `leerSalidaPastilla()/Controller.requireExit`, GPIO35 separado de presencia GPIO34.
- Pruebas ejecutadas: version2_test.cpp: filtro, flanco fresco, bloqueo inicial, NO_EXIT y rechazo de confirmación sin salida.
- Alcance/límite: Driver compilado; señal eléctrica/sensor real sin probar, disponibilidad=0. Salida no equivale a ingestión.

### 12. Bomba de agua opcional

**IMPLEMENTADO PARCIALMENTE.**

- Fuentes: `firmware/PastilleroESP32/PastilleroESP32.ino:800`; `Feedback.tick()/actualizarIndicadores()`, GPIO23 y pumpDurationMs 500..5000. Solo tras confirmación nueva; cancelación en fallo/alerta.
- Pruebas ejecutadas: version2_test.cpp: inicio por flanco, duración, vuelta de millis, no repetición por nivel sostenido y corte por Fault; reglas/preferencias.
- Alcance/límite: No se alimentó ni accionó bomba. Driver de potencia, caudal y montaje pendientes; disponibilidad=0.

### 13. Room y migraciones

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `app/src/main/java/mx/edu/badi/pastillero/PastilleroDatabase.java:7`; `MIGRATION_1_2/2_3/3_4`, `PastilleroDao`. Seis entidades, columnas aditivas y esquemas antiguos conservados.
- Pruebas ejecutadas: RoomOfflineTest (3) + RoomVersionTwoTest (2) en API24: migraciones, reapertura, aislamiento, token y borrado de pauta conserva eventos. Puente moderno también escribe Room.
- Alcance/límite: No se sustituyó ni eliminó la base del teléfono; pruebas sobre bases/emuladores del proyecto.

### 14. Firebase y funcionamiento offline

**IMPLEMENTADO PARCIALMENTE.**

- Fuentes: `app/src/main/java/mx/edu/badi/pastillero/DashboardRepository.java:32`; `app/src/main/java/mx/edu/badi/pastillero/ProgramWorker.java:29`; `CommandWorker`, `Repository`, `.ino/tareaFirebase()/mantenerSesionFirebase()`, NVS. Reglas V2 publicadas.
- Pruebas ejecutadas: 37 pruebas reglas locales, 2 SDK Android reales V1/V2 con goOffline/goOnline, 20+17 comprobaciones REST, Room y conflictos/transacciones locales.
- Alcance/límite: No se ejecutó el runtime ESP32 Wi-Fi/TLS/NTP/NVS ni una caída de radio. La publicación real de horarios desde la UI y ejecución autónoma en chip quedan pendientes; los sondeos reales solo usaron PING de simulación.

### 15. Prevención de dispensaciones duplicadas

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `app/src/main/java/mx/edu/badi/pastillero/ScheduleEngine.java:18`; `ProgramWorker` token/revisión; `AdaptadorMotor.record()` reserva STARTED antes de mover; NVS conserva done/recovery.
- Pruebas ejecutadas: VersionTwoTest.doseIdsStayStableAcrossRetries/compartmentChangeGetsNewImmutableDoseIdentity, reglas de inmutabilidad, C++ recuperación/reserva, seis regresiones de propiedad JSON, ocho pruebas del contrato de blobs y Room IGNORE; reintento PING real conserva ID.
- Alcance/límite: Protecciones verificadas por componente/simulación. Reinicios/NVS reales y pérdida de pasos físicos pendientes; no hay encoder.

### 16. Pruebas específicas de V2

**IMPLEMENTADO Y PROBADO.**

- Fuentes: `tests/version2_test.cpp`, `VersionTwoTest.java`, `RoomVersionTwoTest.java`, `DashboardBridgeTest.java`, `LegacyWebViewTest.java`, pruebas web, doce casos nuevos de reglas, ContractFixtureTest.java, event_json_test.cpp, snapshot_test.cpp y contract.integration.test.mjs.
- Pruebas ejecutadas: 204 casos aprobados acumulados: base histórica 74 + 130 adicionales; la unificación repite los 192 anteriores y añade doce del generador privado. 37 comprobaciones REST separadas; informes concretos en RESULTADOS.md.
- Alcance/límite: No se cuenta compilación como prueba funcional ni PING PC como ejecución de firmware sobre ESP32.

## Conservación y correcciones verificadas

Respaldo: `archives/before-version-2-20261020-214129`, 186 archivos y manifiesto verificado. `reports/version2-integrity.json` comprueba entregas previas, original, esquemas 1..3, certificados y definiciones privadas; V1 de reglas no cambia al retirar únicamente la rama V2 nueva. No se tocó CRUDSQLITE1 ni otro proyecto.

Durante QA se corrigieron una etiqueta de prueba de intervalo, el foco inicial del formulario y una comparación JSON de URL que confundía barras escapadas equivalentes. La primera apertura del AVD moderno agotó el tiempo con el permiso de notificaciones pendiente; se concedió exclusivamente en QA y la prueba final aprobó. La corrida de navegador que carecía de PLAYWRIGHT_BROWSERS_PATH no llegó a iniciar Chromium; se fijó la ubicación del navegador local y las seis pruebas finales aprobaron. El WebView de API24 carece de mensajes por origen: su comportamiento correcto es ofrecer la vista clásica, cubierto por LegacyWebViewTest, sin introducir un puente inseguro.

La revisión visual del APK detectó un botón clásico permanente que restaba espacio. Se trasladó a Ajustes y se conserva el botón XML visible solo en el caso de compatibilidad. Los tres casos de puente y las seis pruebas de Room/compatibilidad se repitieron sobre el APK final. Lint termina con cero errores y una advertencia de actualización del wrapper; no se ocultó ni se cambió la herramienta validada solo para silenciarla.

## Pendientes concretos

1. Montaje físico documentado, niveles de señal y fuentes del NEMA 17/TB6600; calibrar cinco espacios con material inerte.
2. Probar cada periférico por separado; sus disponibilidades siguen en 0 y el firmware predeterminado en simulación.
3. Introducir personalmente Wi-Fi en private/firmware.local.json y, en una fase autorizada posterior, probar ESP32 real con TLS/NTP, aplicación de programa, confirmación, omisión, reconexión y reinicio/NVS. No se cargó firmware.
4. Probar el flujo completo de programación real desde dos clientes y conflicto hasta dispositivo; las fechas/planes se validaron localmente sin crear horarios de dosis en la nube real durante QA.
5. Resolver mantenimiento de la capacidad NVS (256 IDs/documento de 48000 bytes) antes de uso prolongado y republicar las ventanas de 1..7 días; no hay renovación ilimitada ni purga automática de reservas.
6. Dashboard administrativo privilegiado y notificaciones remotas con app cerrada siguen pendientes. React móvil está implementado; no contiene autoridad administrativa.

La aclaración final del usuario se conserva: **el motor principal es el NEMA 17**, gobernado por TB6600; el servo es únicamente una preparación opcional de compuerta.

## Ampliación de evidencia tras el cierre inicial

La integración local de doce casos detectó y permitió corregir referencias compartidas a arreglos const en eventos y claves done. Se añadieron writeDoseEvent/reserveDoseId compartidos por firmware y adaptador PC y seis regresiones con ArduinoJson real. ScheduleEngine aporta una fixture JVM adicional. La evidencia nueva no se atribuye retrospectivamente a las 165 pruebas anteriores: el detalle del fallo inicial/corrección y la corrida final está en INTEGRACION_SOFTWARE.md.

Los requisitos 6, 14, 15 y 16 cuentan ahora con integración del contrato Java→Firebase Emulator→Controller→eventos y reserva/serialización compartida. La clasificación parcial del requisito 14 permanece: no se ejecutó el recorrido de publicación desde UI/WorkManager ni el runtime de red/NVS del ESP32. Tampoco se validó hardware. El .ino permanece en simulación incluso al compilar la variante física por opciones del compilador. El NEMA 17 sigue siendo el motor principal.

La persistencia ESP32 se corrigió además a blobs NVS: snapshot-v2 + marcador snapshot-ver, límite local de 48000 bytes y lectura compatible de la cadena histórica. No se usa putString para documentos grandes ni se vuelve a una copia antigua si falta el bloque marcado. Ocho pruebas nuevas verifican estas funciones compartidas con un doble RAM, incluido un programa de 96 dosis mayor de 4000 bytes; la flash física, cortes de energía y RECOVERY del adaptador Arduino no se ejecutaron. INTEGRACION_SOFTWARE.md detalla la migración conservadora y sus límites.


## Unificación del 22 de octubre de 2026

La fuente pública y la privada generada contienen toda la configuración y lógica. La carpeta activa conserva únicamente PastilleroESP32.ino y partitions.csv; las cabeceras anteriores y la caché retirada están en archives. Se compararon instrucciones de 22 funciones y clases existentes contra el respaldo, incluyendo la extracción atenderDispensacion del loop. Android mantiene sus capas: DashboardActivity agrupa onCreate en cinco funciones descriptivas. Referencia real elegida: MQTT.ino de Kali. Evidencia y límites en UNIFICACION_FIRMWARE.md y COMPARACION_CRUDSQLITE1.md.

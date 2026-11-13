# Resultados verificables — PastilleroBadi unificado

Fecha: **22 de octubre de 2026**, ISC0633. Raíz: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

## Resultado de la reorganización

El firmware tiene una única implementación pública en `firmware/PastilleroESP32/PastilleroESP32.ino`, organizada en 17 secciones. La carpeta contiene **solo ese .ino y partitions.csv**, necesario para la tabla de flash. No depende de Commands.h, Controller.h, config.h, secrets.example.h, secrets.h ni trust.h. Las seis cabeceras se conservan únicamente en los respaldos. Las pruebas C++ incluyen directamente el .ino con PASTILLERO_HOST_TEST; las cabeceras externas de bibliotecas se conservaron.

Se integraron configuración Wi-Fi/Firebase, pines, indicadores de disponibilidad y certificados TLS dentro del sketch. Las 22 funciones existentes del adaptador ESP32 y las instrucciones de las clases de control se compararon con el respaldo; el bloque atenderDispensacion se extrajo del loop, se conservó el argumento por defecto HTTPS en el prototipo y la URL completa sustituye al dominio anterior de forma equivalente. El mensaje de s ahora enumera las cuatro posiciones útiles. No se añadieron clases de firmware. La evidencia funcional/estructural es `reports/unification-integrity.json`.

**NEMA17 + TB6600 sigue siendo el motor principal**, PUL25/DIR26, AccelStepper y 3200 pasos configurables. El montaje conserva cinco espacios totales: cuatro útiles y cero vacío, recorrido **640→0,1280→0,1920→0,2560→0**, calibración a/r/c y secuencia s. Se conserva el perfil de cuatro posiciones por compatibilidad. Servo, LCD16x2, salida y bomba siguen preparados y deshabilitados localmente por defecto; LED/buzzer, botón, horarios, omisión, reservas y NVS mantienen la implementación anterior. DRY_RUN=1 es el valor predeterminado en las fuentes pública y privada. No se cargó firmware, abrió serie ni accionó hardware.

## Referencia real CRUDSQLITE1

Se inspeccionó Android en `C:\Users\milit\AndroidStudioProjects\CRUDSQLITE1` y los cuatro sketches de `/home/kali/Arduino` en la VM **Kali Linux MT** de VirtualBox. Se eligió **MQTT/MQTT.ino, 1121 líneas**, porque contiene Wi-Fi/Firebase/MQTT, sensores LDR/DHT11, LED/PWM, relay, funciones separadas y temporización. Los otros tienen 352,322 y24 líneas, con menos funciones efectivas. Las rutas Firebase de sensores/actuadores coinciden con las que escucha MainActivity de CRUDSQLITE1.

Se adoptaron sus secciones claras, variables agrupadas y funciones descriptivas, conservando las tareas asíncronas, TLS, autenticación y estados del pastillero. No se modificó ni compiló CRUDSQLITE1 ni se escribieron datos en su Firebase. Los sketches se leyeron en modo rb; cada archivo se comprobó con dos lecturas y las copias con datos privados están excluidas de Git. `docs/COMPARACION_CRUDSQLITE1.md` contiene archivos, funciones y líneas de referencia; `reports/kali-reference-comparison.json` y los hashes de fuentes Android permiten comprobarlo.

## Copia privada y configuración exacta

| Uso | Ruta absoluta |
|---|---|
| Lógica canónica y configuración pública visible | `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\firmware\PastilleroESP32\PastilleroESP32.ino` |
| Datos locales preservados | `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\firmware.local.json` |
| Copia privada generada para Arduino IDE | `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\firmware\PastilleroESP32\PastilleroESP32.ino` |

Los siete campos son WIFI_SSID, WIFI_PASSWORD, FIREBASE_DATABASE_URL, FIREBASE_API_KEY, DEVICE_EMAIL, DEVICE_PASSWORD y DEVICE_ID. El .ino público tiene marcadores para datos privados y URL pública del proyecto; la copia privada tiene los valores locales, sin incluir cabeceras propias. `python tools/generate_private_firmware.py` genera desde la única fuente. También se pueden editar solo esos literales en el .ino privado y ejecutar `--import-config`; rechaza cambios de lógica y respalda valores anteriores. Doce pruebas verifican determinismo, campos, escapes, preservación de instrucciones e importación segura. No se reproducen credenciales ni tokens en este informe. Las cuentas existentes, confianza TLS y archivos Android protegidos se conservaron.

## Android y persistencia

DashboardActivity.onCreate se divide en solicitarPermisoNotificaciones, configurarContenidoLocal, registrarPuenteSeguro, observarDatosLocales y configurarBotonAtras. Se extrajeron los mismos bloques en el mismo orden. Se mantienen React/TypeScript/Glass, XML, autenticación nativa, restricción de origen, tipos/acciones del puente, SQL asíncrono, Workers y repositorios.

Todos los demás archivos app/src coinciden con el respaldo: **Room4, entidades, DAO, migraciones aditivas, historial offline y assets permanecen idénticos**. No se sustituyó ni eliminó el historial. Se probaron migraciones/reapertura y aislamiento en los AVD del proyecto; no se accedió a una base del teléfono físico. El APK conserva applicationId mx.edu.badi.pastillero y versión2.0-simulacion.

## Compilaciones

Android assembleDebug y assembleDebugAndroidTest: **APROBADOS**. Lint: **0 errores,1 advertencia** AndroidGradlePluginVersion; se conserva la herramienta validada, sin ocultar el aviso. TypeScript/Vite, pruebas de navegador y verificación de assets incluidos en el APK: aprobados.

Se compilan ambos modos en fuente pública y copia privada; cada flag se pasa al compilador, sin editar el valor de simulación del .ino. Plataforma: ESP32 DOIT devkit-v1, core3.3.12, AccelStepper1.64 y ArduinoJson7.3.2. La comprobación final compara instrucciones del sketch con la salida de Arduino, admitiendo comentarios/prototipos automáticos; comprueba particiones, placa, flag0/1 y hashes de cada artefacto.

| Fuente/modo | Compilación |
|---|---|
| public-simulation | 1123420 bytes; RAM global 59824 |
| public-hardware | 1130052 bytes; RAM global 59912 |
| private-hardware | 1130020 bytes; RAM global 59912 |
| private-simulation | 1123388 bytes; RAM global 59824 |

Evidencia: `reports/unified-firmware-validation.log`, los cuatro `unified-*-build.log`, `firmware-sizes.json` y `compiled-source-validation.log`. Ninguna compilación equivale a una ejecución en chip.

## Pruebas ejecutadas

**204 casos aprobados**: se repitieron los192 existentes y se añadieron12 del generador/importador privado. Frente a74 de referencia, hay130 adicionales. Las compilaciones y las comprobaciones REST se contabilizan aparte.

| Grupo | Casos | Evidencia |
|---|---:|---|
| Controlador/comandos históricos C++ |24| controller-v2-tests.log |
| Geometría/periféricos V2 en PC |20| firmware-v2-new-tests.log |
| Propiedad de identificadores JSON |6| event-json-tests.log |
| Contrato de instantáneas con doble RAM |8| snapshot-tests.log |
| JVM, incluyendo fixture ScheduleEngine |32| app/build/test-results/testDebugUnitTest/TEST-*.xml |
| Java→Firebase Emulator→Controller→eventos |12| unified-integration-validation.log e integration-v2-contract.log |
| Room, migraciones y datos offline |5| unified-PastilleroBadiQA-tests.log |
| Alternativa segura WebView antiguo |1| mismo log API24 |
| React→Java→Room en APK real |3| unified-PastilleroBadiV2QA-tests.log |
| SDK Android con Firebase real V1/V2 |2| android-firebase-live.log; solo PING simulation y goOffline/goOnline |
| Reglas Firebase en emulador |37| unified-firebase-rules.log |
| Módulo administrativo, dobles locales |12| unified-admin-tests.log |
| React, API y fechas |24| web-v2-unit-tests.log |
| Navegador escritorio/móvil |6| web-v2-e2e.log y .json |
| Generación e importación privada |12| unified-generator-tests.log |

Además, **37 comprobaciones REST reales aprobadas**:20 V1 y17 V2, en reports/firebase-setup/live-probe*.json. Solo cuentas ordinarias y comandos qa-* PING simulation; no se publicaron horarios ni eventos de dispensación reales. El validador C++ se ejecutó en PC, no en un ESP32. La semilla de fechas pasadas del contrato se usa solo en el emulador para representar una caché anterior; no se cuenta como publicación nueva admitida. Los reinicios del modelo/dobles RAM no equivalen a probar RECOVERY/flash/NVS en chip.

Firebase sigue en el proyecto **PastilleroBadi**, ID **pastillerobadi**, URL **https://pastillerobadi-default-rtdb.firebaseio.com**, región us-central1 y plan Spark. No se creó facturación ni se publicaron reglas nuevas en esta reorganización. Las reglas V2 existentes siguen verificadas con acceso público denegado, roles separados, vínculos y revocación. El backend administrativo no se desplegó ni se activó una cuenta privilegiada.

## Respaldo, documentación y entregables

Respaldo previo: `archives/before-unified-20261022-e595f701`, **297 archivos**, manifiesto verificado. Los archivos retirados están allí; la caché anterior se conservó aparte en archives/retired-build-doit-20261022. Se mantuvieron original/, esquemas, entregas anteriores y configuración privada. No se sobrescribió releases/2.0. El cierre anterior está íntegro en RESULTADOS_2.0_ANTES_UNIFICACION.md y en el respaldo. Las copias privadas modificadas y la configuración anterior a importación tienen respaldo local automático.

Las guías por línea se regeneraron desde el código final: **110 archivos y 13 921 líneas no vacías**, cero fragmentos sin explicación en el inventario; huellas y referencias finales comprobadas. Se actualizaron también las guías Firebase, Room, conexiones y defensa oral, configuración, arquitectura, auditoría y contrato. `UNIFICACION_FIRMWARE.md` muestra estructura anterior/posterior, configuración real sin secretos y navegación por las17 secciones. Los hashes de artefactos están en reports/artifact-hashes.json; el listado de cambios de esta revisión está en reports/unification-changes.json.

Entrega nueva: `releases/unificado-20261022/`, con APK debug y cuatro binarios. Las cuatro compilaciones terminaron y el comprobador verificó las instrucciones compiladas, ausencia de cabeceras propias, particiones, placa y flags. APK: **8 644 168 bytes**, SHA-256 `1E7C278BA44639C23C51CADE4A585B61B75A08F5DBCBC35A71684C8714B69E45`. Los binarios privados pueden contener credenciales del dispositivo y están excluidos de Git; no distribuirlos. El .ino público no contiene cuentas ni contraseñas reales.

## Pendientes antes de las pruebas físicas

1. Introducir personalmente Wi-Fi y revisar montaje, alimentación, niveles y microstepping del NEMA17/TB6600, mecanismo vacío y cero de retorno.
2. Con autorización posterior, cargar primero simulación al chip y probar Wi-Fi, TLS/NTP, autenticación, reconexión, memoria disponible y persistencia NVS real. Nada de eso se ejecutó aquí en ESP32.
3. Revisar señales sin motor y después calibrar/entregar/volver a cero con material inerte. No usar medicamentos reales. Probar los cuatro compartimentos, botón, omisión y reinicio interrumpido.
4. Validar LCD/sensor/servo/bomba y sus etapas eléctricas antes de habilitar macros, manteniendo la confirmación física y límites de memoria/colas.
5. Completar el recorrido de publicación desde UI/WorkManager hasta ESP32 real y los conflictos entre clientes. Se probaron componentes, transporte de diagnóstico y contrato local, no ese circuito físico completo.
6. El dashboard administrativo privilegiado y notificaciones garantizadas con app cerrada siguen pendientes; no se añadieron credenciales administrativas al frontend o firmware.

## Preparación para GitHub — 13 de noviembre de 2026

Se prepararon fuentes de Android, ESP32, React móvil, reglas y backend para MarlonTanque/Pastillero. COLABORACION_GITHUB.md explica el clon, configuración local y trabajo pendiente del sitio web. El frontend móvil del navegador conserva su demostración local; no se presenta como una conexión Firebase real.

Se detectaron datos de acceso introducidos manualmente en el .ino público después del cierre anterior. Se respaldaron y conservaron en private/firmware.local.json y su sketch generado, sin publicar valores. La fuente pública vuelve a tener marcadores y su huella coincide exactamente con la validada el 22 de octubre. No se sustituyó su lógica ni se modificó Android, Room, reglas o hardware. El respaldo de esta preparación está en archives/pre-github-20261113.

Se ejecutaron de nuevo **117 casos**: 32 JVM Android, 24 React, 37 reglas en emulador, 12 backend con dobles y 12 generador/importador. Todos aprobaron. Lint Android: **0 errores y 1 advertencia AndroidGradlePluginVersion**. Las guías finales de esta publicación cubren **111 archivos y 13 950 líneas no vacías**, sin fragmentos pendientes en el inventario. El resumen público está en reports/public-validation-summary.json.

Los **204 casos**, 37 sondeos REST reales, APK y cuatro compilaciones descritos arriba corresponden al cierre histórico de octubre. En esta preparación no se repitieron la matriz ESP32, pruebas físicas, integración de red del nuevo sketch privado ni sondeos contra producción. Los APK, binarios, bibliotecas, configuración local, respaldos, capturas y registros completos se excluyen del repositorio. No se publicaron reglas ni se desplegó el backend administrativo.

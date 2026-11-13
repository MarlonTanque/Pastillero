# Resultados de reorganización y estudio — 20 de octubre de 2026

Proyecto: **Pastillero Badi**, materia Programación de Bases de Datos para Aplicaciones Móviles (ISC0633).

Carpeta única: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`. Abrir esta raíz en Android Studio; Arduino abre `firmware/PastilleroESP32/PastilleroESP32.ino`.

**Entrega 1.4-estudio, código 5: APK y ambas variantes ESP32 compilados. Los 74 casos de referencia volvieron a aprobar, sin fallos ni casos omitidos en los grupos ejecutados; además pasaron las 20 comprobaciones REST reales. Modo simulación restaurado y verificado. No se cargó firmware, no se abrió monitor serie ni se accionó el motor.**

## Copia recuperable y entregas conservadas

Copia previa verificada: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\archives\before-study-20261020-151032`, con 143 archivos y manifiesto SHA-256. Conserva fuentes, configuración privada local, documentos y entregables; las bibliotecas/cachés generadas no se duplicaron. La carpeta archives está excluida de Git.

Las entregas 1.0, 1.1-preview, 1.2 y 1.3 permanecen en releases. El informe previo está en [RESULTADOS_1.3_CONSERVADOS.md](RESULTADOS_1.3_CONSERVADOS.md), con identificadores de cuentas omitidos de la copia pública. El original íntegro permanece en el respaldo local. Los sketches de original/ no se modificaron. CRUDSQLITE1 solo se leyó como referencia.

## Cambios realizados

- El modelo Dose/State/Controller y el validador de comandos se reunieron en el `.ino`, con una sola implementación. `Controller.h` y `Commands.h` quedaron como puentes mínimos para que las pruebas C++ existentes incluyan ese modelo sin compilar GPIO ni red.
- Se separaron funciones con nombres descriptivos para configuración, restauración NVS, calibración serie, indicadores, telemetría, autenticación y sincronización. Se conservaron orden de estados, campos JSON, calibración a/r/c/s, cuatro posiciones, 3200 pasos configurables, secuencia 1→0,2→0,3→0 y temporización no bloqueante.
- `config.h` mantiene el interruptor de compilación y los pines; `secrets.h` mantiene valores privados; `trust.h` mantiene los certificados públicos; `partitions.csv` conserva el formato requerido por la herramienta. Sus definiciones privadas y el contenido PEM se comprobaron sin reproducir valores.
- Java se espació por instrucciones y recibió comentarios en español; XML se separó por atributos y se añadieron comentarios por control. Se conservó la organización de Activity, Repository, Workers, entidades y DAO. Las instrucciones Java normalizadas y la semántica XML coinciden con el respaldo.
- Room sigue en versión 3 con los mismos esquemas y migraciones 1→2→3. No se borró historial ni se añadió migración destructiva. Gradle muestra PastilleroBadi como nombre del proyecto y conserva applicationId `mx.edu.badi.pastillero`.
- Se adaptaron los verificadores a los nombres del firmware y a releases/1.4; se añadieron generación/cobertura de guías e integridad de la reorganización. Se ignoraron las cachés Python. Los valores privados siguen excluidos de Git.

## Documentación creada

| Guía | Contenido |
|---|---|
| [GUIA_ARDUINO_LINEA_POR_LINEA.md](GUIA_ARDUINO_LINEA_POR_LINEA.md) | Firmware activo, configuración redactada, certificados como datos, puentes de pruebas, particiones, pruebas C++ y sketch original de referencia |
| [GUIA_ANDROID_LINEA_POR_LINEA.md](GUIA_ANDROID_LINEA_POR_LINEA.md) | Java de producción/pruebas, XML, Gradle/configuración y anexos de Firebase, backend y herramientas propias |
| [GUIA_FIREBASE.md](GUIA_FIREBASE.md) | Identidades, JSON, rutas, reglas, acuses, sincronización, permisos y errores |
| [GUIA_ROOM_SQLITE.md](GUIA_ROOM_SQLITE.md) | Tres tablas, claves, todas las consultas DAO, migraciones y funcionamiento offline |
| [GUIA_CONEXIONES_HARDWARE.md](GUIA_CONEXIONES_HARDWARE.md) | Pines, niveles, TB6600/NEMA 17, calibración y protocolo físico pendiente |
| [GUIA_DEFENSA_ORAL.md](GUIA_DEFENSA_ORAL.md) | Recorrido de exposición, preguntas/respuestas, ejemplos y matriz de requisitos |

Las dos guías de código cubren **67 archivos propios y 9966 líneas no vacías**, incluidos comentarios, cierres y datos de certificados identificados sin copiar su contenido. Las líneas vacías no son instrucciones. El verificador comprueba inventario completo, números de línea y huellas de fuente; los valores privados solo se verifican por su forma redactada. No quedaron fragmentos sin vocabulario explicativo en el informe de revisión. Los esquemas/implementaciones generadas, bibliotecas y Gradle Wrapper no se atribuyen como código escrito para el proyecto.

No se recibió una rúbrica docente adicional con ponderaciones. La matriz de la defensa cubre los requisitos enviados; no se inventa una calificación ni se afirma cumplir criterios desconocidos.

## Comparación de pruebas con la entrega anterior

| Grupo | Referencia 1.3 | Repetidas 1.4 | Evidencia actual |
|---|---:|---:|---|
| Controlador/comandos C++ en PC | 24 | 24 aprobadas | reports/controller-study-tests.log |
| Reglas y puente C++ con Firebase Emulator | 25 | 25 aprobadas | reports/firebase-study-tests.log |
| Servicio administrativo con dobles SDK | 12 | 12 aprobadas | reports/admin-study-tests.log |
| PlanCodec JVM | 9 | 9 aprobadas | app/build/test-results/testDebugUnitTest/ |
| Room API 24 | 3 | 3 aprobadas | reports/room-study-tests.log |
| Android SDK ↔ Firebase real | 1 | 1 aprobada | reports/android-firebase-live.log y reports/firebase-setup/android-live.json |
| **Total de casos** | **74** | **74 aprobados** | reports/validation-1.4.json |
| Comprobaciones REST reales, adicionales | 20 | 20 aprobadas | reports/firebase-setup/live-probe.json |

La prueba real se ejecutó optativamente con credenciales privadas en tiempo de ejecución. La prueba Room se seleccionó por clase y la prueba SDK por separado: no se contó un caso ignorado por falta de credenciales como aprobado. Solo se utilizó el AVD PastilleroBadiQA, serial emulator-5580, en modo sin ventana; se cerró al terminar. No se instaló en un teléfono físico.

La integración real verificó autenticación, permisos, PING/resultados en simulación, renovación y goOffline/goOnline del SDK. No creó horarios ni eventos de dosis. La respuesta del rol dispositivo en esa prueba provino del SDK del emulador, no de un firmware ESP32 ejecutándose en el chip. Tampoco simula una caída física de radio Wi-Fi. La revisión visual de MainActivity no se ejecutó en este trabajo.

## Compilaciones y herramientas

Android: assembleDebug, testDebugUnitTest, lintDebug y assembleDebugAndroidTest aprobados; compilación final en reports/android-study-final-build.log. Lint: **0 errores y 1 advertencia**. La advertencia AndroidGradlePluginVersion informa que Gradle 9.8.2 está disponible; se mantuvo 9.6.1 y AGP 9.3.3 para conservar las versiones probadas, sin suprimir lint. Java fuente/destino 11, compile/target SDK 36, mínimo API 24.

ESP32: placa `esp32:esp32:esp32doit-devkit-v1`, core **3.3.12** instalado en el entorno. El registro 1.3 usaba 3.3.11: la comparación de tamaños no aísla solamente el cambio de comentarios/reorganización. Se conservaron AccelStepper 1.64 y ArduinoJson 7.3.2. La compilación no ejecuta upload. El controlador C++ también se compiló en PC con Zig 0.14.1.

| Variante ESP32 | Programa según compilador | Variables globales |
|---|---:|---:|
| hardware | 1102180 B | 50512 B |
| simulation | 1095888 B | 50424 B |

Ambas variantes enlazaron sin errores; los detalles están en reports/firmware-hardware-build.log, reports/firmware-simulation-build.log y reports/firmware-validation.log. Se restauró `PASTILLERO_DRY_RUN=1`. Las imágenes son de aplicación, no paquetes completos de flash. Se conserva la tabla de particiones de 4 MiB con NVS de 256 KiB y aplicación desde 0x50000. Las asignaciones dinámicas TLS/JSON y los márgenes en ejecución requieren medición en el ESP32 real.

## Entregables nuevos

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| releases/1.4/PastilleroBadi-1.4-debug.apk | 7109688 | `1B0EE72A868E7DA8A4F1F8CEC65D422956A39B64988E862EF4354F631D801041` |
| releases/1.4/PastilleroESP32-hardware.bin | 1102336 | `FCEFA935BE5C422F29DBF65E336C56207EC39237D3FBAA6290955141F66F2169` |
| releases/1.4/PastilleroESP32-simulacion.bin | 1096032 | `CDB65A38D48C6A658AA53C1E731AE0FDE768E61AB5C491E125335551149CFCF3` |

Los binarios ESP32 contienen la configuración local de la cuenta del dispositivo y están excluidos de Git; no deben compartirse. El APK no contiene las contraseñas del responsable ni del dispositivo. No se publicó nada en GitHub.

## Firebase, Room y arquitectura conservados

Firebase: PastilleroBadi (`pastillerobadi`), Realtime Database `https://pastillerobadi-default-rtdb.firebaseio.com`, región us-central1, plan Spark sin facturación habilitada. Correo/contraseña para las dos identidades ordinarias ya vinculadas al dispositivo. Las reglas no se modificaron ni se publicaron reglas nuevas en este trabajo; su archivo coincide con la copia que quedó desplegada.

Android sigue usando XML, Room, ejecutor de disco y WorkManager. La caché del SDK no reemplaza el historial Room. El permiso remoto no permite borrar lo ya descargado; revocar acceso conserva las filas locales. ESP32 mantiene colas FreeRTOS, NVS antes del movimiento, acuses idempotentes, certificados TLS, control local no bloqueante y separación simulation/hardware.

Comprobaciones de conservación aprobadas en reports/study-refactor-integrity.json: mismas instrucciones normalizadas del controlador/validador y Java, mismos esquemas Room, misma semántica XML, sketch original intacto, reglas intactas, certificados intactos, definiciones privadas intactas y copia previa recuperable. Las verificaciones adicionales no se sumaron al denominador de 74 casos.

## Configuración y límites pendientes

| Archivo local | Situación |
|---|---|
| app/google-services.json | Guardado; configuración pública del proyecto dedicado, sin reproducir valores en las guías |
| firebase-config.properties | URL, dispositivo y modo de comandos; local e ignorado |
| firmware/PastilleroESP32/secrets.h | Cuenta del dispositivo conservada; WIFI_SSID y WIFI_PASSWORD siguen pendientes de entrada personal |
| private/integration.local.properties | Credenciales de prueba, leídas sin imprimir; no se compilan en APK |
| private/dashboard-admin.local.json | Administrador principal y ADC/despliegue pendientes de la fase web |

React no se desarrolló. El backend administrativo conserva sus 12 pruebas locales, pero no se activó un administrador privilegiado ni se ejecutó la integración Firebase Admin real. La conexión del firmware ESP32 por Wi-Fi/TLS en el chip, los niveles del TB6600, el sensor, botón, corriente, microstepping y retorno mecánico siguen pendientes. El buzón de un identificador de Authentication no se considera verificado por haber iniciado sesión.

Antes de pruebas físicas: completar Wi-Fi personalmente en su archivo privado; verificar modelo de placa/driver, interfaz de nivel, bobinas, fuente y corriente; retirar horarios simulados antes de cambiar de modo; ejecutar el protocolo de GUIA_CONEXIONES_HARDWARE.md solo después de autorizar esa fase, con mecanismo vacío/material de prueba y sin medicamentos reales. No hay homing automático/encoder ni notificaciones FCM garantizadas con Android cerrado en esta entrega.

## Repetir verificaciones documentales

`python tools/generate_study_guides.py --verify` comprueba las referencias finales. Después de editar código, ejecutar el generador sin --verify y volver a verificar. `--annotate` es una operación de mantenimiento que cambia comentarios/números de línea y obliga a recompilar/verificar; no se ejecuta para leer las guías. `python tools/verify_study_refactor.py` contrasta con la copia previa. Los cambios recuperables se enumeran en reports/study-changed-files.json; el inventario de fuentes estudiadas está en reports/study-source-coverage.json.

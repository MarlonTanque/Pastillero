# Resultados verificables — PastilleroBadi 2.0

Cierre: **21 de octubre de 2026**, materia Programación de Bases de Datos para Aplicaciones Móviles (ISC0633). Raíz única: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

## Resultado y alcance

Se auditó el código 1.5 y se implementó la ampliación 2.0: React/TypeScript dentro del APK nativo, interfaz Liquid Glass con temas y cinco vistas, calendario real, medicamentos con horas o intervalos independientes, Room 4, cola V2, reconciliación de conflictos y firmware con cinco espacios y periféricos opcionales. **El motor principal sigue siendo NEMA 17 + TB6600**, PUL25/DIR26, con AccelStepper. El servo es una preparación opcional para compuerta.

No se cargó firmware, abrió monitor serie, movió el motor ni accionó hardware. DRY_RUN=1 queda restaurado y LCD/salida/servo/bomba tienen disponibilidad local 0. Las compilaciones físicas solo producen archivos. El APK se instaló exclusivamente en emuladores del proyecto; no se instaló ni modificó el teléfono conectado.

La auditoría completa, antes/después, clasifica cada uno de los dieciséis requisitos en `AUDITORIA_VERSION_2.md`, con archivos, funciones, líneas finales, pruebas y pendientes. No se declaran como probadas conexiones eléctricas ni ejecución ESP32 por haber compilado.

## Respaldo y conservación

Antes de cambiar: `archives/before-version-2-20261020-214129`, **186 archivos**, manifiesto SHA-256 verificado. El informe es `reports/version2-backup.json`. Se conservaron el sketch recibido y corregido de `original/`, sus comandos a/r/c/s, certificados, definiciones privadas, esquemas Room 1..3 y todas las entregas anteriores. El patrón de ida/regreso se amplió al montaje confirmado de cinco espacios: **640→0, 1280→0, 1920→0, 2560→0** con 3200 pasos/vuelta. El espacio cero queda vacío y vuelve a él tras cada entrega.

El informe anterior está íntegro en `docs/RESULTADOS_1.5_CONSERVADOS.md` y en el respaldo. Los binarios V2 previos a la recompilación también se guardaron en `archives/firmware-prior-*`. `reports/version2-integrity.json` verifica recuperación/conservación, aislamiento de reglas V1, simulación y ausencia de credenciales de cuentas en fuentes, guías y APK. CRUDSQLITE1 y otros proyectos no se modificaron.

## Firebase y contrato

- Nombre: **PastilleroBadi**; ID: **pastillerobadi**.
- Realtime Database: **https://pastillerobadi-default-rtdb.firebaseio.com**, región us-central1; plan Spark, sin habilitar facturación.
- Paquete Android: **mx.edu.badi.pastillero**, código de versión 7, nombre **2.0-simulacion**.
- Authentication: correo/contraseña con dos cuentas ordinarias distintas, responsable y dispositivo; no se incluyen sus identificadores/contraseñas aquí.
- Reglas V2 **publicadas con confirmación explícita**, manteniendo V1 semánticamente igual. Captura: `reports/firebase-v2-rules-published.png`; huella en `reports/version2-validation.json`.

La base V2 es `devices/pastillero-01/v2`, con program (settings/regimens/doses), state, commandRequests, commandResults/MODO/ID y events. `CONTRATO_FIREBASE.md` versión documental 4 contiene JSON, tipos, rutas y permisos; program.version=2 es otra versión distinta. El responsable vinculado habilitado escribe programa/solicitudes; el dispositivo vinculado habilitado escribe estado/eventos/resultados. Ambos deben tener sesión posterior a revokedAt. Raíz pública .read/.write=false; los clientes no se conceden privilegios administrativos.

React está empaquetado y no abre Firebase directamente. WebViewAssetLoader usa HTTPS local; BridgeProtocol comprueba origen único, marco principal, ID, acción, tamaño y tipos. No existe addJavascriptInterface ni orden remota de dispensación/confirmación. Login se realiza en campos nativos. Un WebView antiguo ofrece la vista clásica segura. El dashboard administrativo privilegiado sigue siendo un módulo/fase separado.

## Room, sincronización y datos offline

Room **4** conserva historial/borradores/solicitudes y añade Medication, DevicePreferences y ProgramOutbox. MIGRATION_3_4 añade columnas con DEFAULT y tres tablas; no contiene eliminación/destrucción de datos. Continúan las migraciones 1→2→3. Eliminar una pauta no elimina sus eventos; IGNORE y claves compuestas evitan duplicados. No se probó ni modificó una base del teléfono físico: las pruebas usaron bases de QA.

DashboardRepository trabaja en ejecutor; los listeners no hacen esperas de red/SQL en el hilo principal. ProgramWorker publica por transacción revisión/token y WorkManager reintenta con conectividad. El acuse compara token para no limpiar una edición posterior. Una revisión incompatible exige decidir entre recargar definiciones remotas o conservar locales y revisar/publicar otra vez. Los permisos revocados retiran listeners/trabajos sin destruir Room.

En ESP32 la red/autenticación/TLS están en tarea separada y el controlador avanza con millis. STARTED se persiste antes de solicitar movimiento. La recuperación mantiene reservas y genera RECOVERY sin repetir; una migración de snapshot V1 guarda legacy-v1 antes de retirar el plan incompatible. El reinicio requiere calibración y reloj válido. Sensor de salida y presencia son distintos; NO_EXIT no equivale a ingestión.

## Compilaciones finales

| Entregable/verificación | Resultado |
|---|---|
| TypeScript estricto y Vite | APROBADO; assets locales incluidos en APK |
| Android assembleDebug/assembleDebugAndroidTest | APROBADO; JBR de Android Studio, Gradle 9.6.1, AGP 9.3.3, compile/target 36, min 24 |
| Android lint | **0 errores, 1 advertencia** AndroidGradlePluginVersion sobre actualización del wrapper; se conserva la herramienta validada, sin ocultar el aviso |
| Firmware físico, solo compilación | APROBADO: 1128196 bytes de programa, 59880 bytes globales RAM |
| Firmware simulación | APROBADO: 1121644 bytes de programa, 59792 bytes globales RAM |
| Plataforma firmware | ESP32 DOIT devkit-v1, core 3.3.12, AccelStepper 1.64, ArduinoJson 7.3.2 |
| JSON | Reglas, esquemas, configuración pública y reportes analizados sin errores |
| Integridad compilada | Cabeceras, particiones, placa, instrucciones del sketch, simulación y huellas de tres artefactos coinciden |

La advertencia de lint es la única restante de la revisión histórica que partió de 31 avisos; no se introdujeron errores ni advertencias de WebView. Se corrigió el control explícito de capacidad requerido por WebViewCompat. Los avisos de actualización/deprecación de herramientas en logs no se cuentan como fallos de pruebas.

## Pruebas ejecutadas y comparación con 1.5

**165 casos aprobados**, frente a **74** de referencia: **91 casos adicionales**. Las comprobaciones REST se contabilizan aparte para no mezclar modalidades ni inflar la comparación.

| Grupo | Aprobados | Evidencia y entorno |
|---|---:|---|
| Controlador/comandos C++ históricos | 24 | reports/controller-v2-tests.log; mismo modelo del .ino en PC, sin GPIO |
| Firmware V2: geometría/salida/LCD/servo/bomba/LED/cola | 20 | reports/firmware-v2-new-tests.log; modelos PC, sin periféricos físicos |
| Java JVM: 9 anteriores + 22 V2 | 31 | app/build/test-results/testDebugUnitTest/TEST-*.xml |
| Room: 3 anteriores + 2 V2 | 5 | reports/android-v2-room-legacy.log; migraciones/reapertura/aislamiento en AVD API24 |
| Alternativa WebView antiguo | 1 | mismo informe; LegacyWebViewTest sobre API24 |
| Puente React→Java→Room en APK | 3 | reports/android-v2-bridge.log; AVD PastilleroBadiV2QA, imagen android-37.1 Google Play 16k x86_64 |
| Firebase reglas: 25 anteriores + 12 V2 | 37 | reports/firebase-v2-tests.log; Realtime Database Emulator |
| Backend administrativo | 12 | reports/admin-v2-tests.log; dobles locales de Auth/DB, sin activar administrador real |
| React: componentes/API/fechas | 24 | reports/web-v2-unit-tests.log; Vitest/DOM simulado |
| Navegador: escritorio + Pixel 7 | 6 | reports/web-v2-e2e.log y .json; Chromium local, seis recorridos con teclado/tema/CRUD/calendario/reduced motion |
| SDK Android con Firebase real V1/V2 | 2 | reports/android-firebase-live.log y reports/firebase-setup/android-live.json; cuentas ordinarias, PING simulation, goOffline/goOnline |

**37 comprobaciones REST adicionales**: 20 V1 en `reports/firebase-setup/live-probe.json` y 17 V2 en `live-probe-v2.json`, todas aprobadas. Incluyen acceso anónimo denegado, roles separados, reintento idéntico, comando inválido denegado y resultados inmutables; el validador puro C++ decide PING en PC. No equivalen a ejecutar el runtime de red del firmware.

Los sondeos reales no escribieron horarios ni eventos de dispensación: solo solicitudes/resultados **qa-* PING simulation**. Las fechas/planes y conflictos se comprobaron en motores de fechas, reglas/transacciones locales y Room. No se afirma una ejecución completa de dosis Android→Firebase→ESP32 real.

## Incidencias de QA resueltas

Se corrigieron etiquetas de pruebas, foco inicial de diálogo y comparación de URL JSON con barras escapadas equivalentes. El AVD moderno inicialmente agotó el tiempo con el permiso de notificaciones pendiente; se concedió solo en QA y los tres casos finales aprobaron. La ejecución de navegador sin la variable de ruta no inició Chromium; al señalar `toolchain/browsers` aprobaron los seis casos. `tools/validate-web.ps1` fija esa ruta de forma reproducible.

La revisión visual detectó un botón clásico permanente que restaba espacio: ahora está en Ajustes y el botón XML solo aparece en el caso de compatibilidad. Se repitieron puente, Room y alternativa antigua sobre el APK final. Capturas revisadas: reports/v2-desktop-home.png, v2-mobile-home.png, v2-mobile-calendar-dark.png y v2-android.png. Ninguna captura de demostración se presenta como telemetría física.

## Documentación y archivos modificados

El inventario verificable comprende **106 archivos y 12847 líneas no vacías**, con cero fragmentos sin vocabulario, huellas y referencias finales comprobadas. La cobertura es por instrucción/línea, no una aprobación funcional automática.

Se actualizaron las seis guías GUIA_ARDUINO_LINEA_POR_LINEA, GUIA_ANDROID_LINEA_POR_LINEA, GUIA_FIREBASE, GUIA_ROOM_SQLITE, GUIA_CONEXIONES_HARDWARE y GUIA_DEFENSA_ORAL. Se añadieron VERSION_2_IMPLEMENTACION y AUDITORIA_VERSION_2; se actualizó CONTRATO_FIREBASE y README. Las guías no reproducen secretos.

Fuentes principales: firmware/PastilleroESP32/PastilleroESP32.ino y config.h; web/src y configuración/pruebas de web; app/src con DashboardActivity, BridgeProtocol, DashboardRepository, ScheduleEngine, ProgramWorker, entidades V2, DAO/migración y compatibilidad CommandWorker; app/build.gradle/manifest/layout/strings; firebase/database.rules.json y rules.test.mjs; pruebas C++/JVM/instrumentadas y herramientas de validación/guías. El listado completo con estado y SHA-256 está en `reports/version2-changes.json`.

El verificador histórico verify_study_refactor.py sirve para la reorganización 1.5. V2 cambia funciones y esquema deliberadamente; se verifica con `tools/verify_version2.py`, no se declara igualdad de instrucciones con 1.5.

## Configuración y ubicaciones exactas

Todas las rutas siguientes están bajo `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`:

| Archivo | Variables/campos |
|---|---|
| app/google-services.json | Cliente registrado mx.edu.badi.pastillero; configuración pública de Firebase |
| firebase-config.properties | apiKey/appId/projectId/databaseUrl/deviceId/commandMode, según configuración local |
| firmware/PastilleroESP32/secrets.h | WIFI_SSID, WIFI_PASSWORD, FIREBASE_API_KEY, FIREBASE_HOST, DEVICE_EMAIL, DEVICE_PASSWORD, DEVICE_ID |
| firmware/PastilleroESP32/config.h | PASTILLERO_DRY_RUN=1; cuatro PASTILLERO_*_AVAILABLE=0; DEFAULT_POSITIONS=5; pines |
| private/integration.local.properties | owner.email/owner.password/device.email/device.password, solo para pruebas optativas |
| firmware/PastilleroESP32/trust.h | Certificados raíz públicos, sin cuentas de servicio |

Los archivos privados y binarios ESP32 están ignorados por Git. No hay claves Admin ni cuenta de servicio en APK/firmware. Las credenciales Wi-Fi permanecen pendientes de entrada personal antes de pruebas físicas; no se solicitan por chat. Los binarios ESP32 locales pueden incorporar la cuenta ordinaria del dispositivo: no compartirlos públicamente.

## Entregables nuevos, sin sobrescribir versiones anteriores

- `releases/2.0/PastilleroBadi-2.0-simulacion.apk`: 8644168 bytes; SHA-256 `CB01A19DC9398A079BA41D672F9C90B2B8D385D1CDDBE46D1757BFC983428BE5`.
- `releases/2.0/PastilleroESP32-hardware.bin`: 1128352 bytes; SHA-256 `555B6A8C67A57C387F295F2E7C7B2E15B12C2C9CABE45B79BAD1A5F0BEF35119`.
- `releases/2.0/PastilleroESP32-simulacion.bin`: 1121792 bytes; SHA-256 `D7E22B6AA82812E7A8AE50A5902461B66F7922C46CF20464B6A51B3EF6235A57`.

El APK es una compilación debug de simulación para QA/estudio, no una publicación en tienda. El binario físico no se cargó. `reports/artifact-hashes.json`, `firmware-sizes.json`, `version2-validation.json`, `version2-integrity.json` y `compiled-source-validation.log` conservan el resumen comprobable.

## Pendientes antes de pruebas físicas

1. Documentar el módulo TB6600 real, NEMA 17, fuente, corriente, microstepping y adaptación de niveles. Revisar pines y seguridad eléctrica desenergizado. No hay encoder/homing automático.
2. Introducir personalmente SSID/contraseña Wi-Fi en secrets.h; no mandar credenciales al chat. En una fase posterior explícitamente autorizada se podrá cargar primero simulación al chip y probar TLS/NTP/auth/recuperación de red/NVS; nada de eso se ejecutó aquí sobre ESP32.
3. Probar señales sin motor y calibrar cinco espacios con mecanismo vacío/material inerte; luego una entrega/retorno, las cuatro en secuencia y botón/omisión/recuperación. No usar medicamentos reales.
4. LCD, salida, servo y bomba: validar cada montaje/tensión/polaridad/dirección/topes/caudal por separado antes de habilitar su macro. Mantienen disponibilidad 0. La bomba necesita driver de potencia, no GPIO directo.
5. Probar publicación real de horarios desde UI, conflictos entre dos clientes y flujo completo hasta ESP32; actualmente están probados los componentes, reglas y transporte de diagnóstico, no ese flujo físico completo.
6. Gestionar límites: ventana publicada 1..7 días/96 dosis, sin renovación perpetua; NVS 48000 bytes/256 IDs y cola finita, con bloqueo seguro al llenarse. No borrar reservas para continuar silenciosamente.
7. Dashboard administrativo privilegiado y garantía de notificaciones con app cerrada/FCM siguen pendientes. La interfaz móvil React no es el panel administrativo ni contiene sus credenciales.

Para repetir comprobaciones locales consultar VERSION_2_IMPLEMENTACION.md y las herramientas. Los emuladores del proyecto usados para QA se cerraron al terminar; no se apagó ni alteró el teléfono físico.

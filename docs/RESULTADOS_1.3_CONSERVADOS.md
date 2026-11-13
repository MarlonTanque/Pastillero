# Resultados de validación — 20 de octubre de 2026

## Ubicación y estado

Proyecto consolidado en **`C:\Users\milit\AndroidStudioProjects\PastilleroBadi`**, con Gradle en la raíz y el módulo Android en `app/`. Esta es la carpeta que se abre en Android Studio. Los archivos locales, firmware, reglas, pruebas, documentación y entregables se encuentran dentro de ella. La aplicación y la documentación utilizan únicamente el nombre Badi.

Se preservaron los entregables anteriores en `releases/1.0` y `releases/1.1-preview`. El sketch original está en `original/`. No se modificaron los proyectos anteriores de Android/Arduino ni el proyecto Firebase de referencia. No se cargó firmware, no se abrió un monitor serie y no se accionó el motor.

**Ambas cuentas están creadas y vinculadas; las reglas con acceso revocable están publicadas. Las 20 comprobaciones REST contra Firebase real pasaron. Android y ambas variantes ESP32 compilan. La prueba instrumentada del SDK Android contra Firebase real también pasó; la ejecución del firmware sobre ESP32 y la revisión visual de la interfaz siguen pendientes.**

## Firebase creado

| Dato | Resultado |
|---|---|
| Nombre | PastilleroBadi |
| Identificador | `pastillerobadi` |
| Número | `461409252301` |
| Plan | Spark, sin facturación habilitada |
| Base | `https://pastillerobadi-default-rtdb.firebaseio.com` |
| Región | `us-central1` |
| Authentication | Correo/contraseña habilitada; responsable y ESP32 creados; ambos inicios de sesión comprobados |
| Android | `mx.edu.badi.pastillero` |
| ID Firebase Android | `1:461409252301:android:5540a4a6c0dcc21b7c4a84` |
| Reglas remotas actuales | Denegación global y permisos limitados por UID vinculado, cuenta habilitada y corte temporal de sesión |
| Reglas ampliadas | Publicadas desde `firebase/database.rules.json`; 25 pruebas de reglas aprobadas |

`app/google-services.json` está guardado y validado contra proyecto/paquete. Se generó con los valores oficiales visibles de la app registrada y su clave pública Android en Firebase/Google Cloud; el navegador no entregó un archivo descargado. No se incluyeron claves administrativas ni cuentas de servicio. La configuración local está excluida de Git.

El proyecto de referencia se inspeccionó en lectura: estructura de base, aplicaciones y autenticación. Sus reglas permisivas no se copiaron a Badi. Se conservó intacto.

## Arquitectura y contrato

Android conserva Java, interfaz XML, Room y WorkManager. Room usa la base `pastillero.db`, versión 3, con migraciones 1→2→3 que conservan historial y borradores. La cola de comandos también es persistente. Los listeners son asíncronos, el trabajo de disco se realiza en un ejecutor y la identidad del responsable se comprueba antes de importar la caché del SDK.

ESP32 conserva AccelStepper, PUL 25, DIR 26, cuatro posiciones y 3200 pasos/vuelta configurables. Mantiene `a/r/c/s` y secuencia `1→0, 2→0, 3→0`. Usa máquina de estados con `millis()`, red en otra tarea, reservas de dosis y eventos en NVS, TLS con certificados, reconexión Wi-Fi, renovación de sesión y recuperación de reinicio sin repetición automática.

El contrato detallado y su JSON están en `CONTRATO_FIREBASE.md`. Rutas principales: `/devices/<id>/ownerUid`, `deviceUid`, `plan`, `state`, `commandRequests`, `commandResults/<mode>` y `events`. Los eventos tipados representan confirmaciones, omisiones, bloqueos y recuperación; no se duplican en registros inconsistentes. Los comandos solicitados y sus respuestas están separados de las confirmaciones físicas.

`PING` y `APPLY_PLAN` utilizan identificadores estables y caducidad. No permiten mover el motor ni confirmar tomas. Los planes llevan destino `simulation`/`hardware`; cambiar de destino requiere retirar los horarios anteriores. Un firmware físico rechaza planes de simulación. Los borradores también conservan su destino.

El responsable solo escribe planes y solicitudes; el dispositivo solo escribe estado, resultados y eventos. Ambos leen exclusivamente su dispositivo vinculado. Los clientes no modifican UID, no borran historial y no pueden alterar un evento o comando existente; se permiten reintentos idénticos. Todo lo demás se deniega. Las reglas revisadas ya están desplegadas en PastilleroBadi; incluyen revocación mediante `access/users/<uid>`.

## Validaciones

| Comprobación | Resultado | Evidencia |
|---|---|---|
| APK Android con configuración de Badi | Aprobada, versión `1.3-access`, código 4 | `reports/android-access-build.log` |
| Pruebas unitarias Android | 9 aprobadas | `app/build/test-results/testDebugUnitTest/` |
| Room en emulador API 24, app 1.3 | 3 aprobadas: reapertura, migración desde versión 1 y desde versión 2 | `reports/room-access-tests.log` |
| Controlador y comandos C++ en PC | 24 aprobadas, sin GPIO ni puertos | `reports/controller-tests.log` |
| Reglas, duplicados, reconexión SDK y validador C++ con Firebase Emulator | 25 aprobadas; 0 fallos y 0 omitidas | `reports/firebase-access-tests.log` |
| ESP32 físico y simulación | Ambas variantes compiladas y enlazadas correctamente; simulación restaurada | `reports/firmware-validation.log` |
| Lectura pública a Firebase real | Rechazada correctamente | `reports/firebase-setup/live-probe.json` |
| Autenticación real del responsable mediante API REST oficial | Cuenta creada e inicio de sesión aprobado | `reports/firebase-setup/owner-authentication.json` |
| Autenticación real del ESP32 mediante API REST oficial | Cuenta creada e inicio de sesión aprobado | `reports/firebase-setup/device-authentication.json` |
| Reglas y acceso REST con las dos cuentas contra Firebase real | 20 comprobaciones aprobadas | `reports/firebase-setup/live-probe.json` |
| Backend administrativo: autorización, bloqueo, sesiones, administrador protegido y conflictos | 12 pruebas locales aprobadas con dobles de SDK | `reports/admin-access-tests.log` |
| Android SDK ↔ Firebase real en emulador QA API 24 | 1 prueba instrumentada aprobada: ambas cuentas, permisos, PING/resultados, reintento offline y renovación de token | `reports/firebase-setup/android-live.json` y `reports/android-firebase-live.log` |
| Dashboard ↔ backend ↔ Firebase Admin real | Pendiente de cuenta administrativa y ADC | No ejecutada |
| Firebase real ↔ ESP32 ejecutando firmware | Pendiente | No ejecutada |
| Pérdida/reconexión Wi-Fi en ESP32 real | Pendiente | No ejecutada |
| Revisión visual nueva del APK | Pendiente; la apertura de pantalla del emulador fue rechazada por la revisión automática, sin motivo adicional | Las pruebas instrumentadas sí se ejecutaron |
| Motor, sensor y botón reales | Pendiente | No ejecutados |

Lint actual: **0 errores, 1 advertencia**, recomendación de actualizar Gradle. Se revisaron las 31 advertencias previas: se trasladaron textos XML a recursos, se corrigieron concatenaciones señaladas, se añadió icono, se definió el idioma español y se completó la política de respaldo anterior a Android 12. Se mantuvieron las versiones probadas; las sugerencias anteriores sobre nuevas versiones de SDK/dependencias no se resolvieron mediante actualizaciones mayores ni supresiones. El recuento corresponde al informe actual de lint, no a una afirmación de que todas las dependencias sean las más nuevas.

No se usó una migración destructiva de Room ni se ocultaron comprobaciones de lint. El emulador Firebase usa `demo-pastillero`; sus usuarios son identidades locales de prueba. Sus pruebas no equivalen a ejecutar Wi-Fi/TLS sobre un ESP32. El puente C++ ejecuta el mismo validador de comandos en el PC, sin hardware.

## Configuración privada y archivos principales

Todas las rutas siguientes parten de `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

| Archivo | Función |
|---|---|
| `app/google-services.json` | Configuración pública Android del proyecto nuevo; ignorada en Git |
| `firebase-config.properties` | URL, `deviceId` y `commandMode`; configuración local |
| `firmware/PastilleroESP32/secrets.h` | Cuenta ESP32 configurada; completar personalmente `WIFI_SSID` y `WIFI_PASSWORD` |
| `private/integration.local.properties` | `owner.email` y `owner.password` guardados localmente; `device.email` y `device.password` guardados localmente. Ignorado en Git; no se compila en APK |
| `firmware/PastilleroESP32/config.h` | `PASTILLERO_DRY_RUN=1` por defecto y GPIO |
| `firmware/PastilleroESP32/Controller.h` | Horarios, confirmación, omisión, calibración y secuencia |
| `firmware/PastilleroESP32/Commands.h` | Validación de modo, caducidad y comandos |
| `firmware/PastilleroESP32/PastilleroESP32.ino` | Colas, Wi-Fi, TLS, Authentication, RTDB y NVS |
| `app/src/main/java/mx/edu/badi/pastillero/` | Repositorio, trabajadores de sincronización, entidades y migraciones |
| `app/src/main/res/` | Interfaz XML, textos, icono y políticas de respaldo |
| `firebase/database.rules.json` | Reglas de acceso por identidad y ruta |
| `firebase/rules.test.mjs` | Pruebas de reglas e intercambio con C++ |
| `app/src/androidTest/` | Persistencia y migraciones de Room |
| `tests/` | Pruebas C++ y puente de comandos |
| `releases/1.3/` | APK nuevo y dos imágenes ESP32 con credenciales locales; entrega 1.2 conservada |
| `admin-backend/` | Backend reservado a administración web, pruebas y aprovisionamiento deliberado |
| `docs/ADMINISTRACION_WEB.md` | Permisos, API, auditoría, límites y pasos de activación administrativa |
| `private/dashboard-admin.local.json` | UID administrativo principal pendiente; excluido de Git |

Los binarios ESP32 de esta carpeta se excluyen de Git porque futuras recompilaciones podrían contener credenciales locales. El APK no contiene la contraseña del responsable ni la del dispositivo. No se publicó nada en GitHub.

## Antes de las pruebas físicas

Las cuentas del responsable y del ESP32 ya están creadas y ambos inicios de sesión fueron verificados. Completar las variables Wi-Fi locales y verificar la integración ejecutada en Android y ESP32 primero en simulación. Los UID y las reglas ya están aprovisionados. Revisar el modelo de placa/flash, adaptación eléctrica TB6600, corriente/microstepping, sensor y presencia de blíster. Seguir `CONFIGURACION.md` para confirmar calibración, regreso a cero, pulsación nueva, omisión de cinco minutos, reconexión, duplicados y reinicio durante entrega.

No usar medicamentos reales. No cargar todavía firmware ni alimentar el mecanismo para estas verificaciones de software. React y avisos móviles garantizados con la aplicación cerrada corresponden a una fase posterior.

## Entrega 1.2 conservada y verificada

**55 pruebas automatizadas aprobadas**, sin fallos ni casos omitidos: 24 C++, 19 Firebase Emulator, 9 JVM y 3 Room. Verificación de integridad y correspondencia entre fuentes compiladas y binarios aprobada.

| Variante | Programa según compilador | Variables globales |
|---|---:|---:|
| hardware | 1100736 B | 50192 B |
| simulation | 1094480 B | 50104 B |

Las asignaciones dinámicas de TLS/JSON y el margen de memoria en ejecución requieren validación en el ESP32 real. Los binarios son imágenes de aplicación; no son imágenes completas de flash. Se comprobó la tabla de particiones de 4 MiB con 256 KiB NVS y aplicación desde `0x50000`.

- `releases/1.2/PastilleroBadi-1.2-debug.apk`: 7109672 bytes. SHA-256: `CCE5F3F3F4F846EFD4C8EF88DBA73ADCFDCC463B4830D5110513F47CC1A100E5`.
- `releases/1.2/PastilleroESP32-hardware.bin`: 1100880 bytes. SHA-256: `2DC1CCF7DB5D0870EB86A46615338FC4BABD47799617FDA2E6BFD75673E54D2C`.
- `releases/1.2/PastilleroESP32-simulacion.bin`: 1094624 bytes. SHA-256: `DD88880063AE897BC150B1D4E4A3364BA551F617E3A3D6445A490518129B04EF`.

## Actualización 1.3: cuentas y administración preparada

Ambas cuentas se crearon mediante la API oficial y se verificó su inicio de sesión. La cuenta del ESP32 utiliza el identificador elegido `[identificador de cuenta omitido]`; no se creó un buzón Gmail ni se verificó su propiedad. Contraseñas únicamente en `private/integration.local.properties` y, para la cuenta del dispositivo, en `firmware/PastilleroESP32/secrets.h`; no se incluyen en Android. Wi-Fi sigue pendiente.

El backend administrativo está preparado para listar usuarios, consultar todos los dispositivos y bloquear/restablecer permisos mediante un administrador independiente y protegido. React, cuenta administrativa principal, ADC y despliegue quedan pendientes. No se generó una cuenta de servicio ni se habilitó facturación. La protección del administrador impide bloquearlo desde la API; Firebase Console/IAM conserva la autoridad del propietario del proyecto.

Al recibir una revocación, Android retira listeners remotos y cancela trabajos de sincronización; Room se conserva. Las reglas rechazan sesiones anteriores al corte incluso después de restablecer acceso. Esto no elimina datos descargados ni cancela planes ya almacenados en un dispositivo sin red.

Pruebas de esta actualización: 25 reglas Firebase Emulator, 12 servicio administrativo y 9 JVM aprobadas, sin fallos ni omitidas. Las 24 pruebas C++ previas siguen siendo aplicables: no se modificó el controlador. Las 3 pruebas Room volvieron a aprobar con la app 1.3. Además, 1 prueba instrumentada Android SDK contra Firebase real aprobó; sus credenciales llegaron solo en tiempo de ejecución, sin incorporarlas al APK. La prueba realiza PING y resultados en simulación, no escribe horarios ni eventos de dosis. El SDK del rol dispositivo durante esa prueba no equivale a ejecutar firmware ESP32. Las 20 comprobaciones REST reales son adicionales. La revisión visual y la administración privilegiada real siguen pendientes.

Entregables nuevos; la versión 1.2 está conservada y respaldada bajo `archives/before-device-auth-*`. Los binarios ESP32 1.3 contienen la cuenta local del dispositivo y están excluidos de Git; no deben compartirse. Simulación restaurada por defecto.

- ESP32 hardware: programa 1100924 B; variables globales 50192 B.
- ESP32 simulation: programa 1094672 B; variables globales 50104 B.
- `releases/1.3/PastilleroBadi-1.3-debug.apk`: 7109676 B. SHA-256 `A931379A1220B31A2DD9B5B4E298245966EFDEE0CEC0C7DEDFB175C8B8D6D767`.
- `releases/1.3/PastilleroESP32-hardware.bin`: 1101072 B. SHA-256 `CFC94DF5CDEA7342B76CAFC6BB7C0BB04D8BACC3C4DD77373ACFE4F87E7B8E88`.
- `releases/1.3/PastilleroESP32-simulacion.bin`: 1094816 B. SHA-256 `8EE5B39F5E92C4A553638BB5C5102490637C2B63DF3F14A02288173531C9185B`.

Resumen de evidencia: **74 casos automatizados aprobados** (24 C++ del controlador sin cambios, 25 reglas, 12 servicio administrativo, 9 JVM, 3 Room y 1 integración Android SDK real), además de 20 comprobaciones REST reales. No se declara ejecutada la integración Firebase Admin real ni el hardware.

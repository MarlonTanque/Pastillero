# Configuración del proyecto

Carpeta única: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

## 1. Aplicación Android

El archivo ya guardado es `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\app\google-services.json`. Contiene la configuración pública de la app registrada: proyecto `pastillerobadi`, número `461409252301`, paquete `mx.edu.badi.pastillero` e identificador `1:461409252301:android:5540a4a6c0dcc21b7c4a84`.

El archivo se generó a partir de los valores oficiales visibles en Firebase Console y Google Cloud, porque la descarga del navegador no devolvió un archivo local. No es una cuenta de servicio ni una clave administrativa. Solo se incluyen los campos necesarios para Authentication y Realtime Database; no se configura Storage ni OAuth.

Gradle valida proyecto y paquete y prepara `FirebaseOptions`. `firebase-config.properties` contiene la URL de la base, el dispositivo `pastillero-01` y `commandMode=simulation`. Ambos archivos de configuración están excluidos de Git.

## 2. Cuentas personales

La cuenta del responsable ya se creó en **PastilleroBadi** y se comprobó su inicio de sesión mediante la API REST oficial. Sus datos están en `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\integration.local.properties`, campos `owner.email` y `owner.password`, excluidos de Git. No se guardan tokens en el informe.

La cuenta independiente del ESP32 también está creada y su inicio de sesión fue comprobado. Se utiliza el identificador `[identificador de cuenta omitido]` elegido para el dispositivo; el buzón no se ha verificado ni se ha creado una cuenta de Google. Authentication es un servicio real, aunque el identificador se haya elegido para pruebas. La recuperación por correo requiere controlar el buzón. Los campos `device.email` y `device.password` están guardados en el mismo archivo privado. Las dos identidades tienen funciones distintas:

1. Responsable: correo que controles y una contraseña nueva; se utiliza para iniciar sesión en Android.
2. Dispositivo: otro correo identificador y otra contraseña, exclusivos del ESP32.

No introducir la contraseña de la cuenta Google del navegador. Estas son cuentas de usuarios de la aplicación. No enviar contraseñas por mensajes ni incluirlas en documentación.

Los UID de ambas cuentas se prepararon en `private/provision-identities.json`. La vinculación autorizada ya está aprovisionada en `/devices/pastillero-01/ownerUid` y `/devices/pastillero-01/deviceUid` desde Firebase Console. Los clientes no pueden cambiar esos vínculos. Las reglas de `firebase/database.rules.json` ya están publicadas exclusivamente en este proyecto nuevo; permiten acceso limitado a cuentas vinculadas y habilitadas. El acceso público sigue denegado. Los registros `access/users/<uid>` también están preparados para la revocación. Consultar `ADMINISTRACION_WEB.md` para la fase administrativa posterior.

## 3. ESP32

Archivo exacto: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\firmware.local.json`.

Completar personalmente:

| Variable | Valor que se introduce |
|---|---|
| `WIFI_SSID` | Nombre exacto de la red Wi-Fi de 2.4 GHz |
| `WIFI_PASSWORD` | Contraseña de esa red |
| `DEVICE_EMAIL` | Ya configurado con el identificador exclusivo del ESP32 |
| `DEVICE_PASSWORD` | Ya configurado; guardado únicamente en archivos privados |

`FIREBASE_API_KEY`, `FIREBASE_DATABASE_URL` y `DEVICE_ID` se preparan automáticamente con la configuración pública del proyecto. No colocar credenciales administrativas. El modo seguro está en la sección4 de `PastilleroESP32.ino`: `PASTILLERO_DRY_RUN=1`.

`PASTILLERO_STEPS_PER_TURN` permite configurar el microstepping; por defecto 3200 y debe ser divisible entre cuatro y cinco para conservar ambos perfiles. Cualquier cambio requiere recalibrar. Se conservan PUL GPIO 25, DIR GPIO 26 y comandos `a`, `r`, `c`, `s`.

## 4. Compilación y validación

Con JDK de Android Studio: `gradlew.bat :app:assembleDebug :app:testDebugUnitTest :app:lintDebug :app:assembleDebugAndroidTest`. Abrir esta carpeta raíz, no la carpeta `app` por separado.

`tools/validate-firmware.ps1` compila fuente pública y copia privada, ambas en simulación y hardware; el .ino mantiene simulación por defecto. No ejecuta una carga. En `firebase/`, `npm ci` seguido de `npm test` valida reglas contra un emulador local de Realtime Database, proyecto `demo-pastillero`.

Las pruebas C++ usan Zig 0.14.1 u otro compilador C++ compatible. Compilar `tests/controller_test.cpp` y `tests/command_bridge.cpp`; este último genera `reports/command-bridge.exe` para la prueba del validador C++ con Firebase Emulator.

Las pruebas de Room se ejecutan en el emulador Android de QA. No seleccionan un teléfono físico. La migración conserva el historial y los borradores de las versiones 1 y 2 y lleva la base a versión 4 mediante migraciones aditivas 1→2→3→4.

## 5. Integración real y pruebas físicas posteriores

`tools/live_probe.py` utiliza únicamente cuentas normales y archivos locales ignorados. El archivo opcional `private/integration.local.properties` admite `owner.email`, `owner.password`, `device.email` y `device.password` para esa prueba automatizada; estos valores no se compilan en el APK. El informe no imprime credenciales ni tokens. Un resultado `PENDING` indica que no se ejecutó la integración completa.

Antes de cambiar de simulación a hardware, retirar todos los horarios simulados, sincronizar el plan vacío y revisar la configuración. Las reglas impiden cambiar el destino de un plan que todavía contiene horarios. El firmware rechaza planes del otro modo y retira su plan futuro almacenado si detecta ese cambio al reconectarse. Los borradores locales conservan su destino y no se publican automáticamente en otro modo.

Después de autorizar la fase física: comprobar placa, flash, niveles del TB6600, alimentación independiente del motor, corriente, microstepping y sensor. Con mecanismo vacío, verificar `a/r/c` y `s`: 640→0, 1280→0, 1920→0, 2560→0, dos segundos de entrega y quince de intervalo. Probar botón mantenido, confirmación posterior, omisión de cinco minutos, ausencia de blíster, desconexión Wi-Fi y reinicio durante entrega. No usar medicamentos reales. Una compilación o prueba en PC no acredita estas pruebas físicas.

## 6. Administración futura

Backend y pruebas en `admin-backend/`. Configuración privada exacta: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\dashboard-admin.local.json`. Falta elegir una cuenta administrativa independiente, completar `protectedAdminUid`, preparar ADC y autorizar la emisión del claim. El servicio no está desplegado ni iniciado. El dashboard administrativo privilegiado sigue pendiente; React móvil ya está integrado en el APK. Instrucciones: `ADMINISTRACION_WEB.md`.

La prueba Android SDK real optativa está en `FirebaseConnectionTest.java`; solo se habilita mediante `tools/run_android_live.py`, que toma credenciales del archivo privado y exige el AVD `PastilleroBadiQA` en `emulator-5580`. No se compilan esas credenciales. Para ejecutar solo Room, seleccionar explícitamente `mx.edu.badi.pastillero.RoomOfflineTest`; la prueba real está fuera de la ejecución rutinaria sin credenciales. La prueba del SDK usa únicamente PING y resultados de simulación.

## Entrega de estudio 1.4

El APK nuevo está en `releases/1.4/PastilleroBadi-1.4-debug.apk` y las dos imágenes ESP32 en la misma carpeta. La fuente conserva simulación como modo predeterminado. Core ESP32 utilizado: 3.3.12. El nombre de proyecto Gradle ahora es PastilleroBadi; el applicationId y la base Room versión 3 no cambian. Las seis guías de estudio y la comparación de los 74 casos están enlazadas desde README.md y RESULTADOS.md.


Revisión del 22 de octubre de 2026: la configuración y los certificados están dentro del .ino; los datos locales se materializan mediante generate_private_firmware.py. La carpeta del sketch contiene solo .ino y partitions.csv. Referencia elegida, procedimiento privado y evidencia: COMPARACION_CRUDSQLITE1.md y UNIFICACION_FIRMWARE.md.

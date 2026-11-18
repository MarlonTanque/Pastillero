# Inicio de pruebas conectadas — 17 de noviembre de 2026

Se inspeccionó la app instalada en el emulador Pixel_10_Pro_XL (emulator-5554), versión 2.0-simulacion, versionCode 7. Su proceso está activo y se observó la pantalla de historial sin eventos. No se reinstaló la app ni se borró Room.

Desde la computadora se autenticó la cuenta responsable en el proyecto dedicado pastillerobadi (HTTP 200). Las lecturas autorizadas de devices/pastillero-01/state y devices/pastillero-01/v2/state devolvieron HTTP 200 con valor nulo. El programa V2 también está ausente. Esto demuestra acceso REST a Firebase, no una prueba de ida y vuelta del SDK de la app ni comunicación del ESP32.

El usuario indica que el ESP32 se alimenta por separado y ya tiene cargado un sketch con su Wi-Fi. No se detectó un puerto USB del ESP32; solo puertos Bluetooth. La configuración privada de este proyecto todavía tiene marcadores Wi-Fi: no se deduce por ello qué datos contiene realmente la placa.

## Estado pendiente

No hay telemetría publicada por la placa que permita verificar su conexión o firmware. Se solicitó conectar solo el ESP32 por USB de datos con la alimentación del NEMA/TB6600, servo y bomba desconectada. Abrir el puerto serie puede reiniciar el ESP32, por lo que aún no se abrió ningún puerto. No se cargó firmware, enviaron comandos ni escribieron horarios, estados o resultados en RTDB. No se fabricaron acuses del ESP32 mediante pruebas en PC.

Después de identificar la placa y su sketch: revisar arranque, conexión Wi-Fi, reloj, autenticación/TLS y reglas; comprobar que aparece telemetría reciente y solo entonces realizar un PING con acuse producido por el ESP32 real. La dispensación, servo y bomba requieren una fase posterior con montaje y recorrido comprobados y material inerte. Ninguna prueba física se declara aprobada aquí.

Evidencia local sin secretos: reports/conexion-20261117.json. No se publicaron estos cambios en GitHub automáticamente.

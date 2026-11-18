# PastilleroBadi — Wi-Fi configurable desde Android

Proyecto ISC0633. Raíz para Android Studio: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

Repositorio del equipo: [MarlonTanque/Pastillero](https://github.com/MarlonTanque/Pastillero). Para clonar, configurar Android/ESP32 y continuar el dashboard web, empezar por [COLABORACION_GITHUB.md](docs/COLABORACION_GITHUB.md). El React actual está integrado en el APK; en navegador usa demostración local. La web administrativa independiente sigue pendiente.

Este repositorio publica fuentes y plantillas. La configuración local, credenciales, respaldos, registros completos y entregables compilados permanecen excluidos; las rutas a releases/archives/private que aparecen en informes históricos describen el equipo original.

## Configuración Wi-Fi y botón de confirmación

La versión 2.1 incorpora [Wi-Fi desde la app y conexiones físicas](docs/WIFI_DINAMICO_Y_CONFIRMACION.md). El cliente puede cambiar de router desde Ajustes, con un código de acceso del dispositivo; no necesita editar SSID/contraseña en Arduino. Las constantes Wi-Fi antiguas se conservan por compatibilidad, pero el driver usa la red guardada en NVS.

La pulsación de confirmación apaga buzzer/LED y muestra el acuse en el LCD compatible. La pulsación larga solo abre configuración en reposo y tras soltar el botón. El firmware sigue en simulación por defecto.

**Carga de firmware:** con la tabla de particiones actual no usar la receta estándar de Arduino: app0 está en 0x50000 y OTA en 0x49000. Usar `tools/upload_simulation.py` según la guía. La carga corregida de simulación y la respuesta serie están verificadas; el intercambio Wi-Fi desde un teléfono real y las pruebas de actuadores siguen pendientes. Ver RESULTADOS.md.

## Archivos principales

| Contenido | Ruta dentro del proyecto |
|---|---|
| Fuente Arduino pública, configuración visible y lógica única | `firmware/PastilleroESP32/PastilleroESP32.ino` |
| Valores locales privados | `private/firmware.local.json` |
| Sketch privado generado para Arduino IDE | `private/firmware/PastilleroESP32/PastilleroESP32.ino` |
| Android Java/XML y Room4 | `app/src/` |
| React/TypeScript y Glass | `web/src/` |
| Reglas/contrato Firebase | `firebase/database.rules.json`, `docs/CONTRATO_FIREBASE.md` |
| APK y cuatro variantes compiladas de Wi-Fi 2.1 (locales) | `releases/wifi-20261117/` |
| Sketch original y entregas anteriores | `original/`, `releases/`, `archives/` |

La carpeta principal Arduino contiene el .ino y la tabla técnica partitions.csv. No hay cabeceras propias. Wi-Fi, autenticación Firebase, pines, certificados TLS, estados y funciones están en 17 secciones dentro del .ino. Los valores públicos son marcadores; el generador copia la misma implementación y sustituye solo siete declaraciones para la copia privada.

## Estudio y evidencias

- [Unificación, estructura anterior/posterior y configuración](docs/UNIFICACION_FIRMWARE.md).
- [Comparación con los cuatro sketches de Kali y CRUDSQLITE1](docs/COMPARACION_CRUDSQLITE1.md).
- [Resultados actuales y limitaciones](docs/RESULTADOS.md).
- [Arduino línea por línea](docs/GUIA_ARDUINO_LINEA_POR_LINEA.md).
- [Android línea por línea](docs/GUIA_ANDROID_LINEA_POR_LINEA.md).
- [Defensa oral](docs/GUIA_DEFENSA_ORAL.md).
- [Firebase](docs/GUIA_FIREBASE.md), [Room](docs/GUIA_ROOM_SQLITE.md), [hardware](docs/GUIA_CONEXIONES_HARDWARE.md).

Se eligió MQTT.ino de Kali como referencia más completa: Firebase, LDR, DHT11, LED/PWM, relay y tiempos. Se conserva su estilo por secciones y funciones, manteniendo los requisitos de seguridad y control del pastillero.

## Repetir validación sin hardware

1. Preparar únicamente la identidad Firebase del equipo en `private/firmware.local.json`; SSID/contraseña se reciben desde la app, sin rellenar los marcadores Wi-Fi. Para generar la copia privada, ejecutar `python tools/generate_private_firmware.py`. También puedes editar solo los siete literales del .ino privado e importarlos con `python tools/generate_private_firmware.py --import-config`.
2. `tools/validate-firmware.ps1`: compila fuente pública y copia privada, cada una con simulación y hardware. No carga firmware ni abre serie.
3. `tools/validate-integration.ps1`: controlador C++ y contrato local Java/Firebase; `python -m unittest discover -s tests -p test_private_firmware.py` prueba el generador.
4. `tools/validate-web.ps1`; Android: `gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug`.
5. `python tools/validate_android_emulators.py`: solo AVD PastilleroBadiQA/V2QA, nunca un teléfono físico. Incluye la prueba optativa SDK Firebase real con valores privados existentes.
6. En firebase/: `npm test`; en admin-backend/: `node --test`; sondeos de diagnóstico: `python tools/live_probe.py` y `python tools/live_probe_v2.py`.
7. `python tools/verify_version2.py`; guías: `python tools/generate_study_guides.py --verify`.

Se mantiene **NEMA17/TB6600, cuatro compartimentos útiles y cero vacío**, DRY_RUN=1 y periféricos opcionales deshabilitados localmente. Conservar toda credencial en private/, excluido de Git; no publicar binarios con datos locales. No usar medicamentos reales en pruebas futuras. Los cierres anteriores se conservan como documentación histórica y no describen la estructura vigente.

# Unificación verificable del firmware

Fecha: 22 de octubre de 2026. Raíz: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

## Estructura anterior y actual

Antes, conservado en el respaldo indicado en `reports/unification-backup.json` (297 archivos verificados):

```text
firmware/PastilleroESP32/
  PastilleroESP32.ino
  Commands.h
  Controller.h
  config.h
  secrets.example.h
  secrets.h
  trust.h
  partitions.csv
```

Ahora:

```text
firmware/PastilleroESP32/
  PastilleroESP32.ino       <- única implementación pública, con marcadores
  partitions.csv           <- tabla técnica de flash requerida por Arduino
private/
  firmware.local.json      <- solo valores locales; excluido de Git
  firmware/PastilleroESP32/
    PastilleroESP32.ino     <- copia generada con valores locales
    partitions.csv
```

Las seis cabeceras propias se retiraron de la carpeta activa. La caché `firmware/build/doit` anterior se conservó en `archives/retired-build-doit-20261022`; las compilaciones actuales usan carpetas `unified-*`. No se eliminaron cabeceras de bibliotecas. Las referencias históricas en informes conservados describen versiones anteriores, no dependencias del firmware actual.

## Configuración real visible en el sketch público

```cpp
const char* WIFI_SSID = "INTRODUCIR_WIFI"; // CONFIG_LOCAL
const char* WIFI_PASSWORD = "INTRODUCIR_PASSWORD_WIFI"; // CONFIG_LOCAL
const char* FIREBASE_DATABASE_URL = "https://pastillerobadi-default-rtdb.firebaseio.com"; // CONFIG_LOCAL
const char* FIREBASE_API_KEY = "INTRODUCIR_FIREBASE_API_KEY"; // CONFIG_LOCAL
const char* DEVICE_EMAIL = "INTRODUCIR_CORREO_DISPOSITIVO"; // CONFIG_LOCAL
const char* DEVICE_PASSWORD = "INTRODUCIR_PASSWORD_DISPOSITIVO"; // CONFIG_LOCAL
const char* DEVICE_ID = "pastillero-01"; // CONFIG_LOCAL
```

Es código real, con siete declaraciones marcadas `CONFIG_LOCAL`. No contiene cuentas ni contraseñas reales. La URL y el identificador del dispositivo son públicos. Las raíces TLS completas están dentro del mismo .ino; no se sustituye la validación por setInsecure.

## Generación privada y dónde introducir los datos

Archivo de entrada exacto: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\firmware.local.json`. Campos: WIFI_SSID (nombre de red), WIFI_PASSWORD (contraseña de esa red), FIREBASE_DATABASE_URL (URL dedicada ya configurada), FIREBASE_API_KEY (configuración cliente del proyecto), DEVICE_EMAIL y DEVICE_PASSWORD (cuenta ordinaria exclusiva del dispositivo ya existente), DEVICE_ID (pastillero-01). No enviar estos datos por chat ni añadir cuentas de servicio.

Ejecutar desde la raíz: `python tools/generate_private_firmware.py`. Genera `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\firmware\PastilleroESP32\PastilleroESP32.ino`. Se puede abrir en Arduino IDE para ver toda la configuración y lógica juntas. Para mantener una implementación única, editar la lógica en la fuente pública y los datos en el JSON privado; regenerar después. Cada declaración se sustituye exactamente una vez, se escapan comillas/barra inversa/Unicode y se rechaza un proyecto/dispositivo inesperado. Si cambia una copia privada existente, el generador la respalda antes de regenerar. La copia privada no se distribuye.

También puedes introducir los datos directamente en las siete constantes visibles del .ino privado, desde Arduino IDE. Conserva los nombres y el comentario CONFIG_LOCAL; después ejecuta `python tools/generate_private_firmware.py --import-config`. La herramienta importa solo esos literales al JSON local y regenera desde la misma fuente. Rechaza cambios en funciones, pines, certificados o cualquier otra instrucción del archivo privado. Respalda la configuración anterior y no imprime valores. Esta ruta permite editar los datos dentro del .ino sin mantener dos implementaciones distintas. Doce pruebas verifican generación, escapes, importación y rechazo de cambios de lógica.

Las credenciales existentes se conservaron al retirar la cabecera privada. Wi-Fi requiere los datos personales del montaje antes de una futura prueba en chip. Los valores sensibles permanecen excluidos de Git, igual que los binarios que pueden incorporarlos.

## Navegación del archivo final

| Línea | Sección |
|---:|---|
| 6 | 1. LIBRERIAS |
| 35 | 2. CONFIGURACION WIFI |
| 42 | 3. CONFIGURACION FIREBASE Y CONFIANZA TLS |
| 711 | 4. CONFIGURACION DE PINES Y MODO SIMULACION |
| 748 | 5. CONSTANTES DEL MOTOR NEMA 17 Y TIEMPOS |
| 769 | 6. VARIABLES Y MODELOS DE SENSORES Y ACTUADORES |
| 847 | 7. VARIABLES DE HORARIOS, MEDICAMENTOS Y RESERVAS |
| 912 | 8. VARIABLES DE CONTROL Y ESTADOS |
| 1282 | 9. SETUP: INICIALIZACION UNA SOLA VEZ |
| 1297 | 10. LOOP: CICLO NO BLOQUEANTE |
| 1325 | 11. FUNCIONES WIFI Y FIREBASE |
| 1561 | 12. FUNCIONES DEL MOTOR Y CALIBRACION |
| 1627 | 13. FUNCIONES DE DISPENSACION |
| 1640 | 14. FUNCIONES DE SENSORES |
| 1683 | 15. FUNCIONES DE ALERTAS, LCD Y PERIFERICOS |
| 1779 | 16. FUNCIONES DE CALENDARIO Y VALIDACION DE HORARIOS |
| 1846 | 17. FUNCIONES DE SINCRONIZACION Y PERSISTENCIA |

Los prototipos anuncian las funciones que siguen a setup/loop. La extracción atenderDispensacion conserva el bloque de avance del loop. Las 22 funciones originales del adaptador ESP32 permanecen; Commands/Controller eran puentes de inclusión para pruebas y su modelo ya estaba en el .ino. Las pruebas ahora definen PASTILLERO_HOST_TEST e incluyen directamente ese .ino, por lo que no hay segunda implementación de control.

Se conservaron las clases existentes del modelo, las interfaces de prueba y los adaptadores que implementan Stream/Port. No se crearon clases nuevas de firmware. La definición de tipos y el adaptador deben preceder sus instancias/prototipos por las reglas de C++; esta es la razón técnica de su ubicación en la sección8, aunque sus funciones se estudien también por tema.

El montaje conserva NEMA17/TB6600, PUL25/DIR26, 3200 pasos/vuelta y cinco espacios totales: cuatro útiles y cero vacío. El comando s recorre 1→0,2→0,3→0,4→0; a/r/c mantienen calibración. El perfil de cuatro posiciones sigue disponible por compatibilidad. Los periféricos opcionales continúan bloqueados localmente y DRY_RUN=1 es el valor por defecto en ambas fuentes.

## Evidencia y estado de validación

`reports/unification-functions.json` enumera funciones conservadas; `kali-reference-comparison.json` prueba la elección de referencia; las guías por línea se regeneran desde el código final. Los resultados de compilación, pruebas e integridad se cierran en RESULTADOS.md. La compilación no ejecuta firmware ni demuestra Wi-Fi/NVS/GPIO en chip. No se cargó código ni se accionó el motor.

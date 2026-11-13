# Colaboración — PastilleroBadi

Repositorio: https://github.com/MarlonTanque/Pastillero. Preparación: 13 de noviembre de 2026. Esta entrega comparte fuentes; no despliega servicios, modifica reglas en producción ni carga firmware.

## Abrir el proyecto

```sh
git clone https://github.com/MarlonTanque/Pastillero.git PastilleroBadi
cd PastilleroBadi
git switch -c nombre-del-cambio
```

Abrir la carpeta raíz `PastilleroBadi` en Android Studio, no solo `app/`. Arduino IDE abre `firmware/PastilleroESP32/PastilleroESP32.ino`. La carpeta de ese sketch contiene únicamente `.ino` y `partitions.csv`.

| Carpeta | Trabajo del equipo |
|---|---|
| `app/src/main/java/mx/edu/badi/pastillero/` | Activities, puente React, Room, repositorios, horarios y Workers |
| `app/src/main/res/` | XML, recursos y vista nativa de compatibilidad |
| `app/schemas/` | Esquemas Room 1..4; conservar migraciones e historial |
| `firmware/PastilleroESP32/` | Lógica canónica ESP32, configuración pública y certificados TLS |
| `firmware/firmware.local.example.json` | Plantilla sin credenciales para una copia privada local |
| `web/src/` | React/TypeScript móvil ya integrado en el APK |
| `firebase/` | Reglas y pruebas de Realtime Database |
| `admin-backend/` | API administrativa preparada; todavía no desplegada |
| `tests/`, `tools/` | Pruebas C++/Python y herramientas de compilación/estudio |
| `docs/` | Contrato común, auditoría, hardware y guías por línea |

No se distribuyen `private/`, configuración personal de Firebase, bibliotecas instaladas, respaldos, registros completos ni APK/binarios. Permanecen en el equipo original.

## React actual y sitio web pendiente

`web/src/bridge.ts` usa `window.BadiNative` dentro del WebView. En un navegador normal cae en `preview.ts` y localStorage: es una demostración, no sincronización real con Firebase ni historial Room del teléfono.

Para explorar la interfaz existente, con Node.js 22 o posterior y npm:

```sh
cd web
npm ci
npm run dev
```

Abrir http://127.0.0.1:4173. `npm run build` valida TypeScript y genera recursos dentro de `app/src/main/assets/dashboard/`; esos cambios afectan la interfaz del APK y deben revisarse junto con Java. `npm test` ejecuta las pruebas React. Para las pruebas de navegador, instalar primero `npx playwright install chromium` y ejecutar `npm run test:e2e`.

El dashboard web independiente puede desarrollarse en una carpeta nueva `dashboard-web/`, conservando el frontend móvil. Debe reutilizar el contrato de `docs/CONTRATO_FIREBASE.md`, la geometría de cinco espacios, fechas UTC/zonas IANA e identificadores estables. No copiar la lógica de demostración como si fuera un cliente de producción.

La web necesita autenticación Firebase propia. Una cuenta ordinaria solo accede al dispositivo vinculado y habilitado según las reglas. Las operaciones de administración de usuarios pasan por el backend confiable, nunca por credenciales administrativas en React. Consultar `docs/ADMINISTRACION_WEB.md` para `GET /api/users`, `GET /api/devices` y `PATCH /api/users/<uid>/access`, control de versiones, token y administrador protegido. Su activación con ADC y cuenta dedicada sigue pendiente; no ejecutar `bootstrap-admin.mjs` como parte de instalar el proyecto.

## Configuración Android local

1. Pedir al responsable acceso individual al proyecto Firebase `pastillerobadi`, sin compartir contraseñas de otras cuentas.
2. Obtener de Firebase Console la configuración de la app Android ya registrada con paquete `mx.edu.badi.pastillero` y guardarla como `app/google-services.json`. Ese archivo está ignorado por Git.
3. Si se necesitan ajustes adicionales, copiar `firebase-config.example.properties` a `firebase-config.properties` y completar los valores de la misma app. No dejar `REEMPLAZAR`: ese archivo tiene prioridad sobre `google-services.json`. Mantener `commandMode=simulation`. También puede omitirse para usar los datos del JSON y los valores predeterminados.
4. Android Studio configura el SDK local. No versionar `local.properties` ni cambiar el applicationId o las reglas para eludir errores de acceso.
5. Iniciar sesión con una cuenta propia autorizada. Tener el código o una API key de cliente no concede permisos de base de datos. Las reglas siguen denegando acceso público y escritura de permisos desde clientes.

Desde la raíz, en Windows:

```powershell
.\gradlew.bat :app:assembleDebug :app:testDebugUnitTest :app:lintDebug :app:assembleDebugAndroidTest
```

En Linux/macOS usar `./gradlew` (si el sistema no conserva el permiso, `chmod +x gradlew`). Compile SDK 36; usar el JDK de Android Studio compatible con el Wrapper. Room se mantiene en versión 4 con migraciones aditivas; nunca activar migración destructiva para facilitar una instalación.

## Firmware local sin publicar credenciales

Para estudiar o compilar la fuente pública no hace falta introducir contraseñas: contiene marcadores. Instalar el core ESP32 3.3.12, AccelStepper 1.64 y ArduinoJson 7.3.2, que son las versiones de la validación anterior; Wire/WiFi/HTTPClient/Preferences proceden del core. Placa usada: ESP32 DOIT ESP32 DEVKIT V1. Compilar con Verificar, sin cargar ni abrir un puerto serie durante QA.

Para preparar una copia local con datos propios:

```powershell
New-Item -ItemType Directory -Force private,reports | Out-Null
if (-not (Test-Path private\firmware.local.json)) {
    Copy-Item firmware\firmware.local.example.json private\firmware.local.json
}
# Editar personalmente el JSON privado; no pegar sus valores en issues o mensajes.
python tools\generate_private_firmware.py
```

`Copy-Item` es solo para la primera configuración: no repetirlo sobre un JSON privado ya completado. El generador conserva una sola implementación y produce `private/firmware/PastilleroESP32/PastilleroESP32.ino`. Los cambios de lógica se realizan en el `.ino` público, con marcadores intactos; después se regenera la copia privada. La cuenta del ESP32 es ordinaria y limitada, no una cuenta de servicio. Ver `docs/UNIFICACION_FIRMWARE.md` para edición/importación de los siete campos.

Mantener `PASTILLERO_DRY_RUN=1` y las disponibilidades opcionales en 0. NEMA17/TB6600 conserva PUL25/DIR26, 3200 pasos/vuelta, cuatro compartimentos útiles y cero vacío, calibración `a/r/c` y secuencia `s`. Servo GPIO13, LCD SDA21/SCL22 requieren identificar módulo, tensión, adaptación de nivel, recorrido y mecánica antes de habilitarlos. El modelo de pantalla todavía no está confirmado; no se supone compatibilidad por el nombre WPHX-8. No cargar firmware, accionar motores o usar medicamentos reales como parte del desarrollo web.

## Pruebas del equipo

Además de Android y React, ejecutar sin hardware:

```sh
cd firebase
npm ci
npm test
```

Usa Firebase Emulator y el proyecto `demo-pastillero`; requiere Java compatible con firebase-tools. No sustituirlo por el proyecto real para las pruebas de reglas.

```sh
cd admin-backend
npm ci
npm test
```

Son pruebas con dobles del SDK; no activan el backend ni privilegios reales. Las pruebas `tests/*.cpp` compilan en PC la lógica del mismo `.ino` mediante `PASTILLERO_HOST_TEST`; algunos casos JSON requieren ArduinoJson. `tests/test_private_firmware.py` usa datos ficticios y un compilador Zig en `toolchain/zig/zig.exe`. Los scripts de QA completos tienen rutas locales Windows documentadas y requieren instalar sus herramientas/AVD antes de ejecutarse.

Los verificadores históricos de respaldos y compilaciones dependen de `archives/` e informes locales excluidos del repositorio; no deben considerarse CI portable. Los 204 casos y cuatro binarios del informe son evidencia histórica del 22 de octubre, no una prueba física ni una ejecución nueva después de cada clon.

## Flujo de cambios e integración

Trabajar en una rama y proponer un pull request hacia `main`. Revisar fuentes Java/XML, Room y el puente cuando cambie `web/`; revisar clientes, reglas y serialización cuando cambie el JSON. No publicar reglas nuevas, habilitar facturación ni distribuir contraseñas para que una prueba pase.

Mantener separados `program`, `commandRequests`, `commandResults`, `state` y `events`. La web puede solicitar PING/APPLY_PLAN con permisos ordinarios; no inventar DISPENSE remoto ni escribir CONFIRMED desde el navegador. Las confirmaciones son físicas y los reintentos conservan ID/token. Las altas/bajas administrativas necesitan el backend autorizado.

Antes de subir: revisar `git status` y `git diff --cached`. No añadir con fuerza archivos ignorados. Los compañeros sin permiso de escritura pueden trabajar mediante fork y pull request; el propietario puede conceder colaboración desde GitHub a usuarios concretos. El repositorio público no concede acceso a Firebase ni al dispositivo físico.

# SDK de aprovisionamiento Espressif

Origen: https://github.com/espressif/esp-idf-provisioning-android/tree/lib-2.4.4. Licencia Apache-2.0 y avisos originales conservados. `upstream.json` fija la etiqueta, hash del archivo descargado y hashes de las fuentes originales seleccionadas.

Se incluyó la clausura de dependencias Java de ESPDevice (33 clases), los diez protocolos `.proto` y sus clases Java generadas; no se incluyeron las interfaces de cámara/QR ni ESPProvisionManager. La app crea ESPDevice directamente, únicamente con TRANSPORT_SOFTAP y SECURITY_1. Las clases BLE/Security2 que conserva el SDK son dependencias de compilación del código original y no se ofrecen como flujo de la app.

Adaptaciones locales:

- Todas las llamadas Log del SDK usan PrivateLog, que descarta los mensajes. El código original registraba contraseña del AP y PoP, incluso durante depuración. También se retiraron las impresiones de stack trace que podrían copiar respuestas locales a logcat.
- SecureCapabilities exige sec_ver=1, un código hexadecimal de 24 caracteres y ausencia de la capacidad no_pop antes de crear una sesión. ESPDevice.initSession ejecuta esa comprobación antes de la selección original del esquema. No se permite degradar a Security0 ni negociar sin prueba de posesión.
- `build.gradle` es un módulo local Android Library, sin dependencias de cámara o JitPack. Usa protobuf-javalite 3.25.8, Tink Android 1.12.0 y EventBus 3.3.1. No se implementó criptografía propia.
- Las fuentes de protobuf se generaron una vez con protoc 3.25.8, descarga de Maven Central comprobada contra su checksum publicado. Se versionan para que Android Studio no dependa de un plugin protobuf incompatible con la API nueva de AGP. Para regenerar, usar `protoc --proto_path=src/main/proto --java_out=lite:src/main/java src/main/proto/*.proto`, expandiendo los archivos según el shell. No editar manualmente los archivos marcados como generados.

La excepción HTTP Android se limita a 192.168.4.1: el protocolo Security1 cifra la configuración y requiere PoP, además de la protección WPA2 del AP temporal. Firebase y cualquier otro destino siguen requiriendo HTTPS. Las claves del cliente Firebase y las cuentas del dispositivo son una configuración distinta de la red del usuario.

Estas fuentes son biblioteca externa adaptada. Las guías de estudio recorren las clases propias de la app y las dos políticas locales añadidas; no presentan las clases de protocolo generadas como código escrito para el proyecto.

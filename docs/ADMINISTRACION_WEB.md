# Administración reservada al futuro dashboard

La web tendrá una cuenta administrativa independiente. Android actúa como responsable y ESP32 como dispositivo: ninguno puede administrar usuarios, cambiar su propio rol ni ampliar sus permisos. El dashboard web administrativo continúa pendiente; React móvil ya existe en web/ y se integra en el APK. Esta entrega prepara el backend, el contrato y el control de acceso. La guía COLABORACION_GITHUB.md explica el punto de partida del equipo.

La autoridad completa reside en un backend confiable con Firebase Admin SDK. El navegador se autentica y envía su ID token por `Authorization: Bearer`; el backend verifica firma, proyecto, expiración, revocación y la identidad administrativa en cada petición. Exige a la vez el UID principal configurado y el custom claim `dashboardAdmin=true`, emitido únicamente desde un entorno administrativo.

No basta con comprobar que la petición viene de una página web: el código y las claves públicas del navegador pueden copiarse. La seguridad depende de la identidad y de la autorización del servidor. Nunca se coloca una clave de cuenta de servicio en React, Android o ESP32. El backend utiliza Application Default Credentials del host. No se creó ni descargó una clave administrativa.

## Cuentas y permisos

| Identidad | Acceso |
|---|---|
| Responsable Android | Su dispositivo vinculado, horarios y solicitudes; sujeto a habilitación y vigencia de sesión |
| ESP32 | Su dispositivo vinculado, estado, eventos y resultados; sujeto a habilitación y vigencia de sesión |
| Administrador web principal | Consulta global y administración desde el backend; cuenta separada de Android/ESP32 |
| Otros usuarios o público | Sin acceso a dispositivos |

Las reglas añaden `/access/users/<uid>` con `enabled` booleano, `role` (`owner` o `device`), `revokedAt` (segundos Unix) y `version` entero. Solo el backend o Firebase Console pueden escribir esos registros. Cada usuario puede consultar su propio registro para informar del bloqueo. Cada lectura/escritura de dispositivo requiere `enabled=true`, UID vinculado y `auth.token.auth_time > revokedAt`. Una sesión anterior al bloqueo no recupera permisos al habilitar de nuevo: se debe iniciar sesión otra vez.

El backend deniega bloquear al administrador principal y a cualquier cuenta que tenga el claim administrativo. La interfaz conserva así un administrador de recuperación. Un propietario del proyecto con acceso a Firebase Console/IAM sigue teniendo autoridad: una web no puede garantizar acceso permanente frente a quien controla el proyecto.

La revocación impide acceso nuevo al servidor y cancela la sincronización de Android al recibir la actualización. No borra Room ni retira datos que ya fueron descargados. Tampoco cancela una dosis reservada o un plan ya almacenado en un ESP32 sin red; detener el mecanismo es una operación física distinta. El dispositivo conserva su programación offline según el contrato de seguridad previo.

## API preparada

| Método y ruta | Resultado |
|---|---|
| `GET /api/users?pageToken=...` | Lista paginada de cuentas, estado y permisos; sin hashes de contraseña ni tokens |
| `GET /api/devices` | Consulta de todos los dispositivos para el administrador |
| `PATCH /api/users/<uid>/access` | Habilita/bloquea una cuenta ordinaria mediante `{ "enabled": false, "expectedVersion": 1 }` |

Un conflicto de versión devuelve 409. Un usuario ordinario recibe 403; una sesión revocada/ inválida recibe 401. Las peticiones desconocidas no permiten escritura arbitraria en la base. El SDK administrativo conserva la autoridad para ampliar operaciones en fases posteriores, pero cada nueva operación necesita su validación en el backend.

Al bloquear, primero se cierra el permiso de base; después se deshabilita Firebase Authentication y se revocan las sesiones. Si falla la red, el registro permanece cerrado. Las etapas se registran en `/administration/audit/<id>` con actor, destino, fecha y versión. El restablecimiento conserva el rol y el corte temporal de sesiones. Ni el backend ni la interfaz pueden promover un usuario ordinario mediante el endpoint de permisos.

## Activación posterior

1. Crear una cuenta administrativa dedicada y conservar personalmente sus credenciales. No reutilizar la cuenta responsable ni la del ESP32.
2. Completar `protectedAdminUid` en `C:\Users\milit\AndroidStudioProjects\PastilleroBadi\private\dashboard-admin.local.json`. El archivo está excluido de Git. `projectId` y `databaseUrl` ya están fijados a PastilleroBadi.
3. Preparar la identidad de servidor mediante ADC en un host controlado. No introducir credenciales privilegiadas en el chat ni en los clientes. No se habilitó facturación ni se desplegó un servicio de pago.
4. Tras autorizar el otorgamiento del privilegio administrativo, ejecutar `node admin-backend/bootstrap-admin.mjs` desde la raíz. Este paso comprueba que el UID es distinto de los vínculos del pastillero, registra el administrador principal y emite el custom claim. **No ejecutado en esta entrega.**
5. Desde `admin-backend/`, ejecutar `npm ci` y `npm start`. La API solo escucha en `127.0.0.1:8787`, no se ha iniciado en esta entrega. Antes de alojarla fuera del equipo se requiere HTTPS, límites de peticiones y configuración de origen del despliegue. El frontend futuro deberá servirse desde ese mismo origen.
6. Implementar React después, con pantalla de usuarios, bloqueo/restablecimiento, versiones y auditoría. Validar entonces la integración web real y la recuperación del administrador.

Las pruebas del servicio usan dobles del SDK; las pruebas de reglas usan Firebase Emulator. No equivalen a una sesión real del dashboard ni a la revocación ejecutada con Firebase Admin SDK contra el proyecto real.

Fuentes técnicas: [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup), [revocación de sesiones](https://firebase.google.com/docs/auth/admin/manage-sessions), [verificación de ID tokens](https://firebase.google.com/docs/auth/admin/verify-id-tokens).

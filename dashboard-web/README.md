# Dashboard administrativo — Pastillero Badi

Panel web para **el administrador**. Los responsables siguen usando la app Android; este panel decide qué pueden hacer en ella.

- **Usuarios y permisos:** lista las cuentas, bloquea/habilita una cuenta completa y activa o desactiva funcionalidades de la app por responsable.
- **Dispositivos:** estado V2 de cada pastillero (fase, calibración, revisión aplicada/publicada), carrusel de cinco posiciones (0 = retorno vacío, C1–C4 útiles), pautas publicadas y eventos recientes. Solo lectura: el panel no envía comandos al hardware.

| Funcionalidad | Qué bloquea en la app |
|---|---|
| Medicamentos | Crear, editar y eliminar pautas |
| Publicar al pastillero | Publicar el plan, reintentar, recargar/rebasar el programa remoto |
| Ajustes del dispositivo | Guardar posiciones, horizonte y periféricos |
| Diagnóstico y vista clásica | Comprobar conexión (PING) y abrir la vista nativa |

Detalles del modelo de permisos y de la API: [`docs/ADMINISTRACION_WEB.md`](../docs/ADMINISTRACION_WEB.md).

## Demostración (sin Firebase)

```sh
cd dashboard-web
npm ci
npm run dev
```

Abrir http://127.0.0.1:4174. Sin `.env.local` el panel usa datos ficticios en memoria; no contacta Firebase ni el backend.

## Uso real

1. Completar los pasos de *Activación posterior* en `docs/ADMINISTRACION_WEB.md` (cuenta administrativa dedicada, `private/dashboard-admin.local.json`, ADC y `bootstrap-admin.mjs`).
2. Copiar `.env.example` a `.env.local` y llenar la configuración **web pública** de la app registrada en el proyecto `pastillerobadi` (Firebase Console → Configuración del proyecto → Tus apps → Web). Nunca colocar aquí una cuenta de servicio.
3. Compilar y servir desde el backend (mismo origen, sin CORS):

   ```sh
   cd dashboard-web && npm ci && npm run build
   cd ../admin-backend && npm ci && npm start
   ```

   Abrir http://127.0.0.1:8787 con `"origin": "http://127.0.0.1:8787"` en la configuración privada.

Para desarrollar contra el backend real, `npm run dev` reenvía `/api` a `127.0.0.1:8787`; en ese caso `origin` debe ser `http://127.0.0.1:4174`.

## Pruebas

```sh
npm test        # Vitest con la API de demostración
npm run build   # verifica TypeScript y compila a dist/
```

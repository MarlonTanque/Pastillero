# Comparación real con CRUDSQLITE1

Fecha: 22 de octubre de 2026. Se leyeron fuentes, sin modificar ni compilar el proyecto de referencia.

## Localización y elección del sketch

Máquina VirtualBox: **Kali Linux MT**. Se abrió con VirtualBox y se inspeccionó `/home/kali/Arduino` en Thunar. Pruebas_2 se leyó con Mousepad y su copia de texto coincide con los bytes del disco normalizados a texto. Posteriormente se leyeron los cuatro sketches con lectores VDI/Ext4 abiertos en modo `rb`; no se montó el sistema para escritura ni se cambiaron los originales. Las copias con configuración real están en `private/kali-reference/`, excluidas de Git.

| Sketch real | Líneas | Funciones detectadas en el código |
|---|---:|---|
| `/home/kali/Arduino/sketch_jul27a/sketch_jul27a.ino` | 24 |  |
| `/home/kali/Arduino/Pruebas.ino/Pruebas.ino.ino` | 322 | firebase, ldr, dht |
| `/home/kali/Arduino/Pruebas_2/Pruebas_2.ino` | 352 | firebase |
| `/home/kali/Arduino/MQTT/MQTT.ino` | 1121 | firebase, mqtt, ldr, dht, pwm, relay, millis |

Se eligió **MQTT/MQTT.ino, 1121 líneas**, por sus funciones de lectura y control, no solo por longitud. Usa las mismas rutas `/tarjeta/dispositivos/LDR`, `DHT11`, `LED` y `RELAY` que MainActivity de CRUDSQLITE1. Pruebas_2 es principalmente diagnóstico/LED: declara sensores, pero su loop no lee LDR ni DHT11. Pruebas.ino sí lee esos sensores, sin PWM/relay/MQTT. sketch_jul27a es una prueba pequeña.

La evidencia de rutas, tamaños, huellas y selección está en `reports/kali-reference-inspection.json` y `kali-reference-comparison.json`. Es una lectura del disco de una VM encendida: cada sketch se leyó dos veces y se exigieron bytes iguales; no se afirma haber creado una imagen forense transaccional del sistema completo. API de lectura: [Dissect](https://docs.dissect.tools/en/stable/advanced/api.html).

## Organización observada en Arduino

Las referencias de línea siguientes corresponden al sketch original de Kali, no al de PastilleroBadi:

| Parte | Evidencia del sketch MQTT |
|---|---|
| Librerías | L1–9: Arduino, WiFi, PubSubClient, ArduinoJson, DHT, FirebaseESP32 y sus auxiliares externos. |
| Configuración visible | L11–35: bloques Wi-Fi, Firebase y MQTT, con constantes al principio. Sus valores privados no se reproducen. |
| Pines y variables | L37–121: LED23/LDR34/DHT14/relay27, PWM, objetos de librería, tiempos y variables globales agrupadas. Estos pines pertenecen a esa práctica. |
| Conexión | conectarWiFi L127; conectarMQTT L169; imprimen diagnóstico y usan esperas en bucles. |
| Actuadores | aplicarBrillo L218; leerControlesFirebase L241; PWM 0..255 y estado ON/OFF del relay. |
| Sensores | leerSensores L374: ADC del LDR, conversión/limitación de porcentaje, temperatura/humedad y detección de NaN. |
| Datos | publicarMQTT L518 serializa JSON; actualizarFirebase L664 escribe sensores y estados en rutas tipadas. |
| setup | L885: serie, pines, estado inicial seguro del relay, PWM/DHT, Wi-Fi, autenticación Firebase y MQTT. |
| loop | L1038: atiende conectividad y MQTT; consulta controles cada 500 ms y sensores/publicación cada 5000 ms mediante millis. |

Se adoptaron sus bloques con títulos, configuración al inicio, variables agrupadas y funciones descriptivas. PastilleroBadi conserva su tarea de red y máquina no bloqueante: los bucles de espera/delay de la práctica impedirían atender continuamente AccelStepper. Su contrato sigue en `devices/pastillero-01/v2` y la red del ESP32 mantiene HTTPS con raíces públicas y cuentas limitadas. MQTT de la práctica sirve como referencia de organización; el contrato solicitado del pastillero sigue siendo Firebase.

## Organización observada en Android Studio

Proyecto de referencia: `C:\Users\milit\AndroidStudioProjects\CRUDSQLITE1`.

| Archivo/clase | Evidencia real y correspondencia |
|---|---|
| MainActivity.java | Componentes y Firebase/Room/DataStore agrupados en secciones; onCreate L172; listener Firebase L417–729; eventos de botones L745–849. Usa findViewById y callbacks. |
| MainActivity: ciclo de vida | onStart L1067, onStop L1146, onDestroy L1587; retira listener/recursos según ciclo de vida. |
| RoomManager.java | L21–28 abre singleton/DAO/ejecutor; insertarRegistro L36 y obtenerHistorial L137 trabajan en executorService. |
| RegistroSensorDao.java | @Insert y @Query L50: SELECT de historial ordenado por timestamp DESC. |
| AppDatabase.java | Versión2, singleton getInstance L50, migración1→2 L29 añade estadoAlerta con DEFAULT; no usa migración destructiva. |
| res/layout/activity_main.xml | ScrollView/LinearLayout con sensores, controles PWM/relay, ajustes e historial; IDs coinciden con MainActivity. |

PastilleroBadi conserva Room4, entidades/DAO/migraciones, repositorios, Workers, autenticación y puente por origen. Se simplificó DashboardActivity.onCreate en solicitarPermisoNotificaciones, configurarContenidoLocal, registrarPuenteSeguro, observarDatosLocales y configurarBotonAtras. Son los mismos bloques, extraídos sin cambiar su orden. React/XML y efectos Glass permanecen. El SQL asíncrono y la separación de datos siguen el patrón del RoomManager de la práctica; las clases adicionales responden a permisos, colas y coordinación del sistema distribuido.

No se abrió una base de datos real de CRUDSQLITE1 ni se realizaron escrituras en su Firebase. No se copiaron sus credenciales al pastillero.

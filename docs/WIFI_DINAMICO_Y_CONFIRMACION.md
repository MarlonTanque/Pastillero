# Wi-Fi desde la app y confirmación de dosis

Desarrollo iniciado el 17 de noviembre de 2026; revisión de carga el 18 de noviembre. Raíz: `C:\Users\milit\AndroidStudioProjects\PastilleroBadi`.

## Uso por el cliente

Después de la instalación inicial de firmware, el cliente no tiene que abrir Arduino IDE, editar el sketch ni conocer los datos Firebase del ESP32 para cambiar de router.

1. Instalar la app 2.1-wifi-simulacion para revisar la interfaz. La configuración por radio requiere un teléfono Android real con Wi-Fi; el emulador muestra el formulario pero no sustituye la radio del teléfono.
2. En el firmware físico, con el pastillero en reposo, soltar el botón y mantenerlo pulsado ocho segundos. Abre una ventana local de cinco minutos y pausa el inicio de dosis. Si no hay ninguna red guardada, el servicio se abre al arrancar en reposo. En simulación no se leen GPIO: el técnico puede usar `w` por USB para abrir el servicio.
3. Abrir Ajustes → Configurar Wi-Fi del pastillero (en la vista clásica está en el menú). Introducir el nombre BADI_SETUP_XXXXXX y el código de 24 caracteres de la etiqueta del equipo.
4. Aceptar la conexión local que solicita Android. Esa red temporal puede mostrar «sin Internet»: es el enlace de configuración, no el router del usuario.
5. Buscar las redes desde el ESP32 o escribir un SSID oculto. Introducir personalmente la contraseña y pulsar Guardar y probar. La red debe ser compatible con el ESP32 clásico: 2.4 GHz; este flujo cubre redes personales y red abierta elegida explícitamente, no portales cautivos, 5 GHz exclusivo ni autenticación empresarial.
6. Esperar que el ESP32 confirme conexión. La app distingue datos enviados de red conectada. Después hay que comprobar telemetría reciente/PING para verificar también Internet y Firebase.

La etiqueta se prepara una sola vez por el técnico: `w` por la consola USB muestra nombre y código local, generado aleatoriamente en cada dispositivo y conservado en NVS. No es la contraseña del router, no debe publicarse en GitHub ni enviarse al chat. El cliente conserva esa etiqueta para las siguientes configuraciones; no necesita programar para usarla.

## Seguridad y recuperación

El ESP32 usa el gestor oficial Espressif, SoftAP WPA2 y protocomm Security1 con prueba de posesión. El nombre del AP contiene un sufijo de la MAC; el código de 96 bits aleatorios no es común a todos los equipos. La app usa el SDK oficial fijado a lib-2.4.4, adaptado para no registrar secretos y no degradar a Security0/no_pop. Ver third_party/esp-provisioning/README.md.

El SSID y la contraseña viajan desde una pantalla Java nativa: no pasan por React, Room ni Firebase. El puente solo transmite la acción vacía wifiSetup para abrir la pantalla. Los campos no se restauran tras recreación ni se entregan a autofill; la ventana protege las capturas. El código/contraseña permanecen temporalmente en RAM durante la sesión; no se promete borrado físico de todas las copias de String de Java.

El driver guarda la red en NVS. Antes del cambio se guarda un bloque de recuperación separado del historial de dosis. Solo se retira tras una conexión aceptada; al vencer la ventana sin éxito o reiniciar durante el cambio, se restaura la configuración anterior. Las pruebas de cortes de alimentación/NVS/radio reales siguen pendientes: la compilación y los dobles RAM no las sustituyen. NVS no equivale por sí sola a almacenamiento cifrado contra lectura física del chip; no se activaron secure boot ni flash encryption.

La tarea de red atiende el aprovisionamiento. No hay esperas de Wi-Fi en loop y no se inicia una dispensación mientras está activa la configuración. Una dosis en movimiento o esperando confirmación impide abrir el cambio de red. La pulsación que confirmó una toma debe soltarse antes de que pueda comenzar una pulsación larga nueva.

WIFI_SSID y WIFI_PASSWORD siguen declaradas por compatibilidad con el generador privado anterior, pero **ya no se usan para conectar**: no es necesario rellenarlas. WiFi.begin() recupera la configuración del driver. Firebase mantiene su cuenta ordinaria de dispositivo, URL y TLS; esos datos no se exponen al formulario Wi-Fi del cliente.

## Botón, buzzer y pantalla

Durante la espera de recogida se activa el LED de espera y el patrón de buzzer. Tras el retorno a cero, una pulsación nueva en GPIO27 confirma la dosis: el controlador vuelve a reposo, se apagan el buzzer y los LED de aviso y se registra CONFIRMED una sola vez. Mantener el botón pulsado desde antes no confirma una toma. La confirmación significa que el usuario pulsó el botón; no demuestra ingestión.

El LCD muestra «Toma tu pastilla» al esperar; tras la confirmación muestra «Toma confirmada / Aviso apagado» durante aproximadamente cinco segundos y luego vuelve a espera. Si empieza otra entrega, su estado tiene prioridad. Reconocer una alerta de omisión/fallo no la transforma en una toma confirmada.

## Conexiones físicas previstas

Todo se cablea sin alimentación. GPIO son las etiquetas del ESP32, no la posición ordinal del conector.

| Componente | Conexión y condición |
|---|---|
| Pulsador de confirmación | Un contacto a GPIO27 y el otro a GND. INPUT_PULLUP interno, activo en LOW. En pulsadores de cuatro patas identificar las dos parejas por continuidad; no unir dos patas ya conectadas internamente. |
| LED de espera | GPIO18 → resistencia 330 Ω → ánodo LED; cátodo → GND. Se apaga al confirmar. |
| LED de alerta | GPIO19 → resistencia 330 Ω → ánodo LED; cátodo → GND. Señala alerta/fallo. |
| Buzzer | GPIO14 es la señal. El patrón actual requiere buzzer activo o módulo con entrada compatible de 3.3 V. Usar etapa de control si consume más que un GPIO; no conectar una carga de 5 V directamente al pin. Si es pasivo necesita generación de tono adicional, todavía no implementada. |
| Servo de compuerta | Señal GPIO13; positivo a fuente externa de la tensión indicada por su modelo; negativo a GND de esa fuente y GND lógico del ESP32. Calibrar extremos previstos 1000/2000 μs sin forzar la tablita. No alimentar desde 3V3 ni GPIO. El cierre y retorno aún requieren validar los tiempos mecánicos reales. |
| LCD 16x2 I2C compatible | SDA21 y SCL22, GND común y VCC según módulo. Si trabaja a 5 V, adaptar SDA/SCL con conversor bidireccional 3.3↔5 V. El firmware espera PCF8574 0x27 y mapa específico de pines. |
| NEMA17/TB6600 | PUL25/DIR26 mediante la interfaz eléctrica adecuada al módulo; alimentación de potencia independiente y microstepping acordado. Conservar cuatro dosis y cero vacío. No se accionó en esta revisión. |
| Sensores | GPIO34 para presencia analógica, máximo 3.3 V y umbral a medir; GPIO35 para salida activa LOW con polarización externa. Son funciones distintas. |
| Bomba opcional | GPIO23 solo señal a su etapa de potencia, no alimentación de la bomba desde GPIO. |

La pantalla llamada WPHX-8 no se ha identificado por foto/manual. La fila de LCD **solo aplica si realmente es un LCD16x2 con adaptador PCF8574**; no se afirma que WPHX-8 lo sea. Es necesario identificar sus terminales y el modelo de buzzer/servo antes de cerrar el esquema de alimentación.

La fuente conserva DRY_RUN=1 y las disponibilidades de servo/LCD/salida/bomba en 0. Por ello, la carga actual de simulación no produce pulsos ni lee el botón físico. Después de validar el cableado se requiere una fase física autorizada para habilitar los periféricos correctos y probar con material inerte, nunca medicamentos reales.

## Carga y particiones: corrección necesaria

La tabla existente reserva NVS en 0x9000..0x49000, OTA en 0x49000 y app0 en 0x50000. La receta estándar de Arduino usada inicialmente escribió aplicación en 0x10000 y OTA en 0xe000; aunque la verificación de bytes aprobó, esas direcciones no corresponden a esta tabla y alcanzaron parte del rango NVS. **No usar el botón Cargar/receta estándar con esta tabla sin corregir los offsets.**

Se guardó un respaldo local de la zona NVS después de ese primer intento. El prefijo 0x9000..0xe000 conserva páginas NVS válidas; no se había creado un respaldo de toda la memoria anterior a la primera carga, por lo que no se declara preservación completa de datos previos del ESP32. Room Android no fue borrado. La lectura completa de flash falló por ruido serie; el respaldo acotado de NVS sí completó a 115200 baudios.

El nuevo tools/upload_simulation.py extrae los offsets del binario de particiones, impide escrituras sobre NVS, rechaza DRY_RUN=0 y respalda tabla/NVS antes de futuras cargas. Sin --execute solo comprueba archivos. Ejemplo de carga futura, con actuadores sin alimentación y puerto comprobado: `python tools/upload_simulation.py --port COM5 --execute`. Si la tabla instalada difiere, se detiene para no improvisar una migración.

El resultado real de la recuperación/carga y del arranque se registra en docs/RESULTADOS.md y reports/wifi-upload-recovery.json; no se deduce éxito de arranque por haber escrito un binario. Durante la corrección hubo pérdida de detección USB y se pidió cambiar cable/puerto; hasta verificar el arranque no debe usarse el montaje.

Actualización del 18 de noviembre: la carga corregida y su verificación terminaron, y el firmware respondió por USB con su identidad local. Ver RESULTADOS.md y reports/wifi-retry-upload-20261118.json. El intercambio de red por radio y las pruebas de actuadores siguen pendientes; la imagen cargada permanece en simulación.

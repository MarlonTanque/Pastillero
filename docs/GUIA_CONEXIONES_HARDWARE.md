# Guía de conexiones de hardware

## Estado y alcance

Esta guía documenta el montaje previsto por el código. **No se cargó firmware ni se movió el motor.** La variante predeterminada es simulación. La tabla de pines es verificable en la sección4 de `PastilleroESP32.ino`; las condiciones eléctricas concretas dependen de la placa DOIT/ESP32 real, del módulo comercial TB6600, del sensor y de la ficha del motor disponibles. No se ha identificado una fotografía/manual de cada pieza instalada ni se ha medido su cableado.

Compilar la variante física no habilita un dispositivo conectado: solo produce un archivo binario. Mantener `PASTILLERO_DRY_RUN=1` en la fuente. El modelo sin GPIO usado en pruebas C++ tampoco configura pines.

## 1. Función de cada componente

| Componente | Trabajo |
|---|---|
| ESP32 | Decide horarios/estados, lee botón/sensor y genera señales de control |
| TB6600 comercial | Recibe paso/dirección y proporciona corriente a las dos bobinas |
| NEMA 17 | Gira el mecanismo; NEMA 17 indica tamaño mecánico, no la corriente nominal |
| Fuente del motor | Alimenta la etapa de potencia del driver según la ficha del conjunto |
| Botón | Registra una nueva pulsación de confirmación o reconocimiento de alerta |
| Sensor óptico | Informa presencia de blíster según umbral; no verifica ingestión de una pastilla |
| LED/avisador | Indican espera, alerta y fallo |

El ESP32 no alimenta las bobinas desde un GPIO. El TB6600HG de Toshiba es un circuito integrado; un módulo con borneras añade electrónica que puede variar. Sus límites y entradas no se deducen solo del nombre de la carcasa. [Referencia del fabricante del circuito](https://toshiba.semicon-storage.com/ap-en/semiconductor/product/motor-driver-ics/stepping-motor-driver-ics/detail.TB6600HG.html).

## 2. Tabla exacta de señales del firmware

| Nombre | GPIO | Conexión prevista/condición |
|---|---:|---|
| PIN_PUL | 25 | Entrada de una interfaz de nivel que controle PUL del driver |
| PIN_DIR | 26 | Entrada de una interfaz de nivel que controle DIR del driver |
| PIN_BUTTON | 27 | Pulsador entre GPIO y GND lógico; INPUT_PULLUP, activo en LOW |
| PIN_OPTICAL | 34 | Salida analógica adaptada a niveles seguros del ESP32 |
| PIN_BUZZER | 14 | Señal a avisador compatible o a su transistor/driver |
| PIN_READY | 18 | LED de espera mediante resistencia limitadora |
| PIN_ALERT | 19 | LED de alerta mediante resistencia limitadora |

GPIO no es el número de posición física del conector. Confirmar la serigrafía de la placa. En ESP32 clásico GPIO34 es de entrada y no dispone de pull-up/pull-down interno; el sensor debe proporcionar una señal definida. No aplicar una salida de 5 V directamente al GPIO. [Guía de hardware de Espressif](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/schematic-checklist.html).

No hay un GPIO de habilitación ENA configurado en el firmware. No asumir que ENA del módulo queda en el nivel correcto sin consultar su manual. Tampoco hay final de carrera o encoder de cero en esta versión.

## 3. Alimentación y niveles

Separar alimentación lógica del ESP32 y potencia del motor. Seleccionar tensión/corriente de la fuente por la ficha del motor y módulo, con protección y conexiones adecuadas; esta guía no fija valores desconocidos. La corriente del driver debe corresponder a la corriente por fase del NEMA 17 y a la forma en que el módulo expresa RMS/pico.

El ESP32 trabaja con lógica de 3.3 V. Algunos módulos etiquetados TB6600 requieren entradas optoacopladas de otra tensión/corriente. Por eso **no se da por probado el enlace directo GPIO → bornera**. Debe verificarse el manual del módulo exacto y utilizar una interfaz de nivel/driver de entrada compatible.

Ejemplo conceptual de interfaz colector abierto, únicamente si el manual del módulo admite esa configuración:

```text
GPIO25 -> resistencia calculada -> base de Q1
emisor Q1 -> GND lógico
colector Q1 -> PUL-
alimentación lógica de la entrada -> PUL+

GPIO26 -> resistencia calculada -> base de Q2
emisor Q2 -> GND lógico
colector Q2 -> DIR-
alimentación lógica de la entrada -> DIR+
```

Este esquema no es el cableado certificado del equipo: faltan modelo del transistor, corriente requerida por el optoacoplador, resistencias y polaridad del módulo real. La alimentación de la entrada no se conecta a un GPIO. La masa común de la etapa lógica y el aislamiento respecto a la potencia dependen de la interfaz elegida; no unir a ciegas las masas de un montaje que se pretende aislado.

Se conservaron `setPinsInverted(true,true)` del sketch original y pulso mínimo de diez microsegundos. Una interfaz adicional puede invertir la señal físicamente: comprobar flanco activo/dirección antes de pruebas de giro. No se cambia esta configuración sin documentar el montaje.

## 4. Bobinas y microstepping

Con todo desenergizado, identificar las dos parejas de bobina del motor siguiendo su ficha o medición adecuada. Una pareja se conecta a A+/A- y la otra a B+/B- de la etapa de potencia. Los colores no son universales. No conectar/desconectar bobinas con el driver energizado.

El proyecto conserva 3200 pasos por vuelta como valor configurable. La relación general es:

```text
pasos_por_vuelta = pasos_completos_del_motor × factor_de_microstepping
pasos_por_compartimento = pasos_por_vuelta / posiciones_totales
V2: 3200 / 5 = 640
```

Ejemplo aritmético, condicionado al motor real: 200 pasos completos y factor 16 producen 3200 pulsos por vuelta. Eso no demuestra que los interruptores DIP estén así configurados. Se debe leer la tabla del módulo concreto. Cambiar microstepping requiere actualizar la constante y recalibrar.

| Posición | Destino por defecto | Función |
|---|---:|---|
| 0 | 0 pasos | Cero vacío/punto de retorno; no contiene pastillas |
| 1 | 640 pasos | Primer compartimento de dosis |
| 2 | 1280 pasos | Segundo compartimento de dosis |
| 3 | 1920 pasos | Tercer compartimento de dosis |
| 4 | 2560 pasos | Cuarto compartimento de dosis |

Se conserva el patrón de ida y retorno del original y se amplía al montaje confirmado de cinco espacios: **640→0, 1280→0, 1920→0, 2560→0**. El perfil histórico de cuatro posiciones sigue disponible como compatibilidad y requiere recalibración al cambiarlo. Hay dos segundos de espera de entrega y quince segundos entre posiciones manuales. Los horarios programados eligen un compartimento concreto y esperan confirmación: no convierten automáticamente cada dosis en la secuencia manual completa.

## 5. Botón y sensor

El pulsador conecta GPIO27 a GND al presionarse. La resistencia interna mantiene HIGH cuando está suelto. El filtrado exige cuarenta milisegundos estables. Tras regresar al cero, el controlador exige soltar y pulsar nuevamente: mantener presionado el botón desde antes no confirma una toma por accidente.

El sensor llega a GPIO34 con nivel compatible. El código compara `analogRead()` con 1800; no son 1800 voltios ni una distancia física. Se debe medir lectura con/sin blíster, comprobar polaridad y documentar el umbral elegido. En simulación se devuelve presencia verdadera y botón falso, sin leer GPIO.

Un aviso bloqueado no se convierte en confirmación por pulsar reconocimiento. La alerta se reconoce para revisar el estado; el historial conserva su tipo real. Un blíster presente no demuestra que salió una pastilla ni que una persona la tomó.

## 6. Indicadores

PIN_READY se activa durante Awaiting. PIN_ALERT se activa en Alert/Fault. El avisador usa un patrón calculado con `ms % 1000 < 100`: una ventana de cien milisegundos por segundo, sin delay(). Una carga que exceda la capacidad del GPIO requiere etapa de control; los LED requieren resistencia. Confirmar si el avisador es activo/pasivo antes de atribuirle un tono que el firmware no genera.

## 7. Calibración y retorno

| Comando | Efecto previsto |
|---|---|
| `a` | Ajustar +10 pasos antes de confirmar calibración |
| `r` | Ajustar -10 pasos antes de confirmar calibración |
| `c` | Declarar que la posición alineada actual es cero |
| `s` | Iniciar secuencia manual solo con calibración y controlador libre |

`c` no busca un final de carrera: fija una referencia lógica donde se alineó el mecanismo. El retorno a cero usa el contador de pasos de AccelStepper. Un atasco, pérdida de pasos o corte de energía exige revisión y nueva calibración; esta versión no tiene homing automático o realimentación de posición. `moveTo()` selecciona el objetivo y `run()` avanza progresivamente sin bloquear. [API de AccelStepper](https://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html).

## 8. Protocolo físico futuro, aún no ejecutado

1. Revisar manuales, alimentación, bobinas, corriente, microstepping, interfaz de nivel y pinout. Documentar cada pieza.
2. Comenzar con mecanismo vacío/material de prueba y sin medicamentos reales. Obtener autorización de la fase física antes de energizar o cargar firmware.
3. Comprobar niveles/pulsos y dirección de forma controlada, con acceso a la desconexión de potencia.
4. Validar a/r/c y después la secuencia s, retorno al cero y pausas, con resguardo de partes móviles.
5. Probar botón mantenido, liberación/nueva pulsación, sensor sin blíster y reconocimiento de alerta.
6. Probar un horario de ensayo, omisión de cinco minutos, caída real de Wi-Fi y reinicio durante una reserva.
7. Confirmar que no se repite la dosis y que el modo de prueba queda marcado como simulación en el historial.

El informe diferencia lo compilado, lo ejecutado en PC/emulador y estas pruebas pendientes. No se publican resultados físicos inferidos a partir de una compilación.

## 9. Periféricos V2 preparados, pendientes de montaje real

| Señal | GPIO/dato | Implementación y condición física pendiente |
|---|---|---|
| LCD SDA / SCL | 21 / 22 | Wire, PCF8574 0x27, dos líneas de 16 caracteres; verificar dirección y mapa RS0/RW1/E2/BL3/D4..7 |
| Sensor de salida | 35 | Entrada activa LOW, sin pull-up interno; polarización externa a 3.3 V, filtro 10 ms y flanco nuevo |
| Servo | 13 | PWM 50 Hz/16 bits; pulsos previstos 1000/2000 μs, verificar recorrido/corriente y topes reales |
| Bomba opcional | 23 | Señal al driver de potencia, duración 500..5000 ms; no alimentar la bomba desde GPIO |

Las cuatro macros PASTILLERO_LCD_AVAILABLE, PASTILLERO_EXIT_AVAILABLE, PASTILLERO_SERVO_AVAILABLE y PASTILLERO_PUMP_AVAILABLE valen 0. Además, PASTILLERO_DRY_RUN=1 impide accesos físicos. Una casilla Android no elimina estos bloqueos. La compilación de la variante física se hizo sin cargarla y con periféricos nuevos deshabilitados.

El sensor de presencia de GPIO34 y el sensor de salida de GPIO35 son funciones distintas. El segundo exige un flanco durante la entrega; inicialmente bloqueado no cuenta como salida. NO_EXIT impide confirmar la entrega como tomada. Ninguno verifica ingestión. Un montaje que habilite exigencia de sensor sin disponibilidad local no puede demostrarse mediante simulación de GPIO; la validación física debe revisar ambos ajustes.

El servo y la bomba necesitan alimentación adecuada, etapa de potencia/protección según sus fichas y una referencia lógica diseñada correctamente. Para el LCD, verificar tensión del backpack y usar adaptación bidireccional de nivel si sus pull-ups van a 5 V. No aplicar ese nivel al ESP32. La tarea LCD escribe aparte de loop; esto se compiló pero no se ha medido sobre hardware. [PCF8574, TI](https://www.ti.com/lit/ds/symlink/pcf8574.pdf).

Pruebas posteriores autorizadas: medir señales sin motor, validar entrada/salida y pantalla, calibrar con mecanismo vacío, probar un compartimento y retorno, después los cuatro en orden, omisión de cinco minutos y recuperación tras corte. Activar cada periférico por separado tras comprobar su montaje; usar material inerte, nunca medicamentos reales.


Revisión del 22 de octubre de 2026: la configuración y los certificados están dentro del .ino; los datos locales se materializan mediante generate_private_firmware.py. La carpeta del sketch contiene solo .ino y partitions.csv. Referencia elegida, procedimiento privado y evidencia: COMPARACION_CRUDSQLITE1.md y UNIFICACION_FIRMWARE.md.

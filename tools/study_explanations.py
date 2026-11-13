"""Vocabulario de estudio: explica instrucciones sin leer valores privados en los informes."""
import re
from study_notes import note_for
import study_v2

FILES = {
    'PastilleroESP32.ino': 'coordina la dosis, el motor simulado/físico, la memoria NVS y la comunicación segura del ESP32',
    'MainActivity.java': 'presenta la interfaz XML, escucha botones y observa datos sin ejecutar SQL en el hilo de pantalla',
    'Repository.java': 'conecta los permisos Firebase, los listeners y el almacenamiento Room de cada responsable',
    'PastilleroApp.java': 'inicializa Firebase y el canal de notificaciones al crear el proceso Android',
    'PastilleroDatabase.java': 'construye la base SQLite mediante Room y conserva datos al migrar de versión',
    'PastilleroDao.java': 'define consultas parametrizadas y operaciones SQL que Room implementa durante la compilación',
    'DoseEvent.java': 'representa una fila de historial, con horas programada/real y marca de simulación',
    'PlanDraft.java': 'representa el borrador local y su versión, incluso sin conexión',
    'CommandRequest.java': 'representa una solicitud persistente que se reintenta con el mismo identificador',
    'PlanCodec.java': 'valida horarios y transforma JSON en los tipos que Firebase puede almacenar',
    'SyncWorker.java': 'publica un borrador Room mediante una transacción Firebase desde un trabajo en segundo plano',
    'CommandWorker.java': 'envía solicitudes guardadas en Room, detecta duplicados y conserva el resultado',
    'Alerts.java': 'emite avisos locales de omisión, bloqueo o recuperación, cuando la aplicación recibe el evento',
    'Labels.java': 'traduce estados y eventos del contrato a mensajes comprensibles',
    'PlanCodecTest.java': 'comprueba validación, límites, separación de dosis y exclusión de simulaciones del conteo real',
    'RoomOfflineTest.java': 'comprueba reapertura, aislamiento, duplicados y migraciones con bases temporales del emulador',
    'FirebaseConnectionTest.java': 'comprueba los SDK Android contra Firebase real solo con credenciales privadas suministradas al ejecutar',
    'controller_test.cpp': 'prueba en PC el mismo controlador del .ino mediante un motor y almacenamiento ficticios',
    'command_bridge.cpp': 'expone el validador C++ a las pruebas Firebase sin conectar un ESP32',
    'activity_main.xml': 'declara los controles de la pantalla que MainActivity enlaza mediante R.id',
    'AndroidManifest.xml': 'declara permisos, aplicación, pantalla inicial y restricciones de respaldo/transporte',
    'strings.xml': 'centraliza los textos traducibles y los argumentos que se insertan al mostrar resultados',
    'styles.xml': 'configura el tema visual de Android sin cambiar la lógica de las dosis',
    'ic_pastillero.xml': 'dibuja el icono vectorial empaquetado en el APK',
    'backup_rules.xml': 'excluye datos locales del respaldo automático anterior a Android 12',
    'data_extraction_rules.xml': 'excluye datos de la nube y transferencia entre dispositivos en versiones nuevas de Android',
    'build.gradle': 'configura compilación, dependencias, Firebase público y generación de constantes para el APK',
    'settings.gradle': 'define el módulo app y los repositorios de complementos/dependencias',
    'database.rules.json': 'autoriza operaciones por UID vinculado, cuenta habilitada, vigencia de sesión y forma de los datos',
    'rules.test.mjs': 'comprueba autorizaciones y rechazos usando exclusivamente Firebase Emulator',
    'access-service.mjs': 'aplica autorización administrativa, bloqueo de cuentas, revocación y auditoría en el servidor',
    'access-service.test.mjs': 'prueba el servicio administrativo con dobles de Authentication y Realtime Database',
    'server.mjs': 'adapta las rutas HTTP locales al SDK Admin sin distribuir autoridad administrativa a los clientes',
    'bootstrap-admin.mjs': 'prepara deliberadamente un administrador independiente; no se ejecuta durante las pruebas ordinarias',
    'PastilleroOriginal.ino': 'conserva el sketch de referencia; contiene movimientos bloqueantes históricos y no se ejecuta',
}

TERMS = {
    'PIN_PUL': 'GPIO 25: señal de pasos hacia la interfaz del TB6600',
    'PIN_DIR': 'GPIO 26: dirección del giro, conservada respecto al sketch original',
    'PIN_BUTTON': 'GPIO 27: botón de confirmación activo en nivel bajo y con resistencia interna de elevación',
    'PIN_OPTICAL': 'GPIO 34: entrada analógica del sensor; solo entrada y sin resistencias internas',
    'PIN_BUZZER': 'GPIO 14: señal del avisador, con etapa de potencia si el componente la requiere',
    'PIN_READY': 'GPIO 18: indicador de espera de confirmación física',
    'PIN_ALERT': 'GPIO 19: indicador de alerta o fallo',
    'OPTICAL_THRESHOLD': 'umbral analógico 1800; su valor y polaridad requieren calibración real del sensor',
    'PASTILLERO_DRY_RUN': '1 selecciona simulación sin pulsos ni lectura física; 0 solo se usa para compilar la variante física',
    'PASTILLERO_HOST_TEST': 'excluye Arduino y GPIO al incluir el modelo en una prueba de PC',
    'PASTILLERO_DOMAIN_DEFINED': 'impide definir dos veces el controlador cuando dos cabeceras incluyen el .ino',
    'PASTILLERO_STEPS_PER_TURN': '3200 pasos/vuelta por defecto; debe coincidir con el microstepping configurado y ser divisible entre cuatro y cinco',
    'STEPS_PER_TURN': 'cantidad de pasos para una vuelta completa',
    'STEPS_PER_SLOT': 'paso del perfil histórico de cuatro posiciones; V2 usa STEPS_PER_TURN / positions, 640 con cinco espacios',
    'DROP_MS': 'espera de entrega de 2000 milisegundos, sin detener loop()',
    'INTERVAL_MS': 'pausa manual de 15000 milisegundos entre compartimentos',
    'OMIT_MS': 'límite de 300000 milisegundos, cinco minutos desde la hora programada',
    'WIFI_SSID': 'nombre privado de la red Wi-Fi de 2.4 GHz',
    'WIFI_PASSWORD': 'contraseña privada de esa red; no se imprime ni se documenta su valor',
    'FIREBASE_API_KEY': 'identificador de configuración pública de Firebase, no una clave de administrador; su valor se oculta aquí',
    'FIREBASE_DATABASE_URL': 'URL HTTPS completa del proyecto dedicado, visible en la sección Firebase del sketch',
    'DEVICE_EMAIL': 'identificador de la cuenta Firebase exclusiva del dispositivo',
    'DEVICE_PASSWORD': 'contraseña privada de la cuenta del dispositivo, nunca del administrador',
    'DEVICE_ID': 'identificador estable del pastillero usado para construir su ruta de base',
    'GOOGLE_ROOTS': 'cadena de certificados raíz públicos de confianza almacenada en flash',
    'Dose': 'estructura con identificador, fecha UTC de ejecución y compartimento',
    'State': 'enumeración cuyo orden numérico se comparte con los textos de estado de Android',
    'Idle': 'estado 0: reposo, disponible para elegir la siguiente dosis vencida',
    'Outward': 'estado 1: desplazamiento hacia el compartimento seleccionado',
    'Drop': 'estado 2: espera no bloqueante de dos segundos para la entrega',
    'Returning': 'estado 3: regreso al cero mecánico previamente calibrado',
    'Awaiting': 'estado 4: espera una pulsación nueva, posterior al regreso',
    'Alert': 'estado 5: requiere revisión y reconocimiento físico; no cuenta como confirmación de toma',
    'ManualGap': 'estado 6: pausa de quince segundos de la secuencia manual',
    'Fault': 'estado 7: fallo seguro que impide nuevas entregas',
    'Port': 'interfaz que permite usar el mismo controlador con hardware o con un doble de prueba',
    'Controller': 'máquina de estados independiente de Wi-Fi y de las librerías Arduino',
    'AdaptadorMotor': 'implementación de la interfaz Port que conecta controlador, motor y registro NVS',
    'dispositivo': 'adaptador real o simulado que implementa movimientos y registro durable',
    'controlador': 'instancia de la máquina de estados que se avanza una vez por iteración',
    'motor': 'objeto AccelStepper que genera pulsos graduales cuando se llama run()',
    'io': 'referencia al puerto de movimiento y persistencia recibido por el controlador',
    'memoriaPersistente': 'objeto Preferences que lee y escribe una instantánea JSON en NVS',
    'registroLocal': 'documento JSON en RAM con plan, identificadores consumidos y colas aún no confirmadas',
    'almacenamientoDisponible': 'bandera que cierra la entrega si la persistencia no garantiza recuperación',
    'mensajesEntrantes': 'cola FreeRTOS desde la tarea de red hacia el control principal',
    'mensajesSalientes': 'cola FreeRTOS desde el control hacia la tarea de red',
    'MensajeRed': 'estructura que transporta la dirección de un texto JSON reservado dinámicamente',
    'posicionSimulada': 'posición calculada sin enviar pulsos al motor',
    'ultimaTelemetria': 'instante local de la publicación de estado anterior',
    'sincronizacionSegura': 'permite escritura en flash y cambios de plan solo en estados sin movimiento',
    'active': 'dosis reservada; al reiniciar permite detectar una entrega interrumpida',
    'doses': 'lista de horarios individuales con identificadores estables',
    'count': 'número de dosis válidas cargadas, con capacidad máxima de 24',
    'state': 'fase de la máquina de estados o subárbol de telemetría según el contexto',
    'calibrated': 'indica que el usuario confirmó la referencia cero en esta ejecución',
    'slot': 'posición seleccionada: 1, 2 o 3; el cero es retorno y no una dosis',
    'manual': 'distingue la secuencia de calibración s de la programación por horarios',
    'released': 'recuerda que el botón se soltó para impedir que una pulsación mantenida confirme sola',
    'since': 'marca millis() del comienzo de la fase temporizada actual',
    'scheduledAt': 'hora UTC programada en milisegundos Unix',
    'actualAt': 'hora UTC registrada al suceder el evento, independiente de la programada',
    'compartment': 'número de compartimento de dosis permitido, entre 1 y 3',
    'simulation': 'marca explícita que separa pruebas de los registros físicos',
    'done': 'conjunto persistente de dosis consumidas; evita iniciar de nuevo un identificador',
    'events': 'eventos históricos pendientes o recibidos; no son órdenes de motor',
    'plan': 'plan versionado de horarios, compartido entre Android, Firebase y ESP32',
    'revision': 'número creciente del plan que detecta escritores desactualizados',
    'appliedRevision': 'revisión que el dispositivo realmente aceptó; no basta con que Android la haya enviado',
    'targetMode': 'destino simulation/hardware: impide mezclar horarios entre variantes',
    'commandRequests': 'solicitudes inmutables escritas por el responsable',
    'commandResults': 'respuestas separadas escritas por el dispositivo para cada modo',
    'token': 'en red ESP32 es una sesión efímera; en PlanDraft es un UUID de borrador, no una contraseña',
    'refresh': 'token de renovación de sesión solo en RAM; no se imprime',
    'refreshed': 'marca millis() de la última autenticación correcta',
    'attempt': 'último intento de sincronización con Firebase, separado cinco segundos',
    'wifiAttempt': 'marca del último intento de conexión Wi-Fi',
    'backoff': 'espera creciente de reconexión Wi-Fi, limitada a sesenta segundos',
    'epoch': 'hora absoluta UTC usada para comparar dosis de diferentes días',
    'ms': 'tiempo monotónico local de millis(), usado para esperas cortas',
    'JsonDocument': 'contenedor ArduinoJson; no se comparte directamente entre tareas',
    'JsonObject': 'objeto JSON de claves y valores modificable',
    'JsonObjectConst': 'vista de objeto JSON de solo lectura',
    'JsonVariantConst': 'vista de un valor JSON sin modificar el documento original',
    'JsonPair': 'par clave/valor recorrido dentro de un objeto JSON',
    'JsonPairConst': 'par clave/valor de solo lectura de un objeto JSON',
    'String': 'texto; en ESP32 es Arduino String y en Java es java.lang.String',
    'StringBuilder': 'acumulador de texto para mostrar historial sin concatenar toda la salida repetidamente',
    'long': 'entero de 64 bits en Java para fechas; en el ESP32 long es de 32 bits para posiciones',
    'int64_t': 'entero con signo de 64 bits para fechas UTC en firmware',
    'uint32_t': 'entero sin signo de 32 bits para restar marcas millis() incluso al desbordar',
    'bool': 'valor lógico C++ que solo representa verdadero o falso',
    'boolean': 'valor lógico Java para banderas como dirty y sent',
    'char': 'un carácter C++ o elemento de un identificador terminado en cero',
    'const': 'impide modificar el valor a través de esa declaración',
    'constexpr': 'constante que el compilador puede evaluar antes de ejecutar el programa',
    'static': 'duración persistente entre llamadas en variables locales o miembro de clase compartido en Java',
    'volatile': 'hace visible una bandera entre hilos; no convierte varias operaciones en una transacción',
    'virtual': 'selecciona el método del puerto concreto en tiempo de ejecución',
    'override': 'comprueba al compilar que el método implementa una operación heredada',
    'scope': 'separación local UID:deviceId: evita mezclar el historial de responsables o dispositivos',
    'uid': 'identificador de usuario Firebase; no es una contraseña',
    'dao': 'acceso a las consultas Room generadas durante la compilación',
    'context': 'contexto de aplicación para servicios y base, sin retener una Activity cerrada',
    'disk': 'ejecutor de un hilo para trabajo Room; evita bloquear la pantalla',
    'root': 'raíz JSON o referencia Firebase de trabajo; la ruta concreta se establece en cada método',
    'connected': 'referencia .info/connected del SDK; no acredita que el motor esté conectado',
    'access': 'referencia al registro de permisos propio en access/users/<uid>',
    'authorized': 'permite acciones remotas después de comprobar habilitación y vínculo como responsable',
    'accessAllowed': 'bandera del permiso habilitado recibido desde Firebase',
    'closed': 'evita procesar callbacks después de cerrar el repositorio',
    'lastState': 'última instantánea del ESP32 para representar fase y antigüedad',
    'timer': 'Handler de Android para actualizar el aviso de datos antiguos',
    'freshness': 'tarea periódica que vuelve a calcular la antigüedad del estado',
    'connection': 'LiveData con conexión, permisos y errores visibles en la pantalla',
    'deviceState': 'LiveData del estado leído del pastillero',
    'planListener': 'observador de cambios del plan; se retira al cerrar o perder acceso',
    'stateListener': 'observador del estado publicado por el dispositivo',
    'eventsListener': 'observador de cada evento de historial; inserta por clave única',
    'resultsListener': 'observador de respuestas de comandos para completar la cola Room',
    'accessListener': 'observador del permiso que permite reaccionar al bloqueo de la cuenta',
    'connectionListener': 'observador de la conexión del SDK con Firebase',
    'PastilleroDatabase': 'base Room versión 4 que envuelve SQLite y conserva migraciones',
    'PastilleroDao': 'contrato de inserción, consulta y actualización de las tres tablas',
    'DoseEvent': 'entidad del historial con clave compuesta scope/eventId',
    'PlanDraft': 'entidad del borrador con clave scope, revisión y UUID de reintento',
    'CommandRequest': 'entidad de solicitud con clave compuesta scope/commandId',
    'PlanCodec': 'validaciones de forma, ID, horas y separación antes de sincronizar un plan',
    'SyncWorker': 'trabajo persistente de publicación de planes que exige una red disponible',
    'CommandWorker': 'trabajo persistente que reintenta solicitudes conservando UUID y contenido',
    'FirebaseAuth': 'SDK que autentica cuentas y conserva/renueva la sesión de Android',
    'FirebaseDatabase': 'SDK que escucha y modifica Realtime Database de forma asíncrona',
    'DatabaseReference': 'dirección lógica de una ruta de Firebase, no una copia completa de la base',
    'DataSnapshot': 'instantánea inmutable de un valor recibido del servidor o caché del SDK',
    'MutableData': 'valor que Firebase ofrece al callback de una transacción y puede reintentar',
    'LiveData': 'dato observable ligado al ciclo de vida de la pantalla',
    'MutableLiveData': 'LiveData que el repositorio puede actualizar con postValue/setValue',
    'WorkManager': 'planificador Android que persiste trabajos y aplica restricciones de conectividad',
    'CountDownLatch': 'señal para esperar el callback en el hilo del Worker, nunca en el hilo de pantalla',
    'done': 'según el contexto: IDs persistentes del ESP32 o señal CountDownLatch de fin de transacción',
    'draft': 'borrador Room que puede quedar dirty hasta recibir acuse de Firebase',
    'dirty': 'marca que el borrador tiene cambios locales todavía no confirmados por el servidor',
    'baseRevision': 'versión remota sobre la que se editó el borrador; sirve para detectar conflictos',
    'sent': 'indica que la solicitud salió de la cola de envío; el resultado sigue en su campo separado',
    'commandId': 'UUID estable de la solicitud; un reintento conserva la misma clave',
    'eventId': 'clave estable del evento, compuesta por dosis, modo y tipo',
    'doseId': 'identificador estable de la dosis compartido por sus eventos',
    'json': 'carga serializada de un borrador o solicitud, almacenada como TEXT en SQLite',
    'resultJson': 'respuesta remota serializada, distinta de la solicitud original',
    'status': 'estado visible de sincronización o etiqueta de resultado, según el objeto',
    'createdAt': 'fecha de creación de la solicitud en milisegundos Unix',
    'requestedAt': 'fecha de creación del comando, validada frente al reloj del servidor',
    'expiresAt': 'caducidad del comando, no más de diez minutos después de requestedAt',
    'selectedAt': 'fecha y hora elegidas en la interfaz, convertidas a UTC al obtener los milisegundos',
    'ids': 'lista de UUID en el mismo orden que el selector de horarios a retirar',
    'dates': 'formateador que muestra fechas usando zona horaria y formato del teléfono',
    'history': 'TextView del historial local, que permanece disponible sin conexión',
    'chosen': 'TextView que muestra fecha elegida y zona horaria para evitar ambigüedad',
    'compartment': 'posición útil: V2 1..4 con cinco espacios; la vista clásica V1 conserva 1..3',
    'deleteChoice': 'selector que relaciona el horario mostrado con su UUID real',
    'draftState': 'texto de estado del borrador y su revisión base',
    'confirmed': 'contador que excluye eventos de simulación',
    'missed': 'contador de omisiones físicas, separado de las pruebas',
    'MIGRATION_1_2': 'agrega command_requests sin borrar historial ni borradores existentes',
    'MIGRATION_2_3': 'agrega targetMode con valor simulation a los borradores anteriores',
    'instance': 'instancia única y compartida de la base Room del proceso',
    'enabled': 'permiso revocable: ser usuario registrado no basta para acceder al dispositivo',
    'revokedAt': 'corte temporal de sesión en segundos Unix; impide reutilizar sesiones anteriores',
    'dashboardAdmin': 'custom claim emitido por un entorno administrativo, nunca por Android o ESP32',
    'protectedAdminUid': 'UID administrativo principal independiente, protegido contra el bloqueo por esta API',
    'expectedVersion': 'versión esperada del permiso, evita sustituir decisiones administrativas simultáneas',
    'ownerUid': 'UID del responsable autorizado para programar este dispositivo',
    'deviceUid': 'UID de la cuenta del ESP32 autorizada para escribir sus resultados y eventos',
    'BUILD_SUCCESSFUL': 'el compilador terminó sin errores; no acredita pruebas de hardware',
}

CALLS = {
    'setup': 'configura una sola vez periféricos, memoria y tarea de red al arrancar',
    'loop': 'cede de inmediato tras atender motor, mensajes, botón, estados e indicadores; se repite continuamente',
    'configurarMotorYSensores': 'prepara pines y AccelStepper únicamente en la variante física',
    'restaurarMemoriaPersistente': 'abre NVS, recupera el plan e identifica reinicios durante una entrega',
    'prepararColasYRed': 'crea las colas, prepara Wi-Fi/NTP y arranca la tarea Firebase en otro núcleo',
    'atenderCalibracionSerial': 'interpreta a/r/c/s sin bloquear: ajustar ±10, fijar cero o recorrer 1→0,2→0,3→0',
    'actualizarIndicadores': 'muestra espera/alerta con LED y pulsos temporizados del avisador en hardware',
    'enviarTelemetria': 'encola estado y pendientes cada dos segundos, con motor detenido',
    'obtenerHoraUtcMs': 'convierte segundos Unix del reloj sincronizado a milisegundos UTC',
    'guardarEstadoPersistente': 'serializa la instantánea y confirma la longitud escrita en NVS antes de permitir seguir',
    'encolarMensaje': 'duplica un texto y lo envía sin espera a FreeRTOS; libera memoria si la cola está llena',
    'validarPlanRecibido': 'comprueba modo, revisión, tipos, capacidad, separación e inmutabilidad del significado de cada ID',
    'procesarMensajesDeRed': 'aplica un mensaje de red, elimina pendientes solo tras acuse o guarda un resultado durable',
    'solicitudHttps': 'envía HTTPS con certificados raíz, tiempos límite y respuesta limitada a 48000 bytes',
    'mantenerSesionFirebase': 'inicia sesión o renueva tokens en la tarea de red, sin bloquear los pulsos de loop',
    'sincronizarConFirebase': 'lee plan/comandos recientes y publica resultados, eventos y telemetría de la última instantánea',
    'tareaFirebase': 'separa Wi-Fi, autenticación y HTTP del control temporal del motor',
    'leerBotonConfirmacion': 'entrega una lectura estable tras cuarenta milisegundos; en simulación devuelve false',
    'hayBlister': 'compara la lectura óptica con el umbral; en simulación devuelve true',
    'tick': 'avanza una fase según llegada, tiempo, hora y nueva pulsación; no usa esperas activas',
    'manualStart': 'inicia la secuencia manual solo estando libre y calibrado',
    'busy': 'indica si la fase es distinta del reposo y por tanto no admite nueva calibración/orden manual',
    'beginMove': 'fija la marca de tiempo, calcula compartimento × pasos por posición y entra en ida',
    'move': 'selecciona un destino; en hardware moveTo programa el movimiento, no lo completa de forma bloqueante',
    'reached': 'comprueba llegada; la simulación llega inmediatamente y el hardware usa distancia pendiente cero',
    'handled': 'consulta si el ID ya quedó reservado/consumido para impedir otra dispensación',
    'record': 'crea un evento, reserva el ID y exige confirmación de escritura persistente antes de continuar',
    'log': 'delega el registro al puerto; si falla pasa a Fault y detiene nuevas entregas',
    'validDose': 'valida longitud/caracteres del UUID, rango de fechas y compartimentos 1..3',
    'planModeMatches': 'compara el destino del plan con la variante compilada para no mezclar pruebas y hardware',
    'commandDecision': 'decide PING/APPLY_PLAN por modo, caducidad y revisión; no concede una orden de motor',
    'millis': 'lee tiempo monotónico desde el arranque; la resta sin signo resiste su desbordamiento',
    'time': 'lee segundos UTC del reloj que NTP sincroniza; no representa la zona horaria de presentación',
    'run': 'si corresponde genera el siguiente paso del motor y regresa rápidamente',
    'moveTo': 'fija una posición absoluta objetivo para futuras llamadas run()',
    'distanceToGo': 'resta posición actual a destino y permite saber si terminó el movimiento',
    'currentPosition': 'lee la posición lógica que AccelStepper lleva contando',
    'setCurrentPosition': 'declara cero en la posición alineada manualmente; no busca el cero por sí mismo',
    'setPinsInverted': 'conserva la inversión de señales del montaje original; debe comprobarse con su interfaz eléctrica',
    'setMinPulseWidth': 'fija diez microsegundos de ancho mínimo de pulso; no configura el microstepping del driver',
    'setMaxSpeed': 'fija límite de velocidad en pasos/segundo',
    'setAcceleration': 'fija aceleración en pasos/segundo al cuadrado',
    'enableOutputs': 'habilita/configura salidas solo en la variante física',
    'pinMode': 'configura entrada/salida digital; INPUT_PULLUP lleva el botón a alto cuando está suelto',
    'digitalRead': 'lee el nivel lógico de un pin configurado como entrada',
    'analogRead': 'lee el ADC del sensor; el umbral no equivale directamente a voltios',
    'digitalWrite': 'fija el nivel de un indicador; no debe alimentar directamente una carga de potencia',
    'configTime': 'inicia sincronización NTP en UTC con los servidores configurados',
    'xQueueCreate': 'reserva una cola FreeRTOS con capacidad y tamaño de elemento fijos',
    'xQueueSend': 'copia un mensaje a la cola; el cero final evita detener el hilo esperando espacio',
    'xQueueReceive': 'extrae un mensaje disponible sin esperar si el último argumento es cero',
    'xTaskCreatePinnedToCore': 'crea la tarea de red en el núcleo 0 y comprueba si pudo reservar sus recursos',
    'vTaskDelay': 'cede CPU en la tarea de red durante veinte milisegundos; no bloquea loop()',
    'pdMS_TO_TICKS': 'convierte milisegundos a unidades del planificador FreeRTOS',
    'serializeJson': 'convierte el documento a texto JSON para NVS o transporte',
    'deserializeJson': 'convierte texto a documento JSON y permite detectar datos inválidos',
    'overflowed': 'comprueba si ArduinoJson no pudo representar correctamente el documento',
    'putString': 'guarda el texto en NVS y devuelve la cantidad escrita, comprobada frente al tamaño esperado',
    'strdup': 'reserva una copia del texto cuya propiedad se transfiere al consumidor de la cola',
    'free': 'libera la copia recibida o el mensaje que no pudo encolarse; evita fuga de memoria',
    'strcmp': 'compara cadenas C; cero significa que los textos son iguales',
    'strlen': 'mide caracteres hasta el terminador cero de una cadena C',
    'strlcpy': 'copia texto limitando el tamaño del destino y conserva su terminación',
    'memcpy': 'copia las dosis ya validadas a la capacidad fija del controlador',
    'llabs': 'calcula una distancia temporal absoluta para rechazar horarios demasiado próximos',
    'isNull': 'comprueba si el campo JSON no tiene valor antes de leerlo o decidir un acuse',
    'setCACert': 'carga raíces públicas para verificar el servidor; no desactiva la comprobación TLS',
    'setHandshakeTimeout': 'limita el tiempo del establecimiento TLS en segundos',
    'setConnectTimeout': 'limita el establecimiento HTTP a cinco segundos en la tarea de red',
    'setTimeout': 'limita la espera de datos HTTP, separada del hilo de motor',
    'addHeader': 'declara el tipo de contenido que se envía al endpoint',
    'sendRequest': 'envía método y cuerpo HTTP y devuelve el código de respuesta',
    'writeToStream': 'vuelca el cuerpo HTTP al receptor de tamaño limitado, también con transferencia fragmentada',
    'getSize': 'consulta Content-Length cuando existe; el límite del receptor protege además respuestas fragmentadas',
    'concat': 'añade bytes al acumulador, indicando fallo si no pudo reservar memoria',
    'begin': 'inicia el recurso del objeto: su receptor distingue Serial, Preferences, Wi-Fi o HTTP',
    'onCreate': 'inicializa la Activity o Application una vez por creación; llama antes al comportamiento heredado',
    'onDestroy': 'libera listeners, temporizadores y ejecutor al destruir la pantalla',
    'onSaveInstanceState': 'conserva la selección de fecha ante recreaciones de pantalla',
    'setContentView': 'infla activity_main.xml para crear las vistas de la pantalla',
    'findViewById': 'obtiene una vista por su identificador XML R.id',
    'setOnClickListener': 'registra el callback que se ejecuta cuando la persona pulsa ese control',
    'observe': 'actualiza la pantalla cuando Room/LiveData entrega cambios y respeta el ciclo de vida',
    'setText': 'muestra texto en una vista; las cadenas con formato están centralizadas en resources',
    'getString': 'según receptor: obtiene recurso traducible, campo JSON, argumento Bundle o texto de NVS',
    'setAdapter': 'asocia los datos al Spinner y al formato de cada opción',
    'getSelectedItemPosition': 'devuelve el índice del selector; sumar uno convierte 0..2 en compartimento 1..3',
    'setOnApplyWindowInsetsListener': 'adapta márgenes internos a barras del sistema para no tapar controles',
    'showChosen': 'muestra la fecha elegida y su zona; informa si todavía no se seleccionó una',
    'showStatus': 'combina conexión, estado del dispositivo y situación del borrador',
    'showPlan': 'ordena horarios y mantiene la correspondencia entre texto visible y UUID a retirar',
    'chooseDate': 'abre selectores de fecha y hora y normaliza segundos/milisegundos',
    'login': 'lee campos, autentica de forma asíncrona y limpia la contraseña de la vista',
    'signInWithEmailAndPassword': 'solicita una sesión Firebase con los datos personales, sin ejecutar SQL ni mover el motor',
    'signOut': 'cierra la sesión del SDK; no elimina el historial Room',
    'getCurrentUser': 'comprueba si el SDK tiene una sesión antes de acceder al UID',
    'getUid': 'obtiene el identificador estable de esa cuenta autenticada',
    'getIdToken': 'solicita un token de sesión; true fuerza su renovación en la prueba',
    'recreate': 'reconstruye la Activity para que el repositorio use el nuevo UID o modo local',
    'requestPermissions': 'solicita permiso de notificaciones en Android 13 o posterior',
    'cloudReady': 'evita usar Firebase si falta configuración o corresponde a otro proyecto/base',
    'createChannel': 'crea el canal de notificaciones exigido por Android 8 o posterior',
    'createNotificationChannel': 'registra el canal de avisos de dosis con importancia alta',
    'notify': 'publica el aviso local con un identificador estable por cuenta/evento',
    'checkSelfPermission': 'comprueba si la persona concedió el permiso antes de notificar',
    'setPersistenceEnabled': 'activa la caché propia del SDK, distinta de las tablas Room del historial',
    'initializeApp': 'construye el cliente Firebase con el proyecto/base configurados, sin autoridad administrativa',
    'newSingleThreadExecutor': 'crea un ejecutor para serializar trabajo de disco fuera del hilo principal',
    'execute': 'programa una tarea en el ejecutor; no equivale a ejecutarla en el callback principal',
    'shutdown': 'deja de aceptar tareas nuevas y permite terminar las ya aceptadas',
    'getReference': 'construye una dirección Firebase; aún no ha descargado esa ruta',
    'child': 'desciende a una clave concreta del árbol JSON sin conceder permisos adicionales',
    'addValueEventListener': 'recibe la instantánea y futuras modificaciones de una ruta sin espera activa',
    'addChildEventListener': 'recibe eventos por hijo para insertar historial sin reemplazarlo todo',
    'removeEventListener': 'retira el observador concreto y evita callbacks de una pantalla cerrada',
    'onDataChange': 'recibe datos de servidor o caché y delega el trabajo de disco al ejecutor',
    'onCancelled': 'gestiona un rechazo del listener, por ejemplo falta de permisos',
    'onChildAdded': 'importa un evento recién observado; Room IGNORE evita duplicar su clave',
    'onChildChanged': 'vuelve a validar/importar un evento observado; no permite duplicar la fila',
    'onChildRemoved': 'no borra historial local ante una eliminación remota',
    'onChildMoved': 'no cambia el significado de eventos por su orden en la consulta',
    'getChildren': 'recorre los hijos presentes en la instantánea sin efectuar una consulta por cada uno',
    'getValue': 'convierte el valor recibido al tipo requerido; puede ser nulo si la ruta no existe',
    'getKey': 'obtiene el nombre del hijo usado como ID estable',
    'exists': 'distingue una ruta presente de un valor ausente',
    'setValue': 'solicita escribir el contenido en la ruta; el acuse es asíncrono y depende de las reglas',
    'runTransaction': 'compara y modifica el plan atómicamente; Firebase puede repetir su callback',
    'doTransaction': 'recalcula contra la revisión remota para evitar sobrescribir un plan más reciente',
    'onComplete': 'recibe el acuse de transacción y libera la espera del hilo Worker',
    'abort': 'cancela la transacción ante conflicto o ante un borrador que ya se había confirmado',
    'success': 'según receptor: acepta la transacción o marca el trabajo como completado',
    'retry': 'pide reintento con espera progresiva; no crea un nuevo UUID',
    'failure': 'marca un fallo que requiere corrección o recarga, en vez de repetir indefinidamente',
    'countDown': 'libera el Worker cuando llegó el resultado del callback',
    'await': 'espera con tiempo límite en Worker/prueba; no se utiliza para bloquear MainActivity',
    'enqueueUniqueWork': 'registra una cadena de trabajo identificada por cuenta y dispositivo',
    'setRequiredNetworkType': 'pospone el envío hasta que Android informe conectividad',
    'setBackoffCriteria': 'establece reintentos exponenciales desde treinta segundos',
    'cancelUniqueWork': 'cancela la cola remota de la cuenta bloqueada; conserva sus filas Room',
    'addOnSuccessListener': 'registra la acción que se ejecuta solo tras una lectura/escritura correcta',
    'addOnFailureListener': 'registra cómo informar un error sin cerrar la aplicación ni borrar datos',
    'addOnCompleteListener': 'recibe éxito/fallo de autenticación y permite limpiar el campo de contraseña',
    'postValue': 'publica una actualización observable de manera segura desde un hilo de trabajo',
    'postDelayed': 'vuelve a planificar la revisión de antigüedad sin una espera bloqueante',
    'removeCallbacks': 'retira el temporizador al bloquear o cerrar el repositorio',
    'startAuthorized': 'instala listeners solo después de verificar permisos y vínculo del responsable',
    'denyAccess': 'cierra autorización, retira listeners y cancela sincronización sin eliminar Room',
    'stopAuthorized': 'retira listeners y temporizador, manteniendo el observador de permisos para un posible restablecimiento',
    'renderState': 'traduce fase, calibración, modo y antigüedad del último estado',
    'ingest': 'convierte un evento remoto en entidad con scope y clave única antes de insertarlo',
    'importPlan': 'carga un plan remoto validado en Room; respeta un borrador local pendiente salvo recarga explícita',
    'reloadRemote': 'descarta el borrador solo tras la decisión explícita de recargar desde Firebase',
    'mutate': 'edita y valida el borrador en disco, guarda un UUID y deja su envío al Worker',
    'ping': 'guarda una comprobación PING; no puede arrancar el motor ni confirmar una toma',
    'insertEvent': 'inserta historial con IGNORE; devuelve -1 si la clave ya estaba guardada',
    'insertCommand': 'inserta una solicitud una sola vez mediante su clave compuesta',
    'saveDraft': 'guarda o reemplaza el borrador de este scope, conservando el resto de cuentas',
    'pendingCommands': 'consulta las solicitudes aún sin enviar ordenadas por creación',
    'observeEvents': 'observa hasta 500 filas más recientes sin borrar las demás',
    'observeDraft': 'observa el borrador de una sola cuenta/dispositivo',
    'observeCommands': 'observa las cincuenta solicitudes recientes conservando la tabla completa',
    'acknowledge': 'limpia dirty solo si coincide el token del borrador que se envió',
    'commandStatus': 'actualiza estado de envío solo mientras no exista un resultado final',
    'commandResult': 'guarda la respuesta separada y marca el comando como enviado',
    'databaseBuilder': 'prepara la base SQLite Room con contexto, clase y nombre de archivo',
    'addMigrations': 'registra rutas de actualización que conservan las tablas anteriores',
    'migrate': 'ejecuta únicamente el SQL de la transición de versión indicada',
    'execSQL': 'ejecuta una sentencia SQL de estructura o prueba; no se llama desde botones en el hilo principal',
    'doses': 'convierte y valida cada dosis JSON antes de construir el mapa Firebase',
    'confirmed': 'solo considera confirmación real cuando el tipo es CONFIRMED y simulation es falso',
    'delay': 'resta hora programada a hora registrada para comparar retraso; es un método Java, no delay() Arduino',
    'goOffline': 'desconecta deliberadamente el SDK en una prueba; no corta la radio Wi-Fi del equipo',
    'goOnline': 'restablece el SDK y entrega escrituras pendientes con su mismo identificador',
    'assertTrue': 'exige una condición verdadera; si no se cumple, la prueba falla',
    'assertFalse': 'exige una condición falsa y falla si se invierte el comportamiento esperado',
    'assertEquals': 'compara el resultado observado con el valor esperado por la prueba',
    'assertNull': 'comprueba que otra cuenta no obtuvo el borrador de este scope',
    'assert': 'en C++ comprueba una condición del controlador y detiene la prueba si falla',
    'assertFails': 'exige que el emulador Firebase rechace una operación prohibida',
    'assertSucceeds': 'exige que el emulador permita una operación válida',
    'verifyIdToken': 'verifica token administrativo y revocación en el backend confiable',
    'revokeRefreshTokens': 'invalida las sesiones renovables de la cuenta bloqueada desde el servidor',
    'setCustomUserClaims': 'emite privilegios solo desde el entorno administrativo autorizado',
    'applicationDefault': 'obtiene la identidad privilegiada del host sin empaquetar claves en los clientes',
    'changeAccess': 'aplica versión esperada, protección de administrador y bloqueo seguro antes de revocar sesiones',
    'authorize': 'exige UID principal y claim administrativo; una cuenta ordinaria recibe rechazo',
    'audit': 'registra actor, destino, hora, versión y etapa de un cambio administrativo',
    'getUser': 'consulta una cuenta desde Admin SDK antes de modificar su acceso',
    'updateUser': 'habilita o deshabilita Authentication sin pedir una contraseña al frontend',
    'transaction': 'actualiza un permiso solo si su versión todavía coincide con la esperada',
    'listUsers': 'pagina cuentas desde el backend y omite contraseñas, hashes y tokens en la respuesta',
    'readAccess': 'consulta metadatos de permisos desde el servidor confiable',
    'overview': 'comprueba autoridad antes de consultar todos los dispositivos',
    'readDevices': 'lee los dispositivos desde Admin SDK para la administración autorizada',
    'listen': 'abre la API únicamente en loopback; no despliega un servicio público',
    'read_text': 'lee un archivo local con la codificación indicada; los informes privados se redactan antes de publicar',
    'write_text': 'guarda un informe/configuración de texto; no cambia por sí mismo Firebase ni el motor',
    'read_bytes': 'lee bytes para comprobar integridad o empaquetar un artefacto',
    'sha256': 'calcula una huella para detectar cambios en archivos y entregables',
    'hexdigest': 'representa una huella binaria como caracteres hexadecimales',
    'copy2': 'copia conservando metadatos y permite mantener una entrega recuperable',
    'copytree': 'copia una carpeta completa para respaldo, sin mover el original',
    'check_output': 'ejecuta una herramienta local y recibe su salida; un código de error produce excepción',
    'rglob': 'recorre archivos bajo la carpeta indicada para inventario y comprobaciones',
    'glob': 'selecciona rutas que cumplen un patrón dentro del proyecto',
}

ATTRIBUTES = {
    'xmlns:android':'declara el prefijo android para atributos de la plataforma',
    'xmlns:tools':'declara el prefijo de herramientas; no altera el comportamiento instalado',
    'android:id':'crea/reutiliza el identificador que Java busca mediante R.id',
    'android:layout_width':'match_parent ocupa el ancho disponible; wrap_content usa el requerido por el contenido',
    'android:layout_height':'wrap_content ajusta contenido; match_parent ocupa el espacio disponible; dp fija tamaño independiente de densidad',
    'android:orientation':'ordena las vistas hijas verticalmente en este contenedor',
    'android:padding':'separa contenido de los cuatro bordes del contenedor en dp',
    'android:paddingTop':'añade espacio superior en dp sin modificar el contenido del control',
    'android:fillViewport':'permite que el contenido de ScrollView ocupe al menos la altura visible',
    'android:text':'elige un recurso string o texto que la vista muestra inicialmente',
    'android:textSize':'define el tamaño tipográfico en sp, que respeta la escala de accesibilidad',
    'android:textStyle':'aplica estilo tipográfico, como negrita, sin cambiar el dato mostrado',
    'android:hint':'muestra una ayuda cuando el campo está vacío; no guarda credenciales',
    'android:inputType':'textEmailAddress adapta el teclado; textPassword oculta visualmente la contraseña sin cifrar por sí solo',
    'android:importantForAutofill':'el valor literal «no» indica que el campo no participa en el rellenado automático; no incorpora una contraseña al APK',
    'android:accessibilityLiveRegion':'polite anuncia cambios a lectores de pantalla sin interrumpir una lectura activa',
    'android:textIsSelectable':'permite seleccionar/copiar texto de planes o historial',
    'android:name':'identifica permiso, clase, acción o categoría según la etiqueta XML contenedora',
    'android:label':'nombre visible de la aplicación obtenido de resources',
    'android:icon':'recurso vectorial que Android muestra como icono de la app',
    'android:allowBackup':'false impide respaldar automáticamente los datos de esta app',
    'android:fullBackupContent':'asocia exclusiones de respaldo para versiones anteriores a Android 12',
    'android:dataExtractionRules':'asocia exclusiones de respaldo y transferencia para Android 12 o posterior',
    'android:usesCleartextTraffic':'false prohíbe transporte HTTP sin cifrar en la app',
    'android:theme':'selecciona el tema AppTheme declarado en styles.xml',
    'android:supportsRtl':'permite adaptar la disposición a idiomas de derecha a izquierda',
    'android:exported':'true permite a Android abrir la Activity de inicio desde el lanzador',
    'android:windowSoftInputMode':'inicia el teclado oculto y redimensiona la pantalla cuando aparece',
    'android:width':'ancho intrínseco del vector en dp',
    'android:height':'alto intrínseco del vector en dp',
    'android:viewportWidth':'sistema horizontal de coordenadas internas del dibujo vectorial',
    'android:viewportHeight':'sistema vertical de coordenadas internas del dibujo vectorial',
    'android:fillColor':'color de relleno de la forma vectorial',
    'android:pathData':'instrucciones M/L/H/V/Z de la geometría del icono, no datos de una dosis',
    'tools:locale':'indica a las herramientas que los textos base están escritos en español',
    'name':'nombre con el que Java o XML referencia el recurso',
    'parent':'tema base del que se heredan los estilos',
    'domain':'tipo de almacenamiento excluido del respaldo, como base o preferencias',
    'path':'ruta dentro del dominio de respaldo; el punto representa todo ese dominio',
}

LIBRARIES = {
    'Arduino.h':'tipos y funciones básicos de Arduino, Serial, millis() y GPIO',
    'AccelStepper.h':'control de pasos con velocidad/aceleración sin movimientos bloqueantes',
    'WiFi.h':'conexión inalámbrica del ESP32 en modo estación',
    'WiFiClientSecure.h':'cliente TLS con validación de certificados raíz',
    'HTTPClient.h':'métodos HTTP usados para las API REST de Firebase',
    'Preferences.h':'almacenamiento persistente NVS para sobrevivir a un reinicio',
    'ArduinoJson.h':'serialización, lectura y comprobación de documentos JSON',
    'time.h':'reloj Unix sincronizado posteriormente mediante NTP',
    'stdint.h':'enteros de tamaño explícito para tiempos y fechas',
    'string.h':'copia, longitud y comparación de cadenas C de identificadores',
    'assert.h':'condiciones verificables de las pruebas C++',
    'stdio.h':'salida de resultados de las pruebas de consola',
}

OPERATORS = [('&&','Y lógico: deben cumplirse ambas condiciones'),('||','O lógico: basta una condición'),
    ('!==','distinto, también en tipo, en JavaScript'),('===','igualdad estricta de tipo/valor en reglas o JavaScript'),
    ('!=','distinto'),('==','igualdad, no asignación'),('>=','mayor o igual'),('<=','menor o igual'),
    ('++','incremento de una unidad'),('--','decremento de una unidad'),('+=','acumula sobre el valor anterior'),
    ('->','lambda/callback de Java o acceso mediante puntero en C++; el contexto distingue ambos'),
    ('?','selección condicional: condición ? alternativa verdadera : alternativa falsa'),
    ('%','resto de división; se usa en divisibilidad de pasos o en el patrón periódico del avisador')]

def components(line):
    parts=[]
    names=re.findall(r'\b[A-Za-z_]\w*\b',line)
    for name in dict.fromkeys(names):
        if name in TERMS: parts.append('`'+name+'`: '+TERMS[name])
    calls=re.findall(r'\b([A-Za-z_]\w*)\s*(?:<[^;{}]*?>)?\s*\(',line)
    for name in dict.fromkeys(calls):
        if name in CALLS: parts.append('`'+name+'()`: '+CALLS[name])
    for token,meaning in OPERATORS:
        if token in line: parts.append('`'+token+'`: '+meaning)
    if '1700000000000' in line: parts.append('1700000000000: límite mínimo de fecha que rechaza el reloj aún sin sincronizar')
    if '4102444800000' in line: parts.append('4102444800000: límite superior de fecha admitido por el contrato')
    for value,meaning in [('600000','diez minutos'),('300000','cinco minutos'),('48000','límite de 48000 bytes del documento/respuesta'),('16384','pila de 16 KiB para la tarea de red')]:
        if re.search(r'(?<![0-9])'+value+r'(?![0-9])',line): parts.append(value+': '+meaning)
    return parts

def sql_explain(code):
    parts=[]
    for token,meaning in [('SELECT','selecciona columnas sin modificar las filas'),('UPDATE','actualiza las filas seleccionadas'),('CREATE TABLE','crea la tabla si hace falta'),('ALTER TABLE','amplía la estructura conservando filas'),('ADD COLUMN','añade la columna indicada'),('INSERT INTO','inserta una fila temporal de prueba'),('WHERE','limita la operación a las filas que cumplen la condición'),('ORDER BY','establece un orden determinista'),('DESC','ordena de más reciente/mayor a menor'),('LIMIT','limita las filas mostradas, no borra las restantes'),('PRIMARY KEY','garantiza unicidad del identificador o pareja de identificadores'),('NOT NULL','impide un valor SQL NULL'),('DEFAULT','rellena la columna nueva de las filas previas'),('SET','indica qué columnas cambian')]:
        if token in code: parts.append(token+': '+meaning)
    params=re.findall(r'(?<!:):([A-Za-z_]\w*)',code)
    if params: parts.append('Parámetros '+', '.join(':'+x for x in dict.fromkeys(params))+': Room enlaza valores separados del SQL, evitando concatenar entradas de la persona')
    if 'scope' in code: parts.append('scope conserva separación por responsable y dispositivo')
    if 'token' in code and 'WHERE' in code: parts.append('La comparación del token impide confirmar o alterar un borrador más reciente')
    if "resultJson=''" in code: parts.append('No modifica el estado de un comando que ya tiene respuesta definitiva')
    return '; '.join(parts)+'.'

def explain(code,filename,context=''):
    s=code.strip();parts=components(s)
    web_note=study_v2.explain_web(s,filename)
    if web_note:return web_note,parts
    if s.startswith('template <typename '):
        return 'Declara un parámetro de tipo de la función plantilla: el documento o almacén concreto se determina al instanciarla. Así firmware y pruebas de PC comparten las mismas operaciones sin exigir Arduino en el modelo.',parts
    if filename=='rules.test.mjs' and s.startswith('regimens:'):
        return 'Prepara una pauta ficticia de prueba V2 con identidad med-a, hora diaria 08:00 UTC, compartimento 4 e intervalo auxiliar; los valores solo se escriben al emulador de reglas.',parts
    if filename=='rules.test.mjs' and s.startswith('doses:'):
        return 'Prepara la ocurrencia ficticia enlazada a med-a, con fecha t y compartimento 4, y cierra el constructor de programa de prueba; permite comprobar el contrato de cinco espacios.',parts
    reviewed=note_for(filename,s)
    if reviewed:return reviewed,parts
    if re.fullmatch(r'[A-Za-z_]\w*(?:\+\+|--);',s):
        name=s[:-3];operation='incrementa' if '++' in s else 'decrementa'
        return 'Contador: '+operation+' `'+name+'` en una unidad. '+TERMS.get(name,'Acumula el resultado del recorrido o pasa a la siguiente posición del proceso')+'.',parts
    special={
        'const String& contentType) {':'Completa la firma de solicitudHttps: recibe el tipo de contenido mediante referencia const para no copiarlo. Su valor predeterminado application/json está solo en el prototipo; esta línea abre el cuerpo.',
        "r'\\1\"VALOR\"\\2', text)":'Completa la sustitución de la prueba: conserva los grupos 1 y 2 de cada declaración y normaliza su literal a VALOR. Permite comparar que ninguna otra instrucción cambió al generar la copia.',
        'while depth:':'Recorre el texto en el verificador mientras quedan llaves abiertas: depth aumenta al abrir y disminuye al cerrar, ignorando comentarios y literales. No es un bucle del ESP32 ni ejecuta el firmware.',
        'std::map<std::string, std::string> values;':'Declara un mapa en RAM: cada nombre de clave se asocia a sus bytes. Es el doble de almacenamiento de la prueba, sin escribir flash ni usar Preferences.',
        'std::map<std::string, unsigned char> markers;':'Declara los marcadores numéricos del doble de memoria: cada clave conserva un byte, como la versión del formato persistente.',
        'std::string json;':'Reserva una cadena de PC para serializar la instantánea completa y verificar un documento mayor que el límite de cadenas NVS.',
        'std::string input, line;':'Declara el JSON de entrada y una línea temporal; el adaptador de PC acumula stdin con límite de 48000 bytes antes de deserializar.',
        'pill::Dose reused;':'Crea la dosis que la prueba reutilizará deliberadamente para comprobar que eventos y reservas anteriores no comparten sus arreglos.',
        'pill::Dose temporary;':'Crea una dosis temporal de ámbito local; sobrescribirla y salir del bloque permite probar la propiedad de memoria del JSON.',
        'std::string serialized;':'Reserva una cadena de PC para serializar el documento completo y probar su reconstrucción sin un ESP32.',
        'JsonDocument reservations;':'Documento JSON del doble de PC que conserva las claves reservadas mediante la misma función usada por el firmware.',
        '[640, 1280, 1920, 2560]);':'Destinos esperados del NEMA 17 con cinco espacios y 3200 pasos/vuelta; se comparan con números capturados, sin señales eléctricas.',
        'access: { users: {':'Inicia la semilla local de permisos ficticios; se escribe exclusivamente con el entorno administrativo del emulador de pruebas.',
        "owner: { role: 'owner', enabled: true, revokedAt: 0, version: 1 },":'Define la cuenta ficticia del responsable habilitada en la base de prueba, sin credenciales reales.',
        "device: { role: 'device', enabled: true, revokedAt: 0, version: 1 },":'Define la cuenta ficticia del dispositivo habilitada; las pruebas posteriores usan sus permisos normales y comprueban su revocación.',
        "devices: { 'pastillero-01': { ownerUid: 'owner', deviceUid: 'device',":'Vincula los UID ficticios al dispositivo de la semilla del emulador; no cambia vínculos en Firebase real.',
        'v2: { program: fixtures.cached } } },':'Coloca el programa de caché como estado anterior de prueba; no se considera una nueva publicación válida de fechas vencidas.',
        'projectId, hardwareUsed: false, productionUsed: false,':'Registra proyecto de demostración y exclusión de hardware/producción en el comprobante de la integración.',
        "nativeProducer: 'ScheduleEngine.program', cppConsumer: 'pill::Controller.tick',":'Identifica las funciones reales que generan y consumen el programa en la integración; no afirma ejecutar la Activity ni WorkManager.',
        'cachedProgramSeededWithRulesDisabled: true,':'Declara explícitamente que el estado histórico se sembró sin reglas dentro del emulador; las operaciones posteriores sí se validan.',
        "limitations: ['No Android UI or WorkManager process in this integration',":'Empieza la lista de límites del comprobante para no presentar la integración PC como una prueba física o de la pantalla nativa.',
        'timeout: 10000, maxBuffer: 100000,':'Limita a diez segundos la ejecución del adaptador C++ y a 100000 bytes su salida para evitar una prueba indefinida o sin límite de memoria.',
        'reservedCount: result.done?.length ?? 0, moves: result.moves ?? [],':'Registra cantidad de reservas y destinos capturados; ?. y ?? toleran ausencia de lista sin inventar movimientos.',
        'Dose doses[96]{};':'Reserva e inicializa el arreglo de 96 ocurrencias V2; count limita el recorrido a las válidas y no se acepta un plan mayor.',
        'exitPulse)':'Completa la condición del sensor: solo un pulso nuevo durante Outward, Drop o Returning puede acreditar salida de esta entrega.',
        'pill::PeripheralSettings preferencias;':'Instancia las preferencias de periféricos en RAM; por defecto solo LED y buzzer están habilitados.',
        'pill::Feedback indicadores;':'Instancia el modelo que calcula salidas y temporización sin escribir GPIO directamente.',
        'pill::ExitDetector detectorSalida;':'Instancia el filtro de diez milisegundos que detecta un flanco nuevo de salida.',
        'previous == pill::State::Awaiting && controlador.state == pill::State::Idle;':'Completa confirmedNow: solo la transición Awaiting→Idle acredita una confirmación nueva para disparar la bomba opcional una vez.',
        'std::vector<std::string> records, done;':'Listas del doble de prueba: records captura eventos y done IDs reservados; no acceden a NVS ni a hardware.',
        'WebView view, WebResourceRequest request) {':'Parámetros del callback de navegación: la vista origen y la solicitud con URL permiten aplicar la lista de origen/directorio permitidos.',
        'String action, JSONObject payload, Consumer<JSONObject> success, Consumer<String> failure) {':'Completa request: acción y datos entran; los callbacks devuelven instantánea o error después del trabajo asíncrono.',
        'List<DoseEvent>':'Tipo genérico del retorno: una lista de filas de historial, obtenida por el método de consulta que sigue.',
        '&& rev == item.baseRevision + 1;':'El mismo token solo acredita una publicación anterior si también coincide su revisión esperada; otro editor no se confunde con un reintento.',
        'DatabaseError e, boolean success, DataSnapshot snapshot) {':'Parámetros del acuse transaccional: error, indicador de confirmación y estado resultante; el callback libera el Worker.',
        '|| m.intervalMinutes > 10080)':'Completa la validación del intervalo: rechaza más de siete días; 10080 son minutos, no milisegundos.',
        '|| p.pumpDurationMs > 5000)':'Completa la validación de preferencias: rechaza una duración de bomba superior a cinco segundos antes de publicar.',
        '!= android.content.pm.PackageManager.PERMISSION_GRANTED':'Completa la condición: el permiso todavía no fue concedido, por lo que puede solicitarse mediante Android.',
        'error -> {});':'Callback sin operación: un fallo de actualización opcional no fabrica datos ni una confirmación; el repositorio conserva Room.',
        'null);':'Argumento nulo que completa la llamada precedente; representa ausencia de error/dato según la firma, no la cadena de texto null.',
        'Dose active{};':'Reserva la estructura privada de la dosis en curso e inicializa sus campos; se copia al seleccionar una candidata.',
        'pill::Dose d;':'Declara una dosis temporal: d.id se rellena con copia limitada y su fecha/compartimento se validan antes de usarla.',
        'pill::Dose key;':'Crea una dosis auxiliar para validar el formato del ID de comando; no agrega un horario ni mueve el motor.',
        'pill::Dose parsed[24];':'Reserva el arreglo temporal del plan; solo se copia al controlador después de validar y persistir el plan completo.',
        'command["planRevision"], registroLocal["plan"]["revision"] | 0);':'Completa commandDecision: compara la revisión pedida con la aplicada; el operador ArduinoJson | entrega cero si falta la revisión local.',
        'std::vector<long> moves;':'Lista del doble de prueba que captura los destinos solicitados en pasos, sin enviar señales eléctricas.',
        'std::vector<std::string> events;':'Lista de tipos de eventos observados por la prueba; las afirmaciones comparan su orden y contenido.',
        'std::set<std::string> done;':'Conjunto de IDs reservados del doble: simula la consulta persistente de duplicados sin un ESP32.',
        'passed);':'Argumento final de printf: muestra el número de casos aprobados y cierra la llamada; no incrementa el contador.',
        '!= PackageManager.PERMISSION_GRANTED)':'Completa la comparación del permiso: si no está concedido, el return siguiente omite el aviso y conserva el evento.',
        'LiveData<List<DoseEvent>>':'Tipo de retorno de observeEvents: lista de eventos observable y ligada al ciclo de vida; la firma continúa en la línea siguiente.',
        'public static final androidx.room.migration':'Inicio dividido de la declaración MIGRATION_2_3: pública, compartida y no reasignable; el tipo completo Migration continúa debajo.',
        'private ValueEventListener planListener, stateListener, connectionListener, resultsListener,':'Declara las referencias de cuatro listeners para poder retirarlos exactamente al cerrar o revocar acceso; accessListener completa la declaración debajo.',
        '? "calibrado"':'Rama verdadera del ternario: muestra calibrado solo cuando la telemetría contiene calibrated=true; debajo está la alternativa.',
        'DatabaseError error, boolean success, DataSnapshot snapshot) {':'Parámetros de onComplete: error recibe el fallo, success el acuse de la transacción y snapshot la instantánea resultante; el cuerpo libera la espera del Worker.',
        'uid:user.uid,email:user.email??null,disabled:user.disabled,':'Proyección administrativa: expone UID, correo o null si falta y estado disabled; no incluye hashes de contraseñas ni tokens.',
        '...old,enabled:body.enabled,version:old.version+1,updatedAt:now,updatedBy:actor,':'Copia el permiso anterior, cambia enabled, incrementa versión y registra hora/autor dentro de la transacción administrativa.',
        'old===null || old===uid?uid:undefined,undefined,false);':'Completa la transacción de administrador protegido: permite inicializar o confirmar el mismo UID; undefined aborta un cambio a otra identidad. false desactiva eventos locales especulativos.',
    }
    if s in special:return special[s],parts
    if s.startswith('? "Firebase conectado'):
        return 'Rama verdadera del ternario de conectividad: muestra conexión del SDK con Firebase y DEVICE_ID; la rama falsa informa que Room sigue disponible.',parts
    if filename=='generate_study_guides.py' and s.startswith("ROOT/'"):
        return 'Continúa el inventario de archivos de configuración: cada ruta se resuelve desde ROOT. Los valores privados se redactan antes de formar las tablas; el corchete final cierra la lista.',parts
    if s in ('Credentials are read only from ignored local files and are never printed.','Reads ignored properties, passes credentials in memory and never prints command arguments.'):
        return 'Texto de la documentación del módulo: indica que las credenciales se leen de archivos ignorados y no se imprimen ni se incorporan al APK. No es una instrucción ejecutable.',[]
    if not s: return 'Línea vacía: separa visualmente instrucciones; no ejecuta una operación.',[]
    if s.startswith(('//','/*','*','<!--','# ')): return 'Comentario de lectura: '+s.lstrip('/*# ').rstrip('*/> ')+'. No se ejecuta.',[]
    if filename=='.gitignore':
        return 'Regla Git: excluye el patrón `'+s+'` del seguimiento automático. Protege configuración privada o evita versionar bibliotecas, cachés y binarios generados; no borra el archivo local.',parts
    if filename=='partitions.csv' and not s.startswith('#'):
        values=s.split(',');purpose={'nvs':'instantánea persistente y reserva de dosis','otadata':'metadatos de selección de aplicación','app0':'primera ranura de aplicación','app1':'segunda ranura de aplicación','spiffs':'área de datos de sistema de archivos'}
        return 'Partición '+values[0]+': tipo '+values[1]+', subtipo '+values[2]+', empieza en '+values[3]+' ('+str(int(values[3],16))+' bytes) y reserva '+values[4]+' ('+str(int(values[4],16))+' bytes). Uso: '+purpose.get(values[0],'partición indicada')+'. Las ranuras OTA reservan espacio; no implican que se haya implementado una actualización remota.',parts
    if s.startswith(('"""',"'''")) or s in ('"""',"'''"):
        return 'Cadena de documentación Python: explica el propósito del módulo o función y no ejecuta una operación Firebase ni de hardware.',parts
    if re.match(r'^def [A-Za-z_]\w*\(',s):
        name=s.split('def ',1)[1].split('(',1)[0]
        return 'Define la función Python `'+name+'()` con sus parámetros; '+CALLS.get(name,'agrupa el procesamiento local descrito por su nombre y sus instrucciones siguientes')+'.',parts
    if s.startswith('raise '): return 'Interrumpe la herramienta con el error indicado; evita declarar una validación aprobada si falta un requisito.',parts
    if s.startswith('except '): return 'Captura el tipo de excepción indicado y registra únicamente el estado/tipo de fallo, sin publicar contraseñas ni tokens.',parts
    if s.startswith('assert '): return 'Verifica exactamente la condición escrita; si es falsa termina con fallo y no permite dar esta comprobación como aprobada.',parts
    if filename.endswith('.py') and re.match(r'^if\s+',s): return 'Evalúa la condición Python indicada antes de la acción después de los dos puntos o de las siguientes líneas indentadas.',parts
    if filename in ('study_explanations.py','generate_study_guides.py','study_notes.py'):
        m=re.match(r"^['\"](.+?)['\"]\s*:",s)
        if m: return 'Entrada de un diccionario de estudio: asocia `'+m.group(1)+'` con el texto explicativo o traducción literal de esta misma línea. Es contenido de documentación, no un valor de credencial ni una orden del dispositivo.',parts
    if 'memoriaPersistente.begin(' in s:
        return 'Abre NVS: pill-sim para simulación o pastillero para hardware. El argumento false habilita lectura y escritura; el valor devuelto indica si pudo abrirse. No se comparte el historial de reservas entre modos.',parts
    if filename.endswith('.xml'):
        parts=[]
    if filename.endswith('.gradle'):
        descriptions={
            'plugins':'Configura complementos de compilación; com.android.application transforma el módulo en app Android.',
            'apply false':'Declara la versión del complemento en la raíz sin aplicarlo allí; app lo aplica en su propio archivo.',
            'pluginManagement':'Fija de dónde se obtienen los complementos Gradle.',
            'dependencyResolutionManagement':'Centraliza repositorios y reglas de resolución de bibliotecas.',
            'repositories':'Agrupa repositorios permitidos para descargar dependencias necesarias.',
            'google()':'Repositorio oficial de componentes Android y Google.',
            'mavenCentral()':'Repositorio Maven Central para bibliotecas declaradas por versión.',
            'gradlePluginPortal()':'Repositorio de complementos Gradle, separado de bibliotecas de la app.',
            'FAIL_ON_PROJECT_REPOS':'Rechaza repositorios añadidos por un módulo y conserva los declarados en settings.',
            'rootProject.name':'Nombre mostrado por Gradle/Android Studio; no cambia el paquete instalado ni la base Room.',
            "include ':app'":'Incluye app/ como módulo del proyecto raíz.',
            'publicFirebase':'Mapa de configuración pública de la app registrada; no contiene cuentas administrativas.',
            'googleConfig':'Ruta google-services.json relativa al módulo app; no se escribe en el código una contraseña.',
            'JsonSlurper':'Analiza el JSON local antes de seleccionar el cliente que corresponde al paquete real.',
            'project_id':'Se exige pastillerobadi para no conectar por error con CRUDSQLITE1.',
            'androidClient':'Selecciona el cliente cuyo paquete coincide con mx.edu.badi.pastillero.',
            'getProperty':'Busca primero la propiedad local y usa el valor público/predeterminado cuando falta.',
            'new Properties':'Prepara un contenedor de configuración local sin iniciar conexión Firebase.',
            'withInputStream':'Lee el archivo de configuración y cierra su flujo al terminar el bloque.',
            'quoted':'Construye un literal String válido para BuildConfig: escapa barras inversas y comillas de la configuración.',
            'namespace':'Paquete de recursos R y clases generadas; se conserva mx.edu.badi.pastillero.',
            'compileSdk':'API 36 usada para compilar referencias Android; no es la versión mínima instalable.',
            'defaultConfig':'Reúne valores base del APK como identificación, versiones y constantes.',
            'applicationId':'Identidad instalada del APK y la registrada en Firebase: mx.edu.badi.pastillero.',
            'minSdk':'API mínima 24: un dispositivo anterior no instala este APK.',
            'targetSdk':'API objetivo 36: selecciona los comportamientos modernos que la app declara soportar.',
            'versionCode':'Número entero creciente de actualización del APK; esta entrega usa 7.',
            'versionName':'Etiqueta visible de entrega: 2.0-simulacion; distinta de la versión 4 del esquema Room.',
            'testInstrumentationRunner':'Selecciona AndroidJUnitRunner para pruebas sobre el emulador.',
            'buildConfigField':'Genera una constante pública String del APK a partir de la configuración; no incluye contraseñas del responsable/ESP32.',
            'javaCompileOptions':'Configura el procesador de anotaciones que genera las implementaciones Room.',
            'room.schemaLocation':'Exporta los esquemas a app/schemas para poder comprobar migraciones.',
            'buildFeatures':'Habilita características de generación del módulo.',
            'buildConfig true':'Activa la clase BuildConfig usada por el proyecto.',
            'compileOptions':'Configura el nivel de lenguaje y bytecode Java del módulo.',
            'VERSION_11':'Nivel Java 11 de las fuentes/destino; Gradle se ejecuta con el JDK de Android Studio.',
            'returnDefaultValues':'Permite valores predeterminados de stubs Android en pruebas JVM; no sustituye pruebas instrumentadas Room.',
            'sourceSets':'Configura carpetas que pertenecen a cada conjunto de fuentes/pruebas.',
            'androidTest.assets':'Incluye los esquemas históricos Room como recursos del APK de pruebas.',
            'dependencies':'Reúne las bibliotecas necesarias en cada ámbito de compilación.',
            'implementation':'Empaqueta la biblioteca de producción en la aplicación.',
            'testImplementation':'Añade una biblioteca solo al ejecutor de pruebas JVM.',
            'androidTestImplementation':'Añade una biblioteca solo al APK de pruebas instrumentadas.',
            'annotationProcessor':'Ejecuta el compilador de Room al compilar; no hace consultas de disco en la pantalla.'
        }
        selected=[meaning for word,meaning in descriptions.items() if word in s]
        if selected and not s.startswith(('if','throw','} else')):return ' '.join(selected),parts
        if s.startswith('if'):return 'Condición Groovy de configuración: comprueba '+s.split('if',1)[1].strip()+' antes de cargar o validar valores del APK. Un rechazo evita compilar con otro proyecto Firebase.',parts
    if s.startswith('#include'):
        name=s.split('include',1)[1].strip(' <>"')
        return 'Incluye '+name+': '+LIBRARIES.get(name,FILES.get(name,'declaraciones compartidas para este archivo'))+'. No ejecuta el recurso al incluirlo.',parts
    if s.startswith('#pragma once'): return 'Hace que esta cabecera solo se incluya una vez por unidad de compilación; evita definiciones repetidas.',parts
    if s.startswith(('#if','#else','#endif')):
        return 'Selección de compilación: '+({'#else':'elige la alternativa del bloque anterior','#endif':'cierra el bloque condicional'}.get(s,'incluye este bloque solo si la condición del preprocesador se cumple'))+'. Lo excluido no llega al binario.',parts
    if s.startswith('#define'): return 'Define una constante o bandera del preprocesador antes de compilar. Su valor decide capacidad, configuración o qué código se incluye.',parts
    if re.fullmatch(r'[{}\[\]();,]+(?:\s*//.*)?',s): return 'Delimita o cierra el bloque, llamada o colección iniciado antes; determina qué instrucciones pertenecen al mismo ámbito.',[]
    if s.startswith('package '): return 'Declara el paquete que agrupa las clases propias de Android; coincide con su organización de carpetas y referencias.',parts
    if s.startswith(('import ','from ')): return 'Importa '+s.rstrip(';')+': permite usar esos tipos o herramientas por su nombre. No sustituye la configuración de dependencias del proyecto.',parts
    if 'SELECT ' in s or 'UPDATE ' in s or 'CREATE TABLE' in s or 'ALTER TABLE' in s or 'INSERT INTO' in s: return sql_explain(s),parts
    annotations={'@Database':'Declara entidades, versión 4 y exportación del esquema Room; las migraciones mantienen los datos anteriores.','@Entity':'Declara el nombre de tabla y, cuando aparece, la clave primaria compuesta para evitar duplicados.','@Dao':'Indica que Room debe generar la implementación de las consultas de esta interfaz.','@Query':'Asocia el SQL a la firma del método que sigue; Room comprueba consulta y tipos al compilar.','@Insert':'Declara una inserción Room: IGNORE conserva el registro existente y REPLACE sustituye solo el borrador con la misma clave.','@PrimaryKey':'Declara la columna o pareja que identifica una fila única.','@NonNull':'Excluye NULL de ese campo o parámetro; Room lo refleja en el esquema.','@Override':'Comprueba que este método implementa uno heredado; ayuda a detectar nombres o firmas incorrectos.','@Test':'Define un caso de prueba automatizada; expected declara el error que debe producir una entrada inválida.','@RunWith':'Selecciona el ejecutor de pruebas Android que proporciona contexto y ciclo de instrumentación.'}
    for prefix,meaning in annotations.items():
        if s.startswith(prefix): return meaning,parts
    if s.startswith('@'): return 'Anotación de compilación: añade metadatos de nulabilidad, valor por defecto o prueba al elemento siguiente; no es un botón ni una orden remota.',parts
    if re.search(r'\b(class|struct|interface|enum|namespace)\b',s) and ('{' in s or s.endswith('extends')):
        return 'Declara la estructura de tipos/ámbito indicada: agrupa datos u operaciones y fija visibilidad o herencia. No inicia por sí sola una dosis.',parts
    if s in ('public:','private:','protected:'): return 'Fija visibilidad C++ para los miembros siguientes: público se usa desde fuera; privado protege el estado interno.',parts
    if s.startswith('static_assert'): return 'Obliga a cumplir la condición durante la compilación; rechaza una configuración incompatible antes de ejecutar el motor.',parts
    if re.match(r'(?:}\s*)?else\s+if\s*\(',s): return 'Evalúa esta alternativa solo si la condición anterior no se cumplió; así una fase no ejecuta otra rama incompatible.',parts
    if re.match(r'(?:}\s*)?else\b',s): return 'Toma la alternativa cuando no se cumplió la condición precedente; mantiene mutuamente excluyentes ambas rutas.',parts
    if s.startswith('if') and re.match(r'if\s*\(',s): return 'Comprueba la condición antes de la instrucción o bloque siguiente. Cada comparación y combinación de condiciones se detalla a continuación.',parts
    if s.startswith(('for (','for(','for await','for ')): return 'Recorre la colección o contador indicado. Inicio fija el primer elemento, condición decide si continúa y avance pasa al siguiente; no crea una orden duplicada por sí mismo.',parts
    if s.startswith(('while (','while(')): return 'Repite mientras se cumpla la condición; en colas/serial procesa solo datos ya disponibles y en red se cede CPU al final.',parts
    if s.startswith('switch'): return 'Selecciona una traducción o acción según el estado/tipo; cada case enumera un valor del contrato.',parts
    if s.startswith('case '): return 'Asocia el valor de esta rama con el mensaje o instrucción que sigue; conserva el orden/valor del contrato.',parts
    if s.startswith('default:'): return 'Ofrece una salida segura/comprensible para un valor no reconocido, sin inventar una confirmación.',parts
    if s.startswith('return'): return 'Devuelve `'+s[len('return'):].strip().rstrip(';')+'` al llamador y termina esta invocación. Si no hay valor, solo cede el control para una próxima iteración/callback.',parts
    if s.startswith('break'): return 'Sale del bucle o selección actual; se usa para dejar pendientes cuando una publicación no recibió acuse.',parts
    if s.startswith('continue'): return 'Omite el resto de esta iteración y revisa el elemento siguiente; permite saltar IDs ya procesados.',parts
    if s.startswith('throw'): return 'Rechaza la entrada o situación indicada mediante una excepción que se informa o se espera en una prueba; no continúa con datos inválidos.',parts
    if re.search(r'\bcatch\b',s): return 'Captura el fallo de la operación protegida y permite informar, reintentar o fallar cerrado sin borrar el historial.',parts
    if s.startswith('try'): return 'Inicia una operación que puede fallar; en try con recurso se garantiza su cierre al terminar.',parts
    if 'finally' in s: return 'Ejecuta limpieza incluso cuando falla una operación: cerrar recursos, restaurar simulación o terminar sesiones de prueba.',parts
    if filename.endswith('.xml'):
        attrs=re.findall(r'([\w:.-]+)\s*=\s*"([^"]*)"',s)
        if attrs:
            details=[f'`{name}={value}`: '+ATTRIBUTES.get(name,'configura el atributo indicado de esta etiqueta') for name,value in attrs]
            if '<string' in s: details.append('El contenido entre etiquetas es un texto de la interfaz; %s/%d son argumentos cuyo orden y tipo se conservan')
            return '; '.join(details)+'.',parts
        if s.startswith('</'): return 'Cierra el elemento XML `'+s+'` y devuelve la jerarquía a su contenedor padre.',parts
        if s.startswith('<'): return 'Abre el elemento XML `'+s+'`: define un control, recurso, permiso o grupo, cuyos atributos se explican en las líneas siguientes.',parts
    if re.search(r'\b(?:public|private|protected|static|inline|void|bool|int|String|long|def|async function|function)\b.*\b([A-Za-z_]\w*)\s*\([^;]*\)\s*(?:throws[^{}]+)?\{',s):
        names=re.findall(r'\b([A-Za-z_]\w*)\s*\(',s)
        name=names[0] if names else context
        return 'Define `'+name+'()`: '+CALLS.get(name,'encapsula la operación de este nombre y recibe los parámetros declarados, separando sus responsabilidades')+'. Sus instrucciones se recorren en las líneas siguientes.',parts
    callnames=re.findall(r'\b([A-Za-z_]\w*)\s*(?:<[^;{}]*?>)?\s*\(',s)
    meaningful=[name for name in dict.fromkeys(callnames) if name in CALLS]
    if meaningful: return 'Realiza '+ '; '.join('`'+name+'()`: '+CALLS[name] for name in meaningful)+'. El orden escrito es el orden de evaluación de esta instrucción.',parts
    if 'new ' in s: return 'Crea el objeto indicado y prepara sus datos iniciales; su tipo determina si representa interfaz, JSON, base, callback o trabajo diferido.',parts
    if re.search(r'(?<![=!<>])=(?!=|>)',s):
        lhs=s.split('=',1)[0].strip();rhs=s.split('=',1)[1].strip().rstrip(';')
        return 'Guarda en `'+lhs+'` el valor de `'+rhs+'`. El signo = asigna; no pregunta si ambos valores son iguales. Esta inicialización/actualización alimenta la operación posterior del mismo ámbito.',parts
    if s.startswith('plugins') or s.startswith('id '): return 'Selecciona el complemento Android/Gradle y su versión; configura cómo se compilan las fuentes del módulo.',parts
    if re.search(r'\b(implementation|testImplementation|androidTestImplementation|annotationProcessor)\b',s): return 'Declara la dependencia del ámbito indicado: aplicación, prueba JVM, prueba Android o procesador Room que genera código durante compilación.',parts
    if filename.endswith('.gradle'): return 'Configura la propiedad o bloque Gradle escrito en esta línea; su valor se aplica en la fase de configuración/compilación y no ejecuta una dosis.',parts
    if s.startswith(('".read"','".write"')): return 'Regla de autorización: decide qué identidad puede leer/escribir esta ruta. false deniega y la expresión comprueba el UID y los metadatos del permiso.',parts
    if s.startswith('".validate"'): return 'Regla de validación: exige tipos, campos y/o inmutabilidad del dato después de autorizar la escritura; un rechazo no confirma un comando.',parts
    if s.startswith('".indexOn"'): return 'Declara un índice de Realtime Database para ordenar/limitar consultas sin descargar todo el historial.',parts
    if s.startswith('"') and ':' in s: return 'Declara la clave JSON y su valor o subárbol; en reglas, $nombre captura el identificador de la ruta y no concede acceso por sí solo.',parts
    if s.startswith('$') or filename.endswith('.ps1'): return 'Instrucción PowerShell del flujo de compilación/verificación: calcula el valor, llama la herramienta o comprueba el estado indicado; no contiene una carga de firmware.',parts
    if filename.endswith('.properties'): return 'Propiedad de configuración con nombre y valor separados por =; Gradle/la herramienta que la lee interpreta el tipo y la unidad.',parts
    if s.endswith(';') and re.match(r'[\w@<>.,\s\[\]*&]+;',s): return 'Declara el campo, tipo o firma con la visibilidad indicada; la definición o uso concreto aparece en las instrucciones del mismo archivo.',parts
    if re.match(r'^[:+]\s*',s):
        return 'Continúa la expresión anterior: `:` introduce la alternativa falsa del condicional y `+` concatena el siguiente fragmento de texto según el carácter escrito. El contenido literal explica el estado mostrado o completa el SQL; no se ejecuta separadamente.',parts
    if s.startswith(('"',"'")):
        if any(word in s for word in ('GET','POST','PUT','application/x-www-form-urlencoded')):
            return 'Argumento literal del transporte HTTPS: GET consulta, POST autentica/renueva y PUT publica un valor. El tipo form-urlencoded identifica la renovación de sesión. body es el cuerpo y code recibe el estado HTTP; no se imprime un token.',parts
        return 'Texto literal que completa la llamada o colección anterior: el contenido visible es un mensaje, resultado esperado, nombre de campo o parte de la consulta. Las comillas lo distinguen de una variable; los paréntesis/comas finales cierran o separan argumentos.',parts
    if s in ('void','int','String','long','Toast'):
        return 'Continúa una declaración/llamada dividida: '+({'void':'no devuelve valor','int':'tipo entero','String':'tipo de texto','long':'entero largo','Toast':'clase Android de avisos breves'}[s])+'. El nombre, parámetros y operación se completan en las líneas adyacentes.',parts
    if re.match(r'^(?:int|long|bool|char|size_t|uint32_t|int64_t)\s+[A-Za-z_]',s):
        return 'Declara el parámetro o campo con el tipo y nombre escritos. Una coma continúa la firma; `)` termina sus parámetros y `{` inicia su implementación.',parts
    if re.match(r'^\d+',s):return 'Valor numérico que completa la definición anterior; su unidad y papel se explican en la declaración y constantes relacionadas.',parts
    if '(' in s:
        names=re.findall(r'\b([A-Za-z_]\w*)\s*\(',s)
        return 'Llama o completa `'+('(), `'.join(names)+'()' if names else context)+'`: los argumentos escritos suministran sus valores y el receptor determina qué instancia se usa. La definición de ese método aparece en este archivo o en las dependencias importadas.',parts
    if re.match(r'^\w+\.\w+',s):return 'Selecciona el miembro o constante con nombre completo `'+s.rstrip(',;')+'`; se usa como argumento de la llamada iniciada antes. No crea un objeto ni modifica datos por sí solo.',parts
    if s.startswith(('}',']',')')):return 'Cierra la función, callback, arreglo o llamada empezada antes y, si hay comas, continúa la estructura contenedora.',parts
    if s.rstrip(',;').isidentifier():return 'Referencia al parámetro o variable `'+s.rstrip(',;')+'` como argumento de la instrucción contenedora; no declara otra variable ni crea otra solicitud.',parts
    return 'Continúa la instrucción escrita en las líneas contiguas: esta parte aporta los argumentos, tipos, condición o encadenamiento que aparecen literalmente en la columna de código. Debe leerse con sus aperturas y cierres, no como una orden independiente.',parts

# Operaciones pequeñas usadas en varias clases: se explican individualmente en cada línea.
CALLS.update({
    'put':'asocia la clave al valor en un mapa, JSON o Bundle según el receptor',
    'get':'consulta el elemento, campo, propiedad o recurso del receptor; en DatabaseReference devuelve una Task asíncrona',
    'set':'asigna un valor al objeto o una fecha Calendar según el receptor; no envía por sí solo una dosis',
    'add':'añade un elemento a la colección o solicita editar el borrador según el receptor',
    'remove':'retira la clave/elemento indicado sin eliminar por sí mismo el historial completo',
    'size':'consulta cuántos elementos hay para comprobar límites antes de continuar',
    'length':'mide la longitud del texto, arreglo u objeto JSON según el receptor',
    'isEmpty':'comprueba si falta contenido antes de autenticar, presentar o publicar',
    'equals':'compara contenido de objetos o textos, en vez de comparar sus direcciones',
    'equalsIgnoreCase':'compara textos sin distinguir mayúsculas de minúsculas',
    'matches':'exige que todo el identificador cumpla la expresión regular permitida',
    'keys':'itera las claves del objeto JSON para validar y ordenar las dosis',
    'next':'obtiene el elemento siguiente del iterador o el identificador de dosis',
    'hasNext':'comprueba que el iterador aún tiene elementos',
    'getJSONObject':'exige que el campo JSON sea un objeto antes de leer sus propiedades',
    'optJSONObject':'consulta un objeto opcional sin lanzar excepción si falta',
    'getJSONArray':'obtiene el arreglo del esquema Room usado en la prueba de migración',
    'getLong':'lee un entero largo, empleado en fechas Unix y revisiones',
    'getInt':'lee un entero, empleado para compartimentos y contadores',
    'getDouble':'lee como número decimal para detectar valores que no eran enteros',
    'optLong':'lee un número opcional para ordenar las fechas del plan mostrado',
    'append':'agrega la parte indicada a un StringBuilder sin cambiar su significado',
    'toString':'convierte el acumulador/JSON/UUID a su representación textual',
    'valueOf':'convierte un valor a texto manejando también la ausencia de valor',
    'sort':'ordena identificadores usando la fecha de cada dosis, manteniendo su identidad estable',
    'comparingLong':'construye un criterio de orden basado en una fecha long',
    'forEachRemaining':'recorre las claves restantes del iterador para construir la lista mostrada',
    'forName':'obtiene una clase por su nombre para una comprobación de prueba',
    'clear':'vacía solo la colección de trabajo en RAM antes de reconstruir la pantalla',
    'format':'presenta fecha con el formato y zona horaria configurados',
    'getDateTimeInstance':'elige formato local de fecha y hora; los dos argumentos SHORT seleccionan estilo breve para cada una',
    'getDefault':'obtiene la zona horaria actual del teléfono',
    'getID':'muestra el identificador de zona horaria junto a la fecha elegida',
    'getApplicationContext':'obtiene el contexto del proceso para no retener la Activity',
    'getSystemService':'obtiene un servicio Android como NotificationManager',
    'setPositiveButton':'registra la acción afirmativa del diálogo antes de recargar el borrador',
    'setNegativeButton':'permite cancelar el diálogo sin modificar el borrador',
    'setTitle':'establece el título del diálogo de confirmación',
    'setMessage':'explica la consecuencia antes de descartar un borrador local',
    'show':'hace visible el selector, diálogo o aviso ya configurado',
    'makeText':'prepara un aviso Toast corto de validación o error',
    'getText':'obtiene el contenido de un campo de entrada antes de validar/autenticar',
    'trim':'retira espacios del correo sin alterar la contraseña',
    'isSuccessful':'distingue el éxito de una operación asíncrona antes de recrear la pantalla',
    'randomUUID':'crea una identidad estable nueva solo para una nueva dosis/borrador/solicitud',
    'hashCode':'deriva un identificador del aviso por scope y evento; no es cifrado de contraseña',
    'setSmallIcon':'elige el icono del aviso de dosis',
    'setContentTitle':'distingue un aviso de simulación de un evento del dispositivo',
    'setContentText':'muestra tipo de evento y compartimento sin afirmar que una prueba es una toma real',
    'setAutoCancel':'retira el aviso cuando la persona lo abre',
    'build':'termina el constructor del objeto configurado, según su tipo',
    'setApiKey':'carga la configuración pública del SDK; no entrega autoridad administrativa',
    'setApplicationId':'selecciona la app Firebase registrada para el paquete Android',
    'setProjectId':'fija el proyecto Firebase dedicado antes de acceder a datos',
    'setDatabaseUrl':'fija la URL de Realtime Database del proyecto Badi',
    'getApps':'comprueba si Firebase ya fue inicializado para no registrarlo dos veces',
    'getInstance':'obtiene la instancia compartida del servicio/SDK solicitado',
    'setInputData':'transporta únicamente el UID al Worker, sin contraseña ni token en la cola',
    'putString':'guarda una cadena bajo su clave en NVS o en datos de trabajo según el receptor',
    'setConstraints':'aplica restricciones de conectividad al trabajo persistente',
    'close':'libera base/cursor/recurso/listeners; no equivale a borrar historial',
    'deleteDatabase':'elimina únicamente la base temporal nombrada por la prueba en el emulador de QA',
    'query':'consulta SQLite para verificar directamente las filas conservadas tras migrar',
    'moveToFirst':'comprueba que la consulta de verificación devolvió al menos una fila',
    'getColumnIndex':'obtiene la posición de una columna del cursor de consulta',
    'setVersion':'marca la versión de la base temporal antigua que la prueba hará migrar',
    'openOrCreateDatabase':'abre una base temporal SQLite para reconstruir el esquema anterior en la prueba',
    'getDatabasePath':'obtiene la ruta privada de la base temporal de prueba, no la de otro proyecto',
    'getAssets':'abre los esquemas Room exportados que usa la prueba de migración',
    'open':'abre el recurso o archivo indicado para leer el esquema sin modificarlo',
    'read':'lee bytes del recurso o serial según el receptor; se comprueba fin de entrada',
    'write':'copia bytes al acumulador de esquema o respuesta limitada según el receptor',
    'replace':'sustituye el marcador indicado; en el esquema coloca el nombre real de tabla',
    'getInstrumentation':'accede al entorno de prueba conectado solo al emulador de QA',
    'getTargetContext':'obtiene el contexto del APK que se está probando',
    'getContext':'obtiene el contexto del APK de pruebas para leer sus recursos',
    'getArguments':'lee credenciales solo en tiempo de ejecución de la prueba real optativa',
    'assumeTrue':'habilita la integración real solo con sus argumentos; se ejecuta separadamente para no ocultar pruebas locales',
    'waitFor':'espera una Task con límite temporal en el hilo de instrumentación, nunca en MainActivity',
    'denied':'comprueba que una operación prohibida devuelve un rechazo de permisos',
    'delete':'libera una FirebaseApp secundaria creada por la prueba; no elimina el proyecto Firebase',
    'abs':'mide diferencia temporal positiva para separar dos dosis diez minutos',
    'max':'elige el mayor corte temporal para que una revocación nunca retroceda',
    'min':'limita el tiempo de reconexión a sesenta segundos',
    'printf':'informa estado de la simulación/prueba sin imprimir contraseñas ni tokens',
    'println':'muestra un mensaje de calibración/estado por Serial sin crear una orden remota',
    'available':'comprueba si hay datos disponibles de Serial o del flujo',
    'mode':'configura Wi-Fi como estación para conectarse al router existente',
    'setAutoReconnect':'permite recuperar Wi-Fi automáticamente, además del retroceso explícito',
    'status':'consulta conexión Wi-Fi o actualiza estado de un borrador mediante DAO según el receptor',
    'as':'interpreta el tipo JSON comprobado; no sustituye la validación previa',
    'is':'comprueba que un valor JSON tiene el tipo solicitado antes de convertirlo',
    'to':'crea/obtiene la estructura JSON receptora donde se escribirán los campos',
    'isinstance':'comprueba el tipo Python antes de procesar un valor JSON o colección',
    'len':'cuenta elementos o líneas antes de verificar capacidad/cobertura',
    'range':'construye una secuencia de índices sin acceder a hardware',
    'enumerate':'recorre elementos junto con su número de línea o índice',
    'print':'informa únicamente el resultado público de una comprobación',
    'json':'convierte el cuerpo a JSON según la herramienta o biblioteca',
    'loads':'interpreta JSON leído de texto y falla si su sintaxis no es válida',
    'dumps':'serializa un informe/configuración con estructura JSON consistente',
    'resolve':'obtiene la ruta absoluta normalizada del archivo del proyecto',
    'relative_to':'presenta rutas relativas al proyecto, sin depender de la carpeta de otro desarrollo',
    'mkdir':'crea una carpeta de informes/configuración dentro del proyecto',
    'splitlines':'separa el texto en líneas manteniendo su orden para lectura y referencias',
    'split':'separa campos por el delimitador indicado, como nombre=valor de una propiedad',
    'join':'reúne fragmentos en una cadena o ruta conforme al receptor',
    'strip':'retira espacios de un campo no secreto o de una línea para su análisis',
    'items':'recorre claves y valores de un diccionario de configuración',
    'exists':'comprueba presencia del archivo/ruta/dato antes de usarlo',
    'suffix':'extensión del archivo usada para seleccionar fuentes propias',
    'is_file':'distingue archivos de carpetas antes de calcular huellas o copiar',
    'readFileSync':'lee configuración del servidor confiable; el archivo privado no se empaqueta en clientes',
    'createServer':'registra el manejador de solicitudes HTTP del backend administrativo',
    'end':'cierra HTTP o envía el resultado ya autorizado; el receptor determina el caso',
    'setHeader':'fija formato JSON y protección de caché/origen para la API administrativa',
    'JSON':'representa la carga de intercambio; los tipos se validan antes de usarlos',
})

CALLS.update({
    'start':'instala el observador de permisos del responsable y verifica su vínculo antes de sincronizar',
    'super':'invoca el constructor o método de la clase base, preservando el ciclo de vida y los parámetros del Worker',
    'accept':'ejecuta el callback recibido con la instantánea ya observada, sin una nueva lectura de red',
    'verifyMigration':'reconstruye una base de versión 1 o 2, migra a 3 y comprueba que conserva filas y cola',
    'fail':'marca explícitamente una prueba como fallida si se permitió una operación que debía rechazarse',
    'getInsets':'lee los márgenes ocupados por las barras del sistema',
    'systemBars':'selecciona las barras de estado y navegación como origen de los márgenes',
    'setPadding':'aplica los cuatro márgenes en el contenedor para que los controles no queden tapados',
    'due':'prepara en el doble C++ una dosis ya vencida y un controlador calibrado para comprobar una transición',
    'push_back':'añade un movimiento/evento a la lista de observaciones del doble de prueba',
    'strcpy':'copia un literal de prueba a un arreglo de tamaño suficiente; el código de red usa copia limitada',
    'strtoll':'convierte el argumento textual del puente de prueba a entero de 64 bits para fechas',
    'atoi':'convierte el argumento del puente a una revisión entera',
    'dispensarYRegresar':'función histórica del sketch original con movimientos bloqueantes; solo se estudia y no se ejecuta',
    'test':'declara un caso Node de seguridad o sincronización; sus afirmaciones determinan si pasa',
    'deepEqual':'compara todos los campos/elementos del resultado con el esperado, no solo su referencia',
    'equal':'exige igualdad del valor observado en una prueba Node',
    'rejects':'exige que una operación asíncrona rechace una situación prohibida',
    'stringify':'convierte un objeto a JSON antes de transportarlo o comprobar que no contiene campos privados',
    'quote':'codifica un componente de URL sin imprimir su contenido',
    'save':'escribe el informe público del sondeo sin tokens ni contraseñas',
    'redact':'reemplaza valores locales por marcadores antes de formar las guías y sus huellas',
    'annotate':'añade comentarios de estudio sin modificar literales privados ni bloques PEM',
    'immutable':'construye la comparación de campos inmutables del helper histórico; las reglas vigentes son el archivo revisado, no se regenera con este helper',
})
TERMS.update({'int':'entero usado para índices, compartimentos o códigos HTTP; las fechas se guardan en 64 bits',
    'applied':'revisión que ya está aplicada, comparada con la pedida por APPLY_PLAN',
    'requested':'hora de creación recibida del comando en milisegundos UTC',
    'expires':'fecha de caducidad del comando en milisegundos UTC',
    'now':'hora actual usada para validar una solicitud o lectura actual del botón según la función',
    'code':'código HTTP de la última solicitud: 200 éxito, 401 sesión inválida y 403 acceso rechazado',
    'body':'texto JSON o formulario que se envía por HTTPS',
    'refreshToken':'campo efímero que permite renovar una sesión; su valor nunca aparece en la guía',
    'APPEND_OR_REPLACE':'política WorkManager que encadena trabajo válido y reemplaza una cadena fallida para permitir reintentar',
    'passed':'contador de casos C++ que llegaron a su afirmación final sin fallo'})

TERMS.update({
    'n':'cantidad de caracteres/bytes o resultado de lectura, según el tipo de la función',
    'i':'índice de recorrido; empieza en cero y no es el número físico de compartimento por sí solo',
    'next':'candidato de dosis más antigua en Controller; en iteradores next() obtiene el siguiente elemento',
    'position':'posición absoluta de destino expresada en pasos del motor',
    'raw':'lectura instantánea del botón antes de validar estabilidad; en la herramienta de guías marca un literal PEM',
    'stable':'último nivel del botón que se mantuvo estable durante el filtro',
    'changed':'marca millis del último cambio instantáneo para filtrar rebotes del pulsador',
    'starting':'indica STARTED; antes de reservar se deja margen en la cola de eventos para finalizar/recuperar la entrega',
    'latest':'última instantánea que la tarea de red recibió desde loop; no accede directamente al registro que modifica el controlador',
    'committed':'indica que Firebase confirmó la transacción o que el mismo borrador ya estaba confirmado',
    'already':'identifica que el token y revisión enviados ya existían antes del reintento',
    'failure':'guarda el error del callback para decidir reintento o conflicto',
    'publicFirebase':'mapa de valores públicos del cliente registrado; no una identidad administrativa',
    'quoted':'función Gradle que escapa texto para generar constantes Java de tipo String',
    'PD_PASS':'valor de éxito de una operación FreeRTOS, comprobado antes de continuar'})
CALLS.update({
    'AccelStepper':'construye el controlador DRIVER con pin de pasos y dirección; los pines adicionales 0 no se usan y enable=false evita configurar GPIO en el constructor',
    'sizeof':'obtiene el tamaño en bytes del tipo/objeto para reservar o copiar su estructura completa',
    'getProperty':'consulta una propiedad por nombre con un valor de respaldo si falta',
    'parse':'analiza el documento de configuración local antes de validar proyecto y paquete',
    'load':'carga propiedades desde un flujo de archivo local sin publicar valores',
    'memoriaPersistente.begin':'abre un espacio NVS de simulación o físico; false permite escritura, no significa que la operación falló'})

CALLS.update({
    'setPinsInverted':'primer true invierte DIR y segundo true invierte STEP; la inversión de habilitación conserva su valor predeterminado, como en el montaje original',
    'xTaskCreatePinnedToCore':'crea tareaFirebase con nombre firebase, pila de 16384 bytes, sin argumento, prioridad 1, sin handle externo y fijada al núcleo 0; se exige pdPASS',
    'free':'libera el texto duplicado de la cola después de analizarlo; ArduinoJson 7 conserva sus propias cadenas, y un envío fallido también libera su copia'})

# Vocabulario de V2: se carga antes de generar las tablas, sin cambiar fuentes de aplicación.
FILES.update(study_v2.FILES)
TERMS.update(study_v2.TERMS)
CALLS.update(study_v2.CALLS)

LIBRARIES.update({'Wire.h':'bus I2C del LCD en una tarea separada del motor','memory':'unique_ptr administra automáticamente el arreglo temporal de dosis','new':'nothrow permite detectar falta de memoria sin iniciar movimiento'})
ATTRIBUTES.update({'android:visibility':'gone retira la vista y su espacio; el código muestra el botón clásico solo cuando falta el puente seguro','android:layout_weight':'reparte el espacio restante; el WebView recibe el alto disponible en la envoltura XML','android:fitsSystemWindows':'ajusta el contenedor respecto a barras del sistema en las plataformas que aplican este atributo'})

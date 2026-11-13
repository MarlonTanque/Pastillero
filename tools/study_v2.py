"""Explicaciones del frontend y vocabulario concreto del protocolo V2 para las guías."""
import re

FILES = {
    'generate_private_firmware.py': 'materializa siete valores locales en la única fuente pública, respalda cambios anteriores y reemplaza la copia privada de forma completa',
    'test_private_firmware.py': 'prueba doce casos de generación, validación y conservación de código usando datos ficticios, sin leer contraseñas reales',
    'read_kali_references.py': 'lee solo sketches del disco VDI abierto en rb, compara dos lecturas y guarda copias privadas sin cambiar los originales',
    'validate_android_emulators.py': 'instala y prueba el APK únicamente en los dos AVD del proyecto, verifica sus nombres y cierra solo los que inició',
    'verify_unification.py': 'compara instrucciones y clases con el respaldo, comprueba Room intacto, fuente única y ausencia de cabeceras propias',
    'finalize_continuation.py': 'exige cierres aprobados, comprueba fuentes y respaldos, normaliza logs y actualiza resultados, guías y huellas después de las dos compilaciones; nunca acciona hardware',
    'snapshot_test.cpp': 'prueba los mismos auxiliares de instantáneas que usa Preferences, con un doble en RAM y JSON mayor de 4000 bytes; no comprueba la flash física',
    'ContractFixtureTest.java': 'genera dos programas de ensayo con ScheduleEngine real: uno futuro y otro que representa una caché anterior, exclusivamente para integración local',
    'contract_controller.cpp': 'adapta JSON del emulador al mismo Controller y serializador/reserva del .ino, capturando destinos del NEMA sin GPIO',
    'event_json_test.cpp': 'comprueba que identificadores y claves reservadas se copien y sobrevivan a reutilización de memoria y serialización',
    'contract.integration.test.mjs': 'conecta las fixtures Java, reglas del emulador y controlador C++ de PC para probar eventos, permisos, reintentos y errores sin producción',
    'validate-integration.ps1': 'compila adaptadores de PC, regenera fixtures Java y ejecuta la integración solo en Firebase Emulator local',
    'DashboardActivity.java': 'aloja React en un WebView HTTPS local, valida origen y abre autenticación exclusivamente nativa',
    'DashboardRepository.java': 'coordina Room, permisos, programa V2, telemetría e historial sin entregar credenciales a JavaScript',
    'BridgeProtocol.java': 'valida tamaño, versión, origen, marco principal, acciones y tipos de cada mensaje React → Java',
    'ScheduleEngine.java': 'expande pautas independientes a fechas UTC con identidad determinista, zona horaria y límites explícitos',
    'ProgramWorker.java': 'publica la cola V2 en una transacción por revisión y token; conserva una edición posterior al acuse',
    'Medication.java': 'define una pauta Room con nombre, zona, horas o intervalo, vigencia y compartimento útil',
    'DevicePreferences.java': 'persiste cinco posiciones por defecto y preferencias que no anulan los bloqueos locales del firmware',
    'ProgramOutbox.java': 'separa edición local, solicitud de publicación y acuse del programa V2 del borrador histórico V1',
    'RoomVersionTwoTest.java': 'comprueba migración 3→4, reapertura de tablas V2 y conservación de historial al borrar una pauta',
    'DashboardBridgeTest.java': 'ejecuta React → mensajes por origen → Java → Room en el APK real de un emulador de QA moderno',
    'LegacyWebViewTest.java': 'comprueba la alternativa clásica segura cuando el proveedor WebView no admite el puente restringido por origen',
    'VersionTwoTest.java': 'prueba recurrencias, cambios de fecha, zonas horarias, identidades y validación estricta del puente',
    'version2_test.cpp': 'prueba cinco posiciones, retorno tras cada entrega y modelos de sensor, LCD, servo, bomba e indicadores sin GPIO',
    'App.tsx': 'construye las cinco vistas React, formularios, calendario real, temas y reconciliación mediante mensajes a Java',
    'api.ts': 'correlaciona solicitudes y respuestas por ID con límite de espera; no autentica ni abre Firebase desde JavaScript',
    'preview.ts': 'permite estudiar la interfaz en un navegador con almacenamiento local explícitamente identificado como demostración',
    'calendar.ts': 'calcula semanas locales y etiquetas; una fecha pasada sin evento se presenta sin registro y no como toma omitida confirmada',
    'types.ts': 'declara los tipos TypeScript del contrato visible; el compilador detecta usos inconsistentes sin sustituir la validación Java',
    'Icon.tsx': 'dibuja iconos SVG propios mediante trazos y atributos, sin descargar imágenes o bibliotecas de iconos remotas',
    'main.tsx': 'monta el componente App en el nodo root de la página empaquetada',
    'tokens.css': 'centraliza colores, superficies y variantes claro/oscuro mediante variables CSS',
    'styles.css': 'define disposición adaptable, tarjetas de vidrio, navegación, formularios, foco y reducción de animaciones',
    'App.test.tsx': 'comprueba interacciones React, persistencia de demostración, navegación, formularios y reconciliación con puente simulado',
    'api.test.ts': 'comprueba mensajes, rechazo, espera máxima y separación entre demostración y autenticación nativa',
    'calendar.test.ts': 'comprueba fechas reales, semanas, años bisiestos, estados e identificadores',
    'dashboard.spec.ts': 'recorre la interfaz en navegador de escritorio y móvil, incluyendo persistencia, teclado y movimiento reducido',
    'vite.config.ts': 'empaqueta exclusivamente los recursos propios dentro de app/src/main/assets/dashboard',
    'vitest.config.ts': 'configura las pruebas React y de fechas en un DOM simulado',
    'playwright.config.ts': 'configura pruebas de navegador de escritorio y Pixel 7 contra el servidor local de vista previa',
}

TERMS = {
    'CONFIG_LOCAL': 'marca de las siete declaraciones que el generador puede sustituir; no autoriza cambiar el resto del programa',
    'SNAPSHOT_MAX_BYTES': 'límite local de 48000 bytes del JSON persistente; es diferente de la capacidad física de la partición NVS',
    'capacity': 'número de bytes disponibles en el búfer de lectura, incluyendo el espacio necesario para el terminador cero',
    'positions': 'número de espacios totales: cinco por defecto, con cero vacío y cuatro espacios de dosis',
    'medicationId': 'identidad de la pauta, diferente del ID de cada ocurrencia y de cada evento',
    'horizonDays': 'ventana explícita publicada, de uno a siete días; no hay renovación ilimitada automática',
    'intervalMinutes': 'separación entre ocurrencias de esta pauta, anclada en su propia fecha startAt',
    'timesJson': 'arreglo de una a seis horas HH:mm de una pauta diaria, conservado como texto en SQLite',
    'zoneId': 'zona IANA usada al convertir una hora local de la pauta a un instante UTC',
    'edited': 'existen cambios locales todavía no preparados para publicar',
    'MAX_DEVICE_DOSES': 'máximo explícito de 96 ocurrencias por programa; excederlo produce error, no truncamiento',
    'PIN_EXIT': 'GPIO35: sensor independiente de salida, con señal de 3.3 V y polarización externa',
    'PIN_SERVO': 'GPIO13: PWM previsto para servo; disponibilidad local deshabilitada por defecto',
    'PIN_PUMP': 'GPIO23: señal a una etapa de potencia de bomba opcional, nunca alimentación directa',
    'PIN_SDA': 'GPIO21: datos I2C del LCD mediante una interfaz de nivel adecuada',
    'PIN_SCL': 'GPIO22: reloj I2C del LCD mediante una interfaz de nivel adecuada',
    'DEFAULT_POSITIONS': 'cinco espacios del montaje confirmado; setup aplica esta geometría antes de evaluar dosis',
    'NO_EXIT': 'alerta de ausencia de pulso válido al volver al cero; no es confirmación de ingestión',
    'WEB_MESSAGE_LISTENER': 'capacidad del proveedor WebView para limitar un puente al origen HTTPS permitido',
    'ORIGIN': 'https://appassets.androidplatform.net: origen local del APK, no un servidor accesible por Internet',
    'BadiNative': 'puente de mensajes inyectado por WebViewCompat solo en el origen autorizado',
    'weekStart': 'fecha inicial de la semana seleccionada; no se reemplaza por hoy al editar una pauta',
}

CALLS = {
    'configurarContenidoLocal': 'agrupa la configuración HTTPS local, bloqueo de recursos externos y rechazo de errores TLS del WebView',
    'registrarPuenteSeguro': 'registra los mismos mensajes restringidos por origen, marco, acciones y tipos antes de delegar al repositorio',
    'observarDatosLocales': 'conecta observadores de Room y autorización con las actualizaciones de pantalla, sin consultar SQL en el hilo principal',
    'configurarBotonAtras': 'delega Atrás a la navegación React y luego al historial o cierre de la Activity',
    'solicitarPermisoNotificaciones': 'solicita el permiso de notificaciones según versión y estado, conservando la marca de solicitud previa',
    'atenderDispensacion': 'ejecuta el mismo bloque extraído de loop: avance de Controller y detección de confirmación recién registrada',
    'isKey': 'consulta si existe una clave en Preferences o en su doble de RAM; no elimina ni crea el dato',
    'getUChar': 'lee un byte numérico persistido, con el valor de respaldo indicado si no existe',
    'putUChar': 'guarda un byte numérico y devuelve cuántos bytes escribió; el marcador usa valor 2 y exige retorno 1',
    'putBytes': 'guarda un bloque de bytes, apto para el JSON mayor que una cadena NVS; devuelve la cantidad escrita',
    'getBytesLength': 'consulta la longitud de un bloque antes de reservar memoria; no deserializa su contenido',
    'getBytes': 'copia los bytes persistidos al búfer acotado y devuelve cuántos leyó',
    'memchr': 'busca un byte en una región de longitud conocida; aquí detecta ceros internos antes de interpretar JSON como cadena',
    'snapshotSource': 'elige el blob nuevo antes que la cadena anterior y bloquea la recuperación si existe un marcador sin bloque, evitando recuperar reservas obsoletas',
    'saveSnapshotBlob': 'limita el JSON a 48000 bytes y exige escritura completa del blob y de su marcador antes de aceptar una reserva',
    'snapshotBlobSize': 'consulta el tamaño del bloque nuevo y rechaza longitudes vacías o superiores al límite local',
    'readSnapshotBlob': 'exige espacio para terminador, lectura completa y ausencia de ceros internos antes de interpretar el JSON',
    'writeDoseEvent': 'escribe el evento con copias de los identificadores; el cast a const char* evita tratar arreglos reutilizables como literales estáticos en ArduinoJson 7.3.2',
    'reserveDoseId': 'reserva la clave de dosis con copia propia en el documento JSON, para que otra dosis no cambie una reserva anterior',
    'expand': 'genera ocurrencias deterministas de cada pauta dentro de la ventana y rechaza desbordar el límite',
    'geometry': 'acepta cuatro o cinco posiciones solo estando detenido y obliga a recalibrar tras un cambio',
    'refreshAuthorization': 'abre o cierra el listener V2 según el permiso y vínculo ya comprobados por el repositorio nativo',
    'importProgram': 'convierte el programa remoto a pautas Room respetando una edición local pendiente',
    'reconcile': 'recarga o conserva pautas locales por elección explícita, tomando la revisión remota como base',
    'acknowledgeProgram': 'limpia la cola solo si su token coincide con el programa confirmado; no toca una edición más reciente',
    'addWebMessageListener': 'registra el receptor solo para el origen permitido y valida además marco principal y contenido',
    'setAllowFileAccess': 'false impide que el WebView lea rutas file del sistema',
    'setAllowContentAccess': 'false impide que la página acceda a proveedores content del teléfono',
    'shouldInterceptRequest': 'sirve recursos empaquetados del origen permitido y rechaza solicitudes externas con 403',
    'evaluateJavascript': 'invoca un callback fijo con datos escapados; nunca ejecuta una orden JavaScript recibida de Firebase',
    'nameUUIDFromBytes': 'deriva un ID estable de pauta, instante y compartimento para que un reintento no duplique una dosis',
    'getValidOffsets': 'detecta horas locales inexistentes por un cambio estacional antes de programar una ocurrencia',
    'plusDays': 'avanza días de calendario, respetando cambios de mes, año y duración local del día',
    'queueV2': 'guarda PING o APPLY_PLAN para la ruta V2; no permite una orden remota de dispensación',
    'ledcAttach': 'prepara PWM de servo a 50 Hz y 16 bits solo en la variante física con disponibilidad local',
    'ledcWrite': 'actualiza el ciclo útil PWM; cero desactiva la señal cuando el servo no está habilitado',
    'lcd': 'construye dos líneas de hasta 16 caracteres; la tarea I2C transmite el cuadro aparte del motor',
    'useState': 'conserva estado de pantalla; cambiarlo solicita a React volver a dibujar las partes afectadas',
    'useEffect': 'registra un efecto tras renderizar y usa su retorno para retirar listeners o callbacks al cerrar',
    'useRef': 'mantiene la referencia a un elemento sin provocar un nuevo renderizado al cambiarla',
    'request': 'envía una acción permitida al puente y espera una respuesta por ID, sin exponer Firebase a JavaScript',
    'listen': 'suscribe la pantalla a instantáneas nuevas y devuelve la función para desuscribirse',
    'setItem': 'guarda una preferencia o datos de demostración en localStorage; no publica en Firebase',
    'getItem': 'lee una preferencia o datos de demostración del navegador local',
    'postMessage': 'transmite JSON por el puente restringido; Java valida el mensaje antes de realizar la operación',
    'newId': 'crea un identificador aleatorio con crypto.getRandomValues para una pauta o solicitud',
    'dayKey': 'forma una clave de fecha local; evita agrupar un día distinto por convertirlo prematuramente a UTC',
    'monday': 'encuentra el lunes local de la semana de una fecha real',
    'doseStatus': 'consulta eventos reales; no inventa omisiones ni confirmaciones a partir de la hora por sí sola',
    'act': 'ejecuta la actualización React o acción de pantalla y permite comprobar su resultado',
}

def explain_web(code, filename):
    """Devuelve explicación propia del lenguaje; None deja actuar al lector general."""
    s = code.strip()
    reviewed={
        'i === 0 ? "slot zero" : i === next ? "slot active" : "slot"':'Escoge la clase del diagrama: cero vacío, posición de la próxima dosis o posición normal; compara índices sin mover el NEMA 17.',
        'initial || {':'Usa la pauta recibida al editar; si no existe, inicia el objeto con valores predeterminados que siguen debajo.',
        'Compartimento {i + 1}':'Muestra la etiqueta de posición útil: el índice de lista empieza en cero y se presenta sumando uno, reservando la posición física cero.',
        'data?.device.updatedAt && now - data.device.updatedAt < 30000;':'Completa la señal de frescura: exige timestamp existente y menos de treinta segundos de antigüedad; no confunde una instantánea antigua con conexión actual.',
        'Badi<small>Tu rutina, en orden.</small>':'Presenta el nombre de la app y su texto secundario; small es jerarquía tipográfica, no un dato del dispositivo.',
        'theme === "light" ? "Activar tema oscuro" : "Activar tema claro"':'Etiqueta accesible del botón: anuncia la acción que cambiará al otro tema, según el tema actual.',
        '{data.settings.positions - 1} de dosis':'Muestra posiciones totales menos el cero vacío: cinco espacios significan cuatro de dosis.',
        'historyFilter === "all" ||':'Comienza el filtro del historial: todas las filas cuando está seleccionado all, o solo las que cumplan el tipo comparado debajo.',
        'Registrada{" "}':'Muestra la palabra Registrada y añade un espacio explícito para separar la fecha que sigue.',
        'settings as unknown as Record<string, unknown>,':'Aserción de tipos para enviar el objeto como mapa de mensajes; no transforma datos ni reemplaza las comprobaciones estrictas de Java.',
        'm as unknown as Record<string, unknown>,':'Presenta la pauta al compilador como mapa de propiedades del mensaje; Java sigue validando nombres, rangos y tipos en tiempo de ejecución.',
        'Se retirará <strong>{deleting.name}</strong> de tus próximas':'Texto de confirmación de borrado de pauta: strong resalta su nombre escapado; la operación todavía espera el botón y no borra historial.',
        '{ length: 7 },':'Configura siete elementos para construir los siete días de una semana real.',
        'let data: Snapshot;':'Declara una variable local tipada para la instantánea de demostración; se carga del almacenamiento o se inicializa debajo.',
        'typeof payload.weekStart === "number" ? payload.weekStart : data.weekStart;':'Usa la semana solicitada solo si es numérica; si falta, conserva la seleccionada. typeof comprueba el tipo de ejecución en esta vista local.',
        '| "nativeView";':'Última alternativa del tipo unión Action; permite pedir la vista clásica y cierra la declaración TypeScript.',
    }
    if filename.endswith(('.ts','.tsx')) and s in reviewed:return reviewed[s]
    if filename.endswith('.css'):
        if s.startswith(('/*', '*')): return 'Comentario de estilo; explica el bloque y no cambia datos del pastillero.'
        if s.startswith('@media'): return 'Aplica el bloque únicamente al ancho de pantalla o preferencia de movimiento indicados; permite adaptar la interfaz y su accesibilidad.'
        if s.startswith('@keyframes'): return 'Declara etapas de una animación visual; no temporiza ni controla el motor.'
        if s == '}': return 'Cierra la regla o condición CSS anterior.'
        if s.endswith(',') and not ':' in s: return 'Añade este selector a la lista de elementos que compartirán el bloque CSS siguiente; la coma une selectores, no valores de datos.'
        if re.match(r'^[\w-]+\s+[\d.]+s',s): return 'Continúa la transición visual: nombra la propiedad y duración en segundos; la coma añade otra propiedad y el punto y coma cierra la declaración.'
        if s.endswith('{'): return 'Selecciona los elementos que coinciden con `'+s[:-1].strip()+'`; las propiedades siguientes cambian su presentación, no su información.'
        if ':' in s:
            prop, value = s.split(':', 1)
            meanings = {'display':'tipo de disposición', 'grid-template-columns':'columnas de la cuadrícula', 'gap':'separación entre elementos', 'padding':'espacio interior', 'margin':'espacio exterior', 'position':'referencia de colocación', 'bottom':'distancia al borde inferior', 'background':'superficie o gradiente', 'color':'color del texto', 'border-radius':'redondeado de esquinas', 'backdrop-filter':'desenfoque del fondo del vidrio', 'box-shadow':'sombra de profundidad', 'transition':'cambio visual progresivo', 'animation':'secuencia visual', 'outline':'indicador de foco', 'font-size':'tamaño del texto', 'min-height':'altura mínima', 'overflow':'tratamiento del contenido que excede la caja', 'z-index':'orden de superposición'}
            return 'Configura '+meanings.get(prop, 'la propiedad visual `'+prop+'`')+' en `'+value.rstrip(';')+'`. '+('Es una variable CSS reutilizable por var(); el tema puede sustituirla.' if prop.startswith('--') else 'px es tamaño CSS, rem depende de la fuente raíz y % depende del contenedor; var() toma un valor del tema cuando aparece.')
    if filename.endswith(('.ts', '.tsx')):
        if s=='<>': return 'Abre un fragmento React: agrupa elementos hermanos sin añadir un contenedor HTML extra.'
        if s.startswith('{') and re.match(r'^\{(?:view|next|data|m\.|e\.|k|busy)',s): return 'Inicia una expresión JSX con el dato escrito; las líneas siguientes completan su condición, recorrido o formato. La apertura { se cierra al terminar ese contenido dinámico.'
        if s.startswith('{') and ('...' in s or 'name:' in s): return 'Construye el objeto escrito copiando propiedades con ... cuando aparece; en pruebas define un perfil/ejemplo explícito y no evidencia de una dispensación real.'
        if s.startswith('action === '): return 'Compara la acción con una operación reservada al APK. Los || siguientes agrupan los casos que la demostración de navegador rechaza porque no tiene puente nativo.'
        if s in ('>', '/>'): return 'Termina la apertura JSX; /> también cierra el elemento sin hijos. Los atributos de las líneas anteriores pertenecen a este mismo control.'
        if s.startswith('...'): return 'Expande las propiedades/elementos escritos en el objeto/arreglo actual; los valores posteriores del mismo objeto pueden sustituir una propiedad previa.'
        field=re.match(r'^(\w+)(\?)?:\s*(.*)',s)
        if field:
            key,optional,value=field.groups()
            if filename=='Icon.tsx': return 'Asocia el icono `'+key+'` con comandos de trazado SVG: M/m mueve, L/l dibuja segmento, H/V horizontal/vertical, C/c curva y Z cierra. Son coordenadas visuales, no pasos del NEMA 17.'
            type_value=value.rstrip(',;')
            if re.match(r'^(?:string|number|boolean|ReactNode|Snapshot|Settings|Medication|Occurrence|DoseEvent|View|Action)(?:\[\])?$',type_value) or filename=='types.ts':
                return 'Campo TypeScript `'+key+'`'+(' opcional' if optional else '')+' de tipo `'+type_value+'`. '+TERMS.get(key,'Describe el dato que intercambian los componentes; [] es una lista y | permite las alternativas escritas')+'. No crea ni guarda una fila por declararlo.'
            meanings={'id':'identificador estable', 'name':'nombre visible', 'label':'etiqueta del control', 'icon':'nombre del icono SVG', 'testDir':'carpeta de casos del navegador', 'workers':'cantidad de procesos simultáneos de pruebas', 'fullyParallel':'permiso de ejecutar casos en paralelo', 'baseURL':'dirección local base de pruebas', 'trace':'condición para guardar trazas de fallo', 'webServer':'servidor local que se inicia para probar', 'command':'instrucción de inicio del servidor de vista previa', 'url':'dirección esperada para considerar listo el servidor', 'reuseExistingServer':'si puede reutilizar un servidor anterior', 'projects':'perfiles de escritorio y móvil', 'viewport':'dimensiones CSS de la ventana de prueba', 'path':'archivo de captura de pantalla', 'fullPage':'captura toda la página desplazable', 'reporter':'formatos de informe de pruebas', 'setupFiles':'preparación común de pruebas', 'environment':'entorno DOM simulado', 'include':'patrones de archivos incluidos', 'outDir':'destino confinado de recursos web generados', 'emptyOutDir':'limpieza solo del directorio de assets generado', 'host':'interfaz local de escucha del servidor', 'port':'puerto local de desarrollo', 'day':'formato del número de día', 'month':'formato del mes mostrado'}
            return 'Propiedad `'+key+'`: '+meanings.get(key,TERMS.get(key,'dato del objeto que se construye'))+'. El valor `'+value+'` se interpreta dentro de ese objeto; no ejecuta por sí mismo una operación Firebase.'
        if s.startswith('{') and re.search(r'\bid:',s): return 'Elemento de la lista de navegación: asocia identidad de vista, etiqueta en español e icono. Las llaves delimitan el objeto y la coma separa la siguiente opción.'
        if s.startswith('{') and s.endswith('}'): return 'Inserta en JSX el resultado de la expresión entre llaves. React escapa las cadenas al mostrarlas; || usa la alternativa si falta un valor y ?: elige entre dos opciones cuando aparecen.'
        if s.startswith('await '): return 'Espera la promesa de la operación indicada y continúa el encadenamiento de las líneas siguientes. Cede ejecución durante la espera; en estas pruebas permite observar el resultado real antes de afirmar éxito.'
        if s.startswith('declare global'): return 'Amplía los tipos de Window para declarar los callbacks del puente; no concede ni crea un puente nativo en una página no autorizada.'
        if s.startswith(('?', ':')): return 'Continúa una selección condicional: ? introduce el caso verdadero y : el alternativo. El valor se usa como etiqueta, estilo o dato del control que abrió la expresión.'
        if s.startswith(('import ', 'export type ', 'interface ', 'type ')):
            return 'Declara/importa los símbolos o tipos escritos: TypeScript comprueba su uso al compilar; esto no concede permisos nativos ni abre una conexión a Firebase.'
        if re.match(r'^</', s): return 'Cierra el componente o elemento visual anterior y continúa el árbol JSX.'
        if re.match(r'^<[A-Za-z]', s):
            tag = re.match(r'^<([A-Za-z][\w.]*)', s)[1]
            return 'Construye `'+tag+'` dentro del árbol React. Una etiqueta minúscula es HTML/SVG y una mayúscula llama un componente propio; las llaves insertan datos como texto, no como HTML ejecutable.'
        if re.match(r'^(className|aria-[\w-]+|role|type|value|checked|disabled|on\w+|htmlFor|tabIndex|ref|key|style)\s*=', s):
            key = s.split('=', 1)[0].strip()
            why = 'enlaza un evento a una función que se ejecutará después de la interacción' if key.startswith('on') else 'relaciona etiqueta y control' if key == 'htmlFor' else 'aporta información de accesibilidad' if key.startswith('aria-') or key == 'role' else 'asigna estilo, identidad, estado o valor del control según el atributo'
            return 'Atributo JSX `'+key+'`: '+why+'. La expresión entre llaves se evalúa con el estado actual; un texto entre comillas es literal.'
        if '=>' in s: return 'Define una función flecha con los parámetros escritos y el resultado/bloque siguiente. Registrarla como evento no ejecuta todavía su cuerpo; map/filter sí la invocan al recorrer datos.'
        if s.startswith(('export function ', 'function ', 'async function ')): return 'Define una función/componente con nombre y parámetros; su cuerpo sigue debajo. async devuelve una promesa y await cede la espera sin bloquear la pantalla.'
        if s.startswith(('it(', 'test(')): return 'Declara un caso automatizado con su descripción y función; las expectativas siguientes deben cumplirse para aprobar.'
        if not re.search(r'[;=(){}<>]',s) and not s.startswith(('import','export','//')): return 'Texto o fragmento literal del componente JSX: se presenta a la persona dentro del control contenedor, sin convertirse en JavaScript ni en una orden del motor.'
    if filename.endswith('.html'):
        if s.startswith('<!doctype'): return 'Declara HTML moderno para que el WebView use el modo de representación estándar.'
        if s.startswith('</'): return 'Cierra la sección HTML nombrada y devuelve la jerarquía al elemento padre.'
        if s.startswith('<'): return 'Abre el elemento HTML escrito: head agrupa metadatos y CSP, body contiene root y el script propio; title fija el nombre de página. No abre Firebase.'
        if s=='/>': return 'Cierra la etiqueta de metadatos cuyos atributos aparecieron arriba.'
    return None

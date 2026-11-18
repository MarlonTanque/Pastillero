"""Produce guías verificables usando los números finales; nunca publica configuración privada."""
from pathlib import Path
import hashlib
import json
import re
import io
import tokenize
from study_explanations import FILES, TERMS, CALLS, LIBRARIES, explain
from study_notes import note_for

ROOT=Path(__file__).resolve().parents[1]
PREFIX='// Estudio: '
TRANSLATIONS={
    'Check the UID binding before importing SDK cache into this user\'s Room scope.':'Verificar el vínculo del UID antes de importar la caché al historial Room de esta cuenta.',
    'A readable access record is not a grant: also verify the device binding.':'Poder leer el permiso propio no concede acceso: también se verifica el vínculo al dispositivo.',
    'The same draft may already have committed before a process restart.':'El mismo borrador pudo confirmarse antes de un reinicio; su token permite reconocerlo.',
    'Suppress speculative local listener events; Room is the durable outbox.':'No emitir cambios locales especulativos: Room conserva la cola hasta el acuse remoto.',
    'A timed-out write may already exist remotely. Check it before expiring locally.':'Una escritura sin acuse pudo llegar al servidor: comprobarla antes de declararla caducada.',
    'Room is the durable outbox; retries always use the same cloud key and payload.':'Room conserva la cola; los reintentos mantienen la misma clave y el mismo contenido.',
    'No GPIO pulses or sensor reads in the default build. Never upload during software QA.':'La compilación predeterminada no genera pulsos ni lee sensores físicos. No cargar firmware durante estas pruebas.',
    'Validate polarity and threshold on the real sensor.':'Comprobar polaridad y umbral con el sensor real en la fase física autorizada.',
    'Must divide by four; recalibrate after changing microstepping.':'Debe ser divisible entre cuatro; recalibrar si cambia el microstepping.',
    'Host only, e.g. project-default-rtdb.firebaseio.com; no scheme or slash.':'Solo dominio, por ejemplo project-default-rtdb.firebaseio.com, sin protocolo ni barra.',
    'LOCAL ONLY: excluded from Git; never share compiled firmware with credentials.':'SOLO LOCAL: excluido de Git; no compartir binarios que incorporen estas credenciales.',
}

def redact(path,line):
    private=path.name=='secrets.h' or path.name in ('google-services.json','firebase-config.properties','local.properties')
    if not private: return line
    if path.name=='secrets.h':
        return re.sub(r'^(\s*#define\s+\w+)(?:\s+.*)?$',r'\1 [VALOR LOCAL OMITIDO]',line)
    if path.suffix=='.properties':
        return line.split('=',1)[0]+'=[VALOR LOCAL OMITIDO]' if '=' in line and not line.lstrip().startswith('#') else line
    return re.sub(r'("(?:current_key|api_key|oauth_client|client_secret|private_key)"\s*:\s*).*',r'\1[VALOR OMITIDO]',line)

def annotate():
    """Inserta solo notas revisadas; los detalles de cada línea se conservan en las tablas."""
    import textwrap
    files=[*ROOT.joinpath('app/src').rglob('*.java'),ROOT/'firmware/PastilleroESP32/PastilleroESP32.ino',
           *ROOT.joinpath('firmware/PastilleroESP32').glob('*.h'),ROOT/'build.gradle',ROOT/'settings.gradle',ROOT/'app/build.gradle']
    for path in files:
        lines=[line for line in path.read_text(encoding='utf-8-sig').splitlines()
               if not line.lstrip().startswith((PREFIX,'// Lectura: '))]
        out=[];raw=False;block=False;macro=False
        for line in lines:
            for old,new in TRANSLATIONS.items(): line=line.replace(old,new)
            stripped=line.strip()
            if macro or raw:
                out.append(line)
                if macro: macro=line.rstrip().endswith(chr(92))
                if raw and ')PEM"' in line: raw=False
                continue
            if stripped.startswith('/*'): block='*/' not in stripped
            if block or stripped.startswith(('//','/*','*')):
                out.append(line)
                if '*/' in stripped: block=False
                continue
            note=note_for(path.name,stripped)
            if stripped.startswith('#include'):
                name=stripped.split('include',1)[1].strip(' <>"')
                note=LIBRARIES.get(name,FILES.get(name))
            if note:
                indent=line[:len(line)-len(line.lstrip())]
                out.extend(indent+'// Lectura: '+part for part in textwrap.wrap(note,width=max(65,108-len(indent)),break_long_words=False,break_on_hyphens=False))
            out.append(line)
            if 'R"PEM(' in line: raw=True
            if stripped.startswith('#') and line.rstrip().endswith(chr(92)): macro=True
        path.write_text('\n'.join(out)+'\n',encoding='utf-8')

def inventory():
    arduino=[p for p in ROOT.joinpath('firmware/PastilleroESP32').iterdir() if p.suffix in ('.ino','.h','.csv')]
    arduino.append(ROOT/'firmware/firmware.local.example.json')
    arduino+=list(ROOT.joinpath('tests').glob('*.cpp'))+list(ROOT.joinpath('tests').glob('*.py'))
    arduino+=list(ROOT.joinpath('original').glob('*.ino'))+list(ROOT.joinpath('original').glob('*.txt'))
    android=[p for p in ROOT.joinpath('app/src').rglob('*') if p.suffix in ('.java','.xml')]
    android+=[ROOT/'build.gradle',ROOT/'settings.gradle',ROOT/'app/build.gradle',ROOT/'gradle.properties',
              ROOT/'gradle/wrapper/gradle-wrapper.properties',ROOT/'firebase-config.example.properties',
              ROOT/'firebase-config.properties',ROOT/'local.properties',ROOT/'app/google-services.json',ROOT/'.gitignore',
              ROOT/'third_party/esp-provisioning/build.gradle',
              ROOT/'third_party/esp-provisioning/src/main/java/com/espressif/provisioning/PrivateLog.java',
              ROOT/'third_party/esp-provisioning/src/main/java/com/espressif/provisioning/SecureCapabilities.java']
    for folder in ('firebase','admin-backend','tools'):
        android += [p for p in ROOT.joinpath(folder).glob('*') if p.suffix in ('.mjs','.json','.py','.ps1') and p.name!='package-lock.json']
    # Solo fuentes propias: no se duplica el bundle generado ni las dependencias de npm.
    android += [p for p in ROOT.joinpath('web').rglob('*')
                if p.is_file() and p.suffix in ('.ts','.tsx','.css','.html','.json')
                and not any(x in p.relative_to(ROOT/'web').parts for x in ('node_modules','test-results','playwright-report'))
                and p.name!='package-lock.json']
    return sorted(set(arduino)),sorted(set(p for p in android if p.is_file()))

def method_context(lines):
    result={};depth=0;stack=[];pending=None
    for number,line in enumerate(lines,1):
        s=line.strip()
        if s.startswith(('//','/*','*','#')):
            result[number]=stack[-1][0] if stack else 'declaraciones del archivo';continue
        clean=re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//.*','',s)
        names=re.findall(r'\b([A-Za-z_]\w*)\s*\(',clean)
        if re.match(r'(?:public |private |protected |static |inline |explicit |async |def |void |bool |int |String |long |size_t |const )',clean) and names and '=' not in clean.split('(',1)[0]:
            candidate=names[0]
            if candidate not in ('if','for','while','switch') and not clean.rstrip().endswith(';'): pending=candidate+'()'
        if pending and '{' in clean:
            stack.append((pending,depth+1));pending=None
        result[number]=stack[-1][0] if stack else (pending or 'declaraciones del archivo')
        depth+=clean.count('{')-clean.count('}')
        while stack and depth<stack[-1][1]:stack.pop()
    return result

def cell(text): return str(text).replace('|','\\|').replace('\n','<br>')

def source_cell(text):
    # Inline code already protects XML angles; a longer delimiter preserves literal backticks.
    fence='`'*(max((len(x) for x in re.findall(r'`+',text)),default=0)+1)
    return fence+' '+cell(text)+' '+fence

def generate():
    groups=inventory();manifest=[];fallback=[]
    common='''La carpeta base es `C:\\Users\\milit\\AndroidStudioProjects\\PastilleroBadi`.

Cada tabla sigue el **orden físico final** de su archivo. `L` es la línea que muestra el editor. Se incluyen instrucciones, continuaciones, comentarios y cierres; las líneas vacías solo separan visualmente. Una instrucción dividida ocupa varias filas: léela desde la apertura hasta el punto y coma/cierre. El campo de componentes descompone tipos, variables, llamadas, comparaciones y unidades de esa línea. Las contraseñas, tokens y valores privados no se reproducen.

Para estudiar: 1) lee la finalidad del archivo; 2) localiza el método; 3) recorre las filas en orden; 4) comprueba entradas, decisión y salida. `=` asigna; `==` compara; `!` niega; `&&` exige ambas condiciones; `||` permite una; `objeto.metodo()` llama una operación. Los paréntesis agrupan argumentos; las llaves agrupan bloques; `;` termina una instrucción. En C++, `&` en un parámetro es una referencia al objeto original; en una expresión `&m` obtiene la dirección de m, `*` declara/accede mediante un puntero y `[]` indexa un arreglo. En Java una lambda `x -> ...` es una función que se ejecutará cuando se invoque su callback, no necesariamente al registrarla.

La herramienta `python tools/generate_study_guides.py --verify` compara huellas y cobertura con los archivos actuales. No modifica fuentes al verificar. Los certificados PEM son datos públicos, no instrucciones: cada línea del bloque está identificada sin copiar su contenido. La implementación generada por Room, Gradle Wrapper, bibliotecas, SDK, archivos de compilación, esquemas exportados y lockfiles no son código fuente escrito para esta app y no se reescriben; se explican sus funciones en las guías temáticas. `private/` contiene datos de ejecución, no una segunda aplicación.

Glosario para leer las tablas: `public` expone un miembro; `private` lo reserva a su clase; `protected` permite el acceso previsto por herencia/paquete. `final` impide reasignar una variable (no vuelve inmutable todo su objeto), y en clases impide heredar. `static` en Java pertenece a la clase. `void` significa que un método no devuelve un valor; `null` representa ausencia de objeto. `new` construye un objeto. Una interfaz define operaciones y una clase concreta las implementa. `@Override` comprueba una operación heredada. En C++, `auto` deja inferir el tipo y `{}` inicializa valores; un arreglo `char id[37]` reserva espacio para hasta 36 caracteres y su terminador cero. Una función recibe parámetros y puede devolver un valor; registrar un callback no ejecuta su cuerpo inmediatamente.

'''
    for group,(title,name) in zip(groups,[('Guía Arduino línea por línea','GUIA_ARDUINO_LINEA_POR_LINEA.md'),('Guía Android línea por línea y anexos técnicos','GUIA_ANDROID_LINEA_POR_LINEA.md')]):
        intro='# '+title+'\n\n'+common+'Versión vigente: APK 2.1-wifi-simulacion, Room 4 y protocolo program.version=2. El montaje de producción tiene cinco espacios (cuatro útiles y cero vacío), con 640 pasos por separación. El perfil histórico V1 conserva cuatro espacios y las pruebas originales. Para la arquitectura y límites consulta VERSION_2_IMPLEMENTACION.md.\n\n'
        if 'ARDUINO' in name:
            intro+='El `.ino` contiene librerías, configuración visible, certificados TLS, pines, máquina de estados y funciones en 17 secciones. La copia privada se genera desde esa misma fuente con tools/generate_private_firmware.py y valores de private/firmware.local.json; no mantiene otra implementación. No hay cabeceras propias ni credenciales reales en el sketch público. partitions.csv conserva el formato requerido por Arduino para la flash. Las clases existentes de control y adaptadores se mantienen dentro del .ino por compatibilidad con pruebas y con Stream; no se añadieron clases nuevas. El sketch de original/ es referencia histórica y no se ejecuta en QA.\n\n'
        else:
            intro+='Se recorre Android (Java de producción, XML y pruebas), Gradle/configuración, Firebase, backend administrativo, herramientas y todas las fuentes React/TypeScript/CSS propias de web/. Estos anexos completan el inventario de fuentes del proyecto y no sustituyen la organización de Activities, Room y Workers. Para la defensa V2 sigue App.tsx → DashboardActivity/BridgeProtocol → DashboardRepository → DAO/entidades → ScheduleEngine/ProgramWorker; MainActivity y Repository conservan compatibilidad V1, y consulta el detalle de cada callback según aparezca.\n\n'
            intro+='Ciclo de vida: PastilleroApp.onCreate configura el proceso; MainActivity.onCreate crea vistas/observadores; onSaveInstanceState guarda la fecha y onDestroy cierra su Repository. No se implementan overrides propios de onStart/onResume/onPause/onStop. Al recrearse se abre otro repositorio con el UID vigente, mientras Room conserva las filas. DatePicker y Calendar usan mes basado en cero; los selectores de fecha/hora fijan segundos y milisegundos a cero antes de guardar la fecha UTC. El Spinner de la vista clásica V1 conserva 1..3; la interfaz V2 usa cinco espacios y compartimentos 1..4. DashboardActivity aloja el puente local y Room usa esquema 4. Los callbacks Firebase no hacen bucles de espera en la pantalla: el disco se delega al ejecutor y la espera de acuse corresponde al Worker.\n\n'
        intro+='## Índice de archivos\n\n'+'\n'.join('- [`'+p.relative_to(ROOT).as_posix()+'`](#archivo-'+str(i)+')' for i,p in enumerate(group,1))+'\n\n'
        output=[intro]
        for file_index,path in enumerate(group,1):
            rel=path.relative_to(ROOT).as_posix();lines=path.read_text(encoding='utf-8-sig').splitlines()
            safe=[redact(path,line) for line in lines];contexts=method_context(safe)
            private=path.name in ('secrets.h','google-services.json','firebase-config.properties','local.properties')
            digest=hashlib.sha256(('\n'.join(safe)+'\n').encode()).hexdigest() if private else hashlib.sha256(path.read_bytes()).hexdigest()
            output.extend(['<a id="archivo-'+str(file_index)+'"></a>\n\n## `'+rel+'`\n\n',FILES.get(path.name,'Herramienta o configuración propia: se recorre cada instrucción en su orden, identificando el recurso y su uso en compilación, prueba o seguridad.')+'.\n\n',
                           'Líneas físicas: '+str(len(lines))+'. Huella '+('de la forma pública redactada' if private else 'SHA-256 de la fuente')+': `'+digest+'`.\n\n',
                           '| Línea final | Instrucción o dato | Qué hace y para qué sirve | Componentes y relación |\n|---:|---|---|---|\n'])
            # tokenize distingue texto multilínea de instrucciones Python incluso en esta herramienta.
            text_lines=set()
            if path.suffix=='.py':
                for token in tokenize.generate_tokens(io.StringIO('\n'.join(safe)+'\n').readline):
                    if token.type==tokenize.STRING and token.end[0]>token.start[0]:
                        text_lines.update(range(token.start[0],token.end[0]+1))
            covered=[];raw=False
            for number,line in enumerate(safe,1):
                if not line.strip():continue
                covered.append(number)
                if number in text_lines:
                    code=line.strip()
                    action='Parte de un literal Python multilínea: conserva exactamente este texto como contenido documental o plantilla. No ejecuta como código las palabras ni ejemplos incluidos; la asignación o docstring que lo contiene fija su uso.'
                    details=[]
                elif raw:
                    code='[Dato público del bloque PEM; contenido omitido]'
                    action='Continúa el certificado público de confianza usado por TLS; es texto de datos, no una instrucción de motor ni una credencial privada.'
                    details=['La biblioteca TLS interpreta el bloque BEGIN/END CERTIFICATE completo; no se cambia un fragmento de forma aislada.']
                    if ')PEM"' in line:
                        raw=False;code=')PEM";';action='Cierra el literal de cadena sin escapes que contiene los certificados públicos.'
                else:
                    code=line.strip();action,details=explain(code,path.name,contexts[number])
                    if 'R"PEM(' in line and not line.lstrip().startswith('//'): raw=True;code='static const char GOOGLE_ROOTS[] PROGMEM = R"PEM([datos públicos]'
                if action.startswith('Continúa la instrucción escrita'): fallback.append({'file':rel,'line':number,'code':code})
                relation='Ámbito: `'+contexts[number]+'`.'
                output.append('| '+str(number)+' | '+source_cell(code)+' | '+cell(action)+' | '+cell(' '.join(details)+' '+relation)+' |\n')
            output.append('\n')
            manifest.append({'file':rel,'guide':name,'physicalLines':len(lines),'coveredLines':covered,'sha256':digest,'redacted':private})
        (ROOT/'docs'/name).write_text(''.join(output),encoding='utf-8')
    (ROOT/'reports/study-source-coverage.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (ROOT/'reports/study-review-fragments.json').write_text(json.dumps(fallback,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Guías generadas:',len(manifest),'archivos;',sum(len(x['coveredLines']) for x in manifest),'líneas no vacías. Fragmentos sin vocabulario:',len(fallback))

def verify():
    records=json.loads((ROOT/'reports/study-source-coverage.json').read_text(encoding='utf-8'))
    expected={p.relative_to(ROOT).as_posix() for group in inventory() for p in group}
    assert expected=={x['file'] for x in records},'El inventario de fuentes cambió'
    for record in records:
        p=ROOT/record['file'];lines=p.read_text(encoding='utf-8-sig').splitlines()
        digest=hashlib.sha256(('\n'.join(redact(p,x) for x in lines)+'\n').encode()).hexdigest() if record['redacted'] else hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest==record['sha256'],record['file']+' cambió: regenerar referencias'
        assert record['physicalLines']==len(lines)
        assert record['coveredLines']==[i for i,x in enumerate(lines,1) if x.strip()],record['file']
        guide=(ROOT/'docs'/record['guide']).read_text(encoding='utf-8')
        section=guide.split('## `'+record['file']+'`\n',1)[1].split('\n## `',1)[0]
        assert [int(n) for n in re.findall(r'^\| (\d+) \|',section,re.M)]==record['coveredLines'],record['file']
    print('PASS: inventario completo, huellas y referencias finales de ambas guías coinciden.')

if __name__=='__main__':
    import sys
    if '--verify' in sys.argv: verify()
    else:
        if '--annotate' in sys.argv: annotate()
        generate()
        verify()

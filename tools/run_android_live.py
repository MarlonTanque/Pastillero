"""Run the opt-in Android Firebase SDK test only on this project's QA emulator.
Reads ignored properties, passes credentials in memory and never prints command arguments.
"""
from pathlib import Path
import json, os, shlex, subprocess
ROOT=Path(__file__).resolve().parents[1]
ADB=Path(os.environ['LOCALAPPDATA'])/'Android/Sdk/platform-tools/adb.exe'
SERIAL=os.environ.get('BADI_QA_SERIAL','emulator-5580')
report={'projectId':'pastillerobadi','serial':SERIAL,'hardwareUsed':False,'status':'PENDING'}
try:
    props={}
    for line in (ROOT/'private/integration.local.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1);props[key.strip()]=value
    assert all(props.get(role+'.'+field) for role in ('owner','device') for field in ('email','password'))
    avd=subprocess.check_output([str(ADB),'-s',SERIAL,'emu','avd','name'],text=True)
    assert SERIAL in ('emulator-5580','emulator-5582') and avd.splitlines()[0].strip() in ('PastilleroBadiQA','PastilleroBadiV2QA'),'Unexpected emulator'
    command=['am','instrument','-w','-e','class','mx.edu.badi.pastillero.FirebaseConnectionTest','-e','liveFirebase','true']
    for role in ('owner','device'):
        for field in ('email','password'):
            command+=['-e',role+field.title(),props[role+'.'+field]]
    command+=['mx.edu.badi.pastillero.test/androidx.test.runner.AndroidJUnitRunner']
    result=subprocess.run([str(ADB),'-s',SERIAL,'shell',shlex.join(command)],capture_output=True,text=True,timeout=180)
    output=result.stdout+result.stderr
    for role in ('owner','device'):
        output=output.replace(props[role+'.password'],'[REDACTED]')
    (ROOT/'reports/android-firebase-live.log').write_text(output,encoding='utf-8')
    report['status']='PASS' if result.returncode==0 and 'OK (2 tests)' in output else 'FAIL'
    report['testCases']=2
    report['limitations']=['SDK test on QA emulator; no MainActivity visual interaction','Device-role SDK result is simulated by this test, not ESP32 firmware',
        'SDK goOffline/goOnline tested; no radio/Wi-Fi outage','Only qa-* PING in simulation; no schedules or dose events written']
except Exception as error:
    report['status']='ERROR';report['errorType']=type(error).__name__
finally:
    (ROOT/'reports/firebase-setup/android-live.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Android Firebase SDK integration:',report['status'])
raise SystemExit(0 if report['status']=='PASS' else 1)

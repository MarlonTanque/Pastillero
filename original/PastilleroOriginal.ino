#include <AccelStepper.h>

const int pinPUL = 25;
const int pinDIR = 26;

AccelStepper motor(1, pinPUL, pinDIR);

const long pasosPorVuelta = 3200; 
const long totalCompartimentos = 4;
const long pasosPorCompartimento = pasosPorVuelta / totalCompartimentos; 

// Variables para la secuencia
int pastillaActual = 1;
const int pastillasADispensar = 3; 
bool sistemaCalibrado = false;
bool secuenciaActiva = false;
unsigned long tiempoAnterior = 0;
const unsigned long intervaloEspera = 15000; // 15 segundos entre pastillas

void setup() {
  Serial.begin(115200);
  delay(2000); 
 
  motor.setPinsInverted(true, true);

  motor.setMaxSpeed(1000);
  motor.setAcceleration(500);
  
  Serial.println("=====================================");
  Serial.println("        CALIBRACION DEL MOTOR        ");
  Serial.println("=====================================");
  Serial.println("Envía 'a' o 'r' para alinear el agujero 0 a la salida.");
  Serial.println("Envía 'c' para Confirmar Punto 0");
  Serial.println("=====================================");
}

void loop() {
  // CALIBRACIÓN INICIAL
  if (!sistemaCalibrado) {
    if (Serial.available() > 0) {
      char comando = Serial.read();
      
      // Movimientos para calibrar
      if (comando == 'a') motor.runToNewPosition(motor.currentPosition() + 10); 
      else if (comando == 'r') motor.runToNewPosition(motor.currentPosition() - 10); 
      else if (comando == 'c') {
        motor.setCurrentPosition(0); 
        sistemaCalibrado = true;
        Serial.println("\n✅ Punto 0 guardado. Envía 's' para Iniciar Secuencia de 3 pastillas.");
      }
    }
  } 
  
  // SECUENCIA DE DISPENSADO Y ESPERA
  else {
    if (!secuenciaActiva) {
      if (Serial.available() > 0 && Serial.read() == 's') {
        secuenciaActiva = true;
        pastillaActual = 1; 
        
        Serial.println("\n--- INICIANDO SECUENCIA ---");
        dispensarYRegresar(pastillaActual); 
        tiempoAnterior = millis(); 
      }
    } 
    else {
      unsigned long tiempoActual = millis();
      
      // Control de espera de 15 segundos entre cada entrega
      if (tiempoActual - tiempoAnterior >= intervaloEspera) {
        pastillaActual++; 
        
        if (pastillaActual > pastillasADispensar) {
          secuenciaActiva = false;
          Serial.println("\n--- SECUENCIA COMPLETA ---");
          Serial.println("Envía 's' si deseas repetir el proceso desde la pastilla 1.");
        } else {
          dispensarYRegresar(pastillaActual);
          tiempoAnterior = millis();
        }
      }
    }
  }
}

// Función que hace el recorrido de Ida y Vuelta
void dispensarYRegresar(int numeroPastilla) {
  long posicionDestino = numeroPastilla * pasosPorCompartimento;
  
  Serial.print("Girando hacia pastilla ");
  Serial.print(numeroPastilla);
  Serial.println("...");

  // IDA: Va directo al compartimento deseado
  motor.runToNewPosition(posicionDestino);
  
  // CAÍDA: Espera 2 segundos 
  delay(2000); 
  
  // VUELTA: Regresa al punto ciego original
  Serial.println("Regresando a 0...");
  motor.runToNewPosition(0);
  
  if (numeroPastilla < pastillasADispensar) {
    Serial.println("Esperando 15 segundos para la siguiente...");
  }
}

// AFMotor_MultiStepper.pde
//'/dev/ttyACM0'
// -*- mode: C++ -*-
//
// Control both Stepper motors at the same time with different speeds
// and accelerations.
// Requires the AFMotor library (https://github.com/adafruit/Adafruit-Motor-Shield-library)
// Caution, does not work with Adafruit Motor Shield V2
// See https://github.com/adafruit/Adafruit_Motor_Shield_V2_Library
// for examples that work with Adafruit Motor Shield V2.

#include <AccelStepper.h>
#define ledPin 11
byte incomingByte;


// Motor shield has two motor ports, now we'll wrap them in an AccelStepper object
AccelStepper stepper1(AccelStepper::DRIVER, 2, 5);

int fullCircle = 336;
int stepCount = 12;
int stepSize = fullCircle / stepCount;
int currentStep = 1;
bool finished = true;


void setup()
{
    // Pin 11 = Focus
    // Pin 10 = Take picture
    pinMode(10, OUTPUT);
    pinMode(11, OUTPUT);

    pinMode(8, OUTPUT); // Enable PIN stepper motor
    stepper1.setMaxSpeed(100.0);
    stepper1.setAcceleration(300.0);
    digitalWrite(8, LOW);
    Serial.begin(9600);
    pinMode(ledPin, OUTPUT);
}

void focus() {
  digitalWrite(11, HIGH);
  delay(250);
  digitalWrite(11, LOW);
}

void takePicture() {
  digitalWrite(10, HIGH);
  delay(250);
  digitalWrite(10, LOW);
}

void loop()
{

  if (Serial.available() > 0) {

    incomingByte = Serial.read();

    if (incomingByte == 'A'){
      digitalWrite(ledPin, HIGH);
      Serial.println("LED ist eingeschaltet!");
      stepper1.runToNewPosition(currentStep * stepSize);
      currentStep++;
      if (currentStep > stepCount){
        currentStep = 1;
      }
    }

    if (incomingByte == 'B'){
      digitalWrite(ledPin, LOW);
      Serial.println("LED ist ausgeschaltet!");
      currentStep = 1;
    }
    if (incomingByte == 'C'){
      do{
        if (Serial.available() > 0) {
          incomingByte = Serial.read();
          break;
        }
      } while (true);
      digitalWrite(ledPin, LOW);
      Serial.println(incomingByte);
      stepCount = (int)incomingByte;
      stepSize = fullCircle / stepCount;
      currentStep = 1;
    }
  }


  finished = true;
 
}

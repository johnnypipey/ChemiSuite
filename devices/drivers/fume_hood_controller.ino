const int SENSOR_PIN = 2;  // Digital pin connected to the sensor
int lastState = -1;         // Track previous state to avoid spam

void setup() {
  Serial.begin(9600);
  pinMode(SENSOR_PIN, INPUT_PULLUP);  // Use internal pullup resistor
  Serial.println("Window Sensor Initialized");
}

void loop() {
  int currentState = digitalRead(SENSOR_PIN);
  
  // Only print when state changes
  if (currentState != lastState) {
    if (currentState == HIGH) {
      Serial.println("Window OPEN");
    } else {
      Serial.println("Window CLOSED");
    }
    lastState = currentState;
  }
  
  delay(100);  // Small delay to debounce
}
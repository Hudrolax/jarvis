/*
  Blink
  Turns on an LED on for one second, then off for one second, repeatedly.
 
  This example code is in the public domain.
 */
 
// Pin 13 has an LED connected on most Arduino boards.
// give it a name:
int pinstate = LOW;
boolean GetCommand = false;
char cname;
int cval;
int cval2;
// Pins
int led = 13;
int Pin22 = 22;
int Pin46 = 46;

// the setup routine runs once when you press reset:
void setup() {                
  pinMode(38, INPUT);
  pinMode(40, INPUT);
  pinMode(42, INPUT);
  pinMode(44, INPUT);
  pinMode(46, INPUT);
  pinMode(48, INPUT);
  pinMode(50, INPUT);
  pinMode(52, INPUT);
  pinMode(53, INPUT);
  pinMode(39, INPUT);
  pinMode(37, INPUT);
  pinMode(35, INPUT);
  pinMode(33, INPUT);
  pinMode(31, INPUT);
  pinMode(29, INPUT);
  pinMode(27, INPUT);
  
  pinMode(36, OUTPUT);
  pinMode(34, OUTPUT);
  pinMode(32, OUTPUT);
  pinMode(30, OUTPUT);
  pinMode(28, OUTPUT);
  pinMode(26, OUTPUT);
  pinMode(24, OUTPUT);
  pinMode(22, OUTPUT);
  pinMode(13, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(2, OUTPUT);
  pinMode(45, OUTPUT);
  pinMode(47, OUTPUT);
  pinMode(14, OUTPUT);
  pinMode(15, OUTPUT);
  pinMode(16, OUTPUT);
  pinMode(17, OUTPUT);
  pinMode(18, OUTPUT);
  pinMode(19, OUTPUT);
  pinMode(49, OUTPUT);
  pinMode(51, OUTPUT);
  pinMode(23, OUTPUT);
  pinMode(25, OUTPUT);
  
     
  Serial.begin(57600);
}

// the loop routine runs over and over again forever:
void loop() {
    if (Serial.available() >= 5){ // read command from raspberry
      int flag = Serial.read();
      if (flag == 222){ // Start header byte is 222
        cname = char(Serial.read());
        int byte1 = Serial.read();
        int byte2 = Serial.read();
        cval = BitShiftCombine(byte1,byte2); // get 2byte integer from two bytes
        cval2 = Serial.read();
        GetCommand = true;
      } 
    }
      
  if (GetCommand){ // recognize command and answer
    if (cname == 'I'){ // I command - Initializing
      if (cval==666 and cval2==1){
        seriaWrite(666); // 'ok' answer
      }else{
        seriaWrite(222); // 'error' answer
      }  
    }else if (cname == 'P'){ // P command - On, Off or invert digital pin
      // cval - pin number
      // cval2 - pin state (0-LOW, 1-HIGH, 2-Invert)
      if (cval2<2){
        pinstate = cval2;
      } else {
        pinstate = digitalRead(cval);
        pinstate = !pinstate;
      }
      digitalWrite(cval, pinstate);
      if (pinstate==HIGH){
        seriaWrite(3001); // 'ON' answer
      } else{
        seriaWrite(3000); // 'OFF' answer
      }
    }else if (cname == 'A'){ // P command - On, Off or invert digital pin
      // cval - pin number
      if (cval<16){
        int val = analogRead(cval);
        seriaWrite(val);
      } 
    }else if (cname == 'S'){ // S command - return state of digital pin
      int val = digitalRead(cval);
      
      if (val==HIGH){
        seriaWrite(2001); // 'ON' answer
      } else{
        seriaWrite(2000); // 'OFF' answer
      }  
    } else {
      while (Serial.available() > 0) int byte1 = Serial.read();
    }
    GetCommand = false;
  } 
}

void seriaWrite(int val){
  // answer is integer val and consist of two bytes
  Serial.write((char)highByte(val));
  Serial.write((char)lowByte(val));
  Serial.flush();
}  

int BitShiftCombine( unsigned char x_high, unsigned char x_low)
{
  int combined;
  combined = x_high;              //send x_high to rightmost 8 bits
  combined = combined<<8;         //shift x_high over to leftmost 8 bits
  combined |= x_low;                 //logical OR keeps x_high intact in combined and fills in                                                             //rightmost 8 bits
  return combined;
}

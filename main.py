from machine import Pin, ADC, PWM
import time
from dht import DHT22

# -------------------- PIN SETUP --------------------
dht_sensor = DHT22(Pin(21))
mq2 = ADC(Pin(34))
mq2.atten(ADC.ATTN_11DB)

red_led = Pin(27, Pin.OUT)
green_led = Pin(26, Pin.OUT)
buzzer = PWM(Pin(14), freq=1000)
buzzer.duty(0)

servo = PWM(Pin(13), freq=50)
servo.duty(25)  # start at 0°

# LCD pins (4-bit mode)
RS = Pin(19, Pin.OUT)
E = Pin(18, Pin.OUT)
D4 = Pin(5, Pin.OUT)
D5 = Pin(17, Pin.OUT)
D6 = Pin(16, Pin.OUT)
D7 = Pin(23, Pin.OUT)

# -------------------- LCD FUNCTIONS --------------------
def pulse_enable():
    E.off(); time.sleep_us(1)
    E.on();  time.sleep_us(1)
    E.off(); time.sleep_us(100)

def lcd_send_nibble(n):
    D4.value((n >> 0) & 1)
    D5.value((n >> 1) & 1)
    D6.value((n >> 2) & 1)
    D7.value((n >> 3) & 1)
    pulse_enable()

def lcd_cmd(cmd):
    RS.off()
    lcd_send_nibble(cmd >> 4)
    lcd_send_nibble(cmd & 0x0F)
    time.sleep_ms(2)

def lcd_data(data):
    RS.on()
    lcd_send_nibble(data >> 4)
    lcd_send_nibble(data & 0x0F)
    time.sleep_ms(2)

def lcd_init():
    time.sleep_ms(20)
    RS.off()
    lcd_send_nibble(0x03); time.sleep_ms(5)
    lcd_send_nibble(0x03); time.sleep_us(150)
    lcd_send_nibble(0x03)
    lcd_send_nibble(0x02)

    lcd_cmd(0x28)
    lcd_cmd(0x0C)
    lcd_cmd(0x06)
    lcd_cmd(0x01)
    time.sleep_ms(2)

def lcd_goto(x, y):
    addr = 0x80 + (0x40 * y) + x
    lcd_cmd(addr)

def lcd_print(msg):
    for c in msg:
        lcd_data(ord(c))

def lcd_clear_line(y):
    lcd_goto(0, y)
    lcd_print(" " * 16)
    lcd_goto(0, y)

# -------------------- INITIAL LCD --------------------
lcd_init()
lcd_goto(0, 0)
lcd_print("Fire Detector")
lcd_goto(0, 1)
lcd_print("Starting...")
time.sleep(2)
lcd_cmd(0x01)

# -------------------- SERVO OSCILLATION --------------------
servo_positions = [25, 75]  # 0° and 90°
servo_index = 0
last_servo_time = time.ticks_ms()

# -------------------- MAIN LOOP --------------------
while True:
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
    except:
        temp = -1

    gas = mq2.read()
    fire = (temp > 45) or (gas > 700)

    if fire:
        red_led.on()
        green_led.off()
        buzzer.duty(512)
    else:
        red_led.off()
        green_led.on()
        buzzer.duty(0)

    print("====================")
    print("Temp : {:.1f}°C".format(temp))
    print("Gas  : {}".format(gas))
    print("Fire : {}".format("YES" if fire else "NO"))
    print("====================\n")

    lcd_clear_line(0)
    lcd_goto(0, 0)
    lcd_print("T:{:.1f} G:{}".format(temp, gas))

    lcd_clear_line(1)
    lcd_goto(0, 1)
    lcd_print("FIRE!" if fire else "SAFE")

    now = time.ticks_ms()
    if time.ticks_diff(now, last_servo_time) > 1000:
        servo_index = 1 - servo_index
        servo.duty(servo_positions[servo_index])
        last_servo_time = now

    time.sleep(0.1)

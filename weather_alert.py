import serial
import time
import requests
from twilio.rest import Client

# ----- CONFIGURATION -----
SERIAL_PORT = 'COM10'     #Update this if needed
BAUD_RATE = 9600

SCRIPT_URL = "Your Script URL"

TWILIO_SID = "Your Twilio SID"
TWILIO_AUTH = "Your Twilio AUTH"
TWILIO_NUMBER = "Your Twilio Number"
TARGET_NUMBER = "Your own Phone Number"

# ----- INIT -----
client = Client(TWILIO_SID, TWILIO_AUTH)
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

last_sent_time = time.time()

# ----- FUNCTIONS -----
def send_to_google(temp, hum, aqi, rain):
    data = {
        "temp": temp,
        "hum": hum,
        "aqi": aqi,
        "rain": rain
    }
    try:
        response = requests.post(SCRIPT_URL, json=data)
        print("[✓] Sent to Google Sheets:", response.text)
    except Exception as e:
        print("[!] Failed to send to Sheets:", e)

def send_sms_alert(temp, aqi, rain):
    msg = ""
    if aqi > 400:
        msg += " Poor air quality detected. Wear a mask. "
    if temp > 37:
        msg += " High temperature detected! Stay hydrated. "
    if rain in ["MODERATE", "HEAVY"]:
        msg += "🌧️ Rain Alert in Your city "

    if msg:
        try:
            message = client.messages.create(
                body=msg,
                from_=TWILIO_NUMBER,
                to=TARGET_NUMBER
            )
            print("[✓] SMS Alert Sent:", message.sid)
        except Exception as e:
            print("[!] Failed to send SMS:", e)

# ----- MAIN LOOP -----
print("Monitoring started... Waiting for sensor data.")

try:
    while True:
        line = ser.readline().decode().strip()

        if line.startswith("SEND->"):
            try:
                parts = line.replace("SEND->", "").split(",")
                if len(parts) == 4:
                    temp = float(parts[0])
                    hum = float(parts[1])
                    aqi = int(parts[2])
                    rain = parts[3].strip().upper()

                    print(f"📡 Temp: {temp}°C, Humidity: {hum}%, AQI: {aqi}, Rain: {rain}")

                    current_time = time.time()
                    if current_time - last_sent_time >= 60:
                        send_to_google(temp, hum, aqi, rain)
                        send_sms_alert(temp, aqi, rain)
                        last_sent_time = current_time

            except Exception as e:
                print("[!] Error parsing data:", e)

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🔴 Monitoring stopped by user.")
    ser.close()

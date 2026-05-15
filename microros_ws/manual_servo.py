import time
from adafruit_servokit import ServoKit

# Initialize the 16-channel driver
kit = ServoKit(channels=16)

# --- 270-DEGREE VARIANT SETTINGS ---
# Set the physical range to 270 degrees
kit.servo[0].actuation_range = 270

# DS51150 pulse range: 500us (0°) to 2500us (270°)
kit.servo[0].set_pulse_width_range(500, 2500)

print("--- DSSERVO 270° Manual Control ---")
print("Type an angle between 0 and 270. Type 'exit' to quit.")

while True:
    try:
        user_input = input("Enter Angle (0-270): ")
        
        if user_input.lower() == 'exit':
            print("Exiting...")
            break
            
        angle = float(user_input)
        
        if 0 <= angle <= 270:
            print(f"Moving to {angle} degrees...")
            kit.servo[0].angle = angle
        else:
            print("Error: Please enter a number between 0 and 270.")
            
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An error occurred: {e}")
        break
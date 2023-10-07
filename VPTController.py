import time
import random
from Model import *
from Lights import *
from Button import *
from Displays import *
from Counters import *
from Scanner import *

class VPTController:
    def __init__(self):
        # Initialize the controller and its components
        self._buttonScan = Button(15, "Scan Button", buttonhandler=self)
        self._buttonSold = Button(16, "Sold Button", buttonhandler=None)
        self._display = LCDDisplay(sda=0, scl=1, i2cid=0)
        self._greenlight = Light(27, "Price Up Light")
        self._redlight = Light(12, "Price Down Light")
        self.products = {
            '195866979345': {'name': 'Nike Dunk', 'price': 207},
            '4897085463761': {'name': 'Supreme Cam', 'price': 135},
            '2000055118': {'name': 'Kith Tee', 'price': 115},
            '759606053018': {'name': 'X-Men Comic', 'price': 40}
        }

        # Create the state model and add transitions
        self._model = Model(4, self, debug=True)  # Updated to support 4 states
        self._model.addTransition(0, [NO_EVENT], 1)
        self._model.addTransition(1, [BTN1_PRESS], 0)
        self._model.addTransition(1, [TIMEOUT], 2)
        self._model.addTransition(2, [NO_EVENT], 1)
        self._model.addTransition(1, [BTN2_PRESS], 3)
        self._model.addTransition(3, [BTN1_PRESS], 0)

        # Add buttons to the model
        self._model.addButton(self._buttonScan)
        self._model.addButton(self._buttonSold)

        # Initialize timer and price
        self._displayed_name = None
        self._displayed_price = None
        self._current_price = None
        self._displayed_price = None  # Store the currently displayed price
        self._price_change_interval = 10000  # 10 seconds (in milliseconds)
        self._price_change_timer = SoftwareTimer(None)  # Initialize the timer to None
        self._scanner = Scanner()
        self._model.addTimer(self._price_change_timer)

    def run(self):
        self._model.run(delay=0.1)

    def stateEntered(self, state, event):
        if state == 0:
            # State 0: Accept user input for the barcode
            self._display.reset()
            self._display.showText("Please scan the product:", 0)
            barcode = self._scanner.scanData(prompt="Enter the product barcode:")
            product = self.products.get(barcode)
            if product:
                self._displayed_name = product['name']
                self._displayed_price = product['price']  # Set displayed price from product
            else:
                self._display.reset()
                print(f"Invalid Barcode {barcode}")
                self._display.showText("Invalid barcode", 0)
                self._model.gotoState(0)

        elif state == 1:
            # State 1: Initialize and start the timer
            self._display.reset()
            self._display.showText(f"Name: {self._displayed_name}", 0)
            self._display.showText(f"Price: ${formatedPrice(self._displayed_price)}", 1)
            self._price_change_timer.start(5)
            self._current_price = self._displayed_price  # Store the current price for later use

        elif state == 2:
            self._display.reset()
            self._display.showText("Price Update in Progress...", 0)
            time.sleep(2)  # Display message for 2 seconds
            self._displayed_price = get_updated_price(self._displayed_price, self)
            self._model.processEvent(NO_EVENT)

        elif state == 3:
            # State 3: Handle the product sold
            self._display.reset()
            self._display.showText(f"Sold: {self._displayed_name}", 0)
            self._display.showText(f"Price: ${formatedPrice(self._displayed_price)}", 1)
            self._greenlight.on()
            self._redlight.on()
            # self._dimlightUp.on() if self._displayed_price > self._current_price else self._dimlightDown.on()
            time.sleep(2)  # Display updated price for 2 seconds

            
            # self._dimlightUp.off()
            # self._dimlightDown.off()

    def stateLeft(self, state, event):
        if state == 1:
            # State 1 exit: Cancel the timer
            self._price_change_timer.cancel()
        if state == 3:
            self._greenlight.off()
            self._redlight.off()

    def stateDo(self, state):
        if state == 1:
            self._price_change_timer.check()
        pass

# Implementations for generate_random_price and get_updated_price functions
def get_updated_price(current_price, controller):
    """
    Calculate the updated price of the product and control the LEDs based on price changes.
    Replace this with your desired logic for updating prices.
    """
    # Example: Simulate a price change by adding or subtracting a random value
    price_change = random.uniform(-5.0, 5.0)  # Simulate price change between -5 and +5
    updated_price = current_price + price_change

    if updated_price > current_price:
        # Turn on the "Price Up" LED
        controller._greenlight.blink()  # Blink the green light
        print("Price Up LED ON")
    elif updated_price < current_price:
        # Turn on the "Price Down" LED
        controller._redlight.blink()  # Blink the red light
        print("Price Down LED ON")
    else:
        # No price change, turn off both LEDs
        controller._greenlight.off()  # Turn off the green light
        controller._redlight.off()  # Turn off the red light
        print("Both LEDs OFF")

    return max(0.0, updated_price)

def formatedPrice(current_price):
    return '{0:.2f}'.format(current_price)


# Phony implementation of GPIO
import pygame

BCM = 0
IN = 0
OUT = 0
PUD_UP = 0
FALLING = 0
RISING = 1

NUMBER_DICT = dict()
CALLBACKS = []
CALLBACK_IDS = []

RESPONSE_DICT = {
    (18, 1): "Pretending to see a Raccoon",
    (18, 0): "Pretending Raccoon left",
    (20, 0): "Pretending to be done feeding Raccoon",
    (20, 1): "Pretending to feed Raccoon",
    (20, 2): "Skip feeding Raccoon",
    (5, 0): "Pretending to press left",
    (6, 0): "Pretending to press right",
    }

responses = []
wait_time = 0

print("Using the RPi phony package.")
print("- Press r to simulate a Raccoon entering the system.")
print("- Press t to simulate a Raccoon leaving the system.")
print("- Press o to simulate a Raccoon pressing the left side of the touch screen.")
print("- Press p to simulate a Raccoon pressing the right side of the touch screen.")
print("")
print("By default the feeder is ignored, but you can simulate the feeder as well, if you want to.")
print("- Press f to start simulating the feeder, or to pretend that the feeder stopped feeding.")
print("- Press g to pretend that the feeder started feeding.")
print("- Press h to ignore the feeder altogether (default).")
print("")


class RACExitRequest(Exception):
    def __init__(self):
        super().__init__("exit request")


def setmode(_):
    pygame.mixer.pre_init(22050, -16, 1, 1024)
    pygame.mixer.init()
    pygame.display.init()
    pygame.display.set_mode((1280, 768))


# noinspection PyUnusedLocal
def setup(index, value, pull_up_down=None):
    if index == 20:
        # Ignore feeding signals
        NUMBER_DICT[index] = 2
    else:
        NUMBER_DICT[index] = value

        
def output(index, value):
    if index == 1 and value == 1:
        print("Right LED is on")
    elif index == 1 and value == 0:
        print("Right LED is off")
    elif index == 2 and value == 1:
        print("Left LED is on")
    elif index == 2 and value == 0:
        print("Left LED is off")


def handle_callbacks(pin):
    for i in range(len(CALLBACKS)):
        if CALLBACK_IDS[i] == pin:
            CALLBACKS[i](pin)

            
def process_events():
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                print("Pretending to see a Raccoon", flush=True)
                NUMBER_DICT[18]=1
                handle_callbacks(18)
            elif event.key == pygame.K_e:
                print("Pretending to see another Raccoon", flush=True)
                NUMBER_DICT[18]=2
                handle_callbacks(18)
            elif event.key == pygame.K_w:
                print("Pretending to have a delay", flush=True)
                NUMBER_DICT[18]=3
                handle_callbacks(18)
            elif event.key == pygame.K_t:
                print("Pretending Raccoon left", flush=True)
                NUMBER_DICT[18]=0
                handle_callbacks(18)
            elif event.key == pygame.K_f:
                print("Pretending to feed Raccoon", flush=True)
                NUMBER_DICT[20]=1
                handle_callbacks(20)
            elif event.key == pygame.K_g:
                print("Pretending to be done feeding Raccoon", flush=True)
                NUMBER_DICT[20]=0
                handle_callbacks(20)
            elif event.key == pygame.K_h:
                print("Skip feeding Raccoon", flush=True)
                NUMBER_DICT[20]=2
                handle_callbacks(20)
            elif event.key == pygame.K_o:
                print("Pretending to press left", flush=True)
                NUMBER_DICT[5]=0
                handle_callbacks(5)
            elif event.key == pygame.K_p:
                print("Pretending to press right", flush=True)
                NUMBER_DICT[6]=0
                handle_callbacks(6)
            elif event.key == pygame.K_ESCAPE:
                raise RACExitRequest()
    
        
def input(index):
    #print("Entering input function")
    global wait_time
    pin_callbacks=[]
    if wait_time > 0:
        wait_time-=1
    else:
        while len(responses) > 0:
            response = responses.pop(0)
            #print("GPIO: Response:", response, flush=True)
            if isinstance(response, int):
                if response == -1:
                    raise RACExitRequest()
                wait_time=response
                break
            elif hasattr(response, "__call__"):
                response()  
            else:
                if response in RESPONSE_DICT:
                    print("GPIO:", RESPONSE_DICT[response], flush=True)
                else:
                    print("GPIO: Setting unknown response:", response, flush=True)
                pin, value = response
                NUMBER_DICT[pin]=value
                if pin in CALLBACK_IDS:
                    pin_callbacks.append(pin)
                        
    for pin in pin_callbacks:
        for callback in CALLBACKS:
            callback(pin)
                
    process_events()            

    #print("Leaving input function")
    if index in NUMBER_DICT:
        return NUMBER_DICT[index]
    else:
        return 0


def remove_event_detect(bla):
    pass


def cleanup():
    pass


def add_event_detect(index, a, callback=None, bouncetime=None):
    CALLBACKS.append(callback)
    CALLBACK_IDS.append(index)


class PWM:
    def __init__(self, arg, zup):
        pass

    def start(self, pho):
        pass

    def ChangeDutyCycle(self, i):
        pass

    def stop(self):
        pass

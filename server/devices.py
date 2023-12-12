import move
import RPIservo
import robotLight
import switch
from mpu6050 import mpu6050

class Screen():
    def __init__(self):
        try:
            import OLED
            self.screen = OLED.OLED_ctrl()
            self.screen.start()
            self.show(1, 'ADEEPT.COM')
        except:
            self.screen = None
            print('OLED disconnected')
            pass
        
    def show(self, line, text):
        if self.screen:
            self.screen.screen_show(line, text)


class Devices(dict):
    def __init__(self, device_config):
        super().__init__()
            
        self["screen"] = Screen()
        
        if "servos" not in device_config:
            raise Exception("[servos] not found in device_config")

        self["servos"] = RPIservo.Servos(device_config["servos"])
        
        servo_ctrl = RPIservo.ServoCtrl(self["servos"])
        self["servo_ctrl"] = servo_ctrl
        self["scGear"] = servo_ctrl
        
        self["light"] = robotLight.RobotLight()
    
        servo_ctrl.moveInit()
        
        move.setup()
        switch.switchSetup()
        
        try:
            sensor = mpu6050(0x68)
            print('mpu6050 connected, PT MODE ON')
        except:
            print('mpu6050 disconnected, ARM MODE ON')
            sensor = None
        self["sensor"] = sensor

#!/usr/bin/env python3
# File name   : servo.py
# Description : Control Servos
# Author	  : William
# Date		: 2019/02/23
from __future__ import division
import time
import RPi.GPIO as GPIO
import sys
import Adafruit_PCA9685
import threading

import random
'''
change this form 1 to -1 to reverse servos
'''
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(50)

class Servo():
    def __init__(self, servo_config : dict):
        self,config = servo_config
        
        if "index" not in config:
            raise Exception("index not found in servo_config")
        
        self.index = config["index"]
        self.name = "servo_" + str(self.index)
        
        self.sc_direction = 1
        self.init_pos = 300
        self.goal_pos = 300
        self.now_pos = 300
        self.buffer_pos = 300
        self.last_pos = 300
        self.ing_goal = 300
        self.max_pos = 560
        self.min_pos = 100
        self.sc_speed = 0
        self.ctrl_range_max = 560
        self.ctrl_range_min = 100
        self.angle_range = 180
        
        for item in config:
            setattr(self, item, config[item])
            
        
    def moveInit(self):
        index = self.index
        initPos = self.init_pos
        pwm.set_pwm(index,0,initPos)
        self.lastPos = initPos
        self.nowPos = initPos
        self.bufferPos = float(initPos)
        self.goalPos = initPos

class Servos():
    def __init__(self, servo_configs : list):
		#dict of servo name to servo object
        self.servos = {}
        for servo_config in servo_configs:
            servo = Servo(servo_config)
            name = servo.name
            self.servos[name] = servo
            
        self.servo_ctrl = ServoCtrl()
        
        #dict of servo index to servo object
        self.servo_idx = {}
        for servo_name in self.servos:
            servo = self.servos[servo_name]
            self.servo_idx[servo.index] = servo

        self.servo_ctrl.moveInit()
            
    def servoPosInit(self):
        for servo in self.servos.values():
            servo.moveServoInit()
            
    def setServoSpeed(self, name, direction, speed):
        self.servos[name].sc_direction = direction
        self.servos[name].sc_speed = speed

class ServoCtrl(threading.Thread):

	def __init__(self, servos : Servos, *args, **kwargs):
		self.servos = servos

		'''
		scMode: 'init' 'auto' 'certain' 'quick' 'wiggle'
		'''
		self.scMode = 'auto'
		self.scTime = 2.0
		self.scSteps = 30
		
		self.scDelay = 0.037
		self.scMoveTime = 0.037

		self.goalUpdate = 0
		self.wiggleID = 0
		self.wiggleDirection = 1

		super(ServoCtrl, self).__init__(*args, **kwargs)
		self.__flag = threading.Event()
		self.__flag.clear()


	def pause(self):
		print('......................pause..........................')
		self.__flag.clear()


	def resume(self):
		print('resume')
		self.__flag.set()


	def moveInit(self):
		self.scMode = 'init'
		for servo in self.servos.values():
			servo.moveInit()
		self.pause()

	def moveServoInit(self, ID):
		self.scMode = 'init'
		for servo in self.servos.values():
			servo.moveInit()
		self.pause()


	def posUpdate(self):
		self.goalUpdate = 1
		for servo in self.servos.values():
			servo.lastPos = servo.nowPos
		self.goalUpdate = 0


	def speedUpdate(self, IDinput, speedInput):
		for servo in self.servos.values():
			servo.sc_speed = speedInput[servo.index]

	def check_ingGoal(self):
		for servo in self.servos.values():
			if servo.ingGoal != servo.goalPos:
				return False
		return True

	def moveAuto(self):
		for servo in self.servos.values():
			servo.ing_goal = servo.goal_pos

		for i in range(0, self.scSteps):
			for servo in self.servos.values():
				if not self.goalUpdate:
					servo.now_pos = int(round((servo.last_pos + (((servo.goal_pos - servo.last_pos)/self.scSteps)*(i+1))),0))
					pwm.set_pwm(servo.index, 0, servo.now_pos)

				if not self.check_ingGoal():
					self.posUpdate()
					time.sleep(self.scTime/self.scSteps)
					return 1
			time.sleep((self.scTime/self.scSteps - self.scMoveTime))

		self.posUpdate()
		self.pause()
		return 0


	def moveCert(self):
		for i in range(0,16):
			self.ingGoal[i] = self.goalPos[i]
			self.bufferPos[i] = self.lastPos[i]

		while self.nowPos != self.goalPos:
			for servo in self.servos.values():
				if servo.last_pos < servo.goal_pos:
					servo.buffer_pos += self.pwmGenOut(servo.sc_speed)/(1/servo.sc_delay)
					newNow = int(round(servo.buffer_pos, 0))
					if newNow > servo.goal_pos:newNow = servo.goal_pos
					servo.now_pos = newNow
				elif servo.last_pos > servo.goal_pos:
					self.buffer_pos -= self.pwmGenOut(servo.sc_speed[i])/(1/servo.sc_delay)
					newNow = int(round(self.bufferPos[i], 0))
					if newNow < servo.goal_pos:newNow = servo.goal_pos
					servo.now_pos = newNow

				if not self.goalUpdate:
					pwm.set_pwm(servo.index, 0, servo.now_pos)

				if not self.check_ingGoal():
					self.posUpdate()
					return 1
			self.posUpdate()
			time.sleep(self.scDelay-self.scMoveTime)

		else:
			self.pause()
			return 0


	def pwmGenOut(self, angleInput):
		return int(round(((self.ctrlRangeMax-self.ctrlRangeMin)/self.angleRange*angleInput),0))


	def setAutoTime(self, autoSpeedSet):
		self.scTime = autoSpeedSet


	def setDelay(self, delaySet):
		self.scDelay = delaySet


	def autoSpeed(self, ID, angleInput):
		self.scMode = 'auto'
		self.goalUpdate = 1
		for i in range(0,len(ID)):
			newGoal = self.initPos[ID[i]] + self.pwmGenOut(angleInput[i])*self.sc_direction[ID[i]]
			if newGoal>self.maxPos[ID[i]]:newGoal=self.maxPos[ID[i]]
			elif newGoal<self.minPos[ID[i]]:newGoal=self.minPos[ID[i]]
			self.goalPos[ID[i]] = newGoal
		self.goalUpdate = 0
		self.resume()


	def certSpeed(self, ID, angleInput, speedSet):
		self.scMode = 'certain'
		self.goalUpdate = 1
		for i in range(0,len(ID)):
			newGoal = self.initPos[ID[i]] + self.pwmGenOut(angleInput[i])*self.sc_direction[ID[i]]
			if newGoal>self.maxPos[ID[i]]:newGoal=self.maxPos[ID[i]]
			elif newGoal<self.minPos[ID[i]]:newGoal=self.minPos[ID[i]]
			self.goalPos[ID[i]] = newGoal
		self.speedUpdate(ID, speedSet)
		self.goalUpdate = 0
		self.resume()


	def moveWiggle(self):
		self.bufferPos[self.wiggleID] += self.wiggleDirection*self.sc_direction[self.wiggleID]*self.pwmGenOut(self.scSpeed[self.wiggleID])/(1/self.scDelay)
		newNow = int(round(self.bufferPos[self.wiggleID], 0))
		if self.bufferPos[self.wiggleID] > self.maxPos[self.wiggleID]:self.bufferPos[self.wiggleID] = self.maxPos[self.wiggleID]
		elif self.bufferPos[self.wiggleID] < self.minPos[self.wiggleID]:self.bufferPos[self.wiggleID] = self.minPos[self.wiggleID]
		self.nowPos[self.wiggleID] = newNow
		self.lastPos[self.wiggleID] = newNow
		if self.bufferPos[self.wiggleID] < self.maxPos[self.wiggleID] and self.bufferPos[self.wiggleID] > self.minPos[self.wiggleID]:
			pwm.set_pwm(self.wiggleID, 0, self.nowPos[self.wiggleID])
		else:
			self.stopWiggle()
		time.sleep(self.scDelay-self.scMoveTime)


	def stopWiggle(self):
		self.pause()
		self.posUpdate()


	def singleServo(self, ID, direcInput, speedSet):
		if ID not in self.servos:
			raise Exception("servo ID:%s not found" % ID)
		self.wiggleID = ID
		self.wiggleDirection = direcInput
 
		servo = self.servos[ID]
		servo.sc_speed = speedSet
		self.scMode = 'wiggle'
		self.posUpdate()
		self.resume()


	def moveAngle(self, ID, angleInput):
		self.nowPos[ID] = int(self.initPos[ID] + self.sc_direction[ID]*self.pwmGenOut(angleInput))
		if self.nowPos[ID] > self.maxPos[ID]:self.nowPos[ID] = self.maxPos[ID]
		elif self.nowPos[ID] < self.minPos[ID]:self.nowPos[ID] = self.minPos[ID]
		self.lastPos[ID] = self.nowPos[ID]
		pwm.set_pwm(ID, 0, self.nowPos[ID])


	def scMove(self):
		if self.scMode == 'init':
			self.moveInit()
		elif self.scMode == 'auto':
			self.moveAuto()
		elif self.scMode == 'certain':
			self.moveCert()
		elif self.scMode == 'wiggle':
			self.moveWiggle()


	def setPWM(self, ID, PWM_input):
		self.lastPos[ID] = PWM_input
		self.nowPos[ID] = PWM_input
		self.bufferPos[ID] = float(PWM_input)
		self.goalPos[ID] = PWM_input
		pwm.set_pwm(ID, 0, PWM_input)
		self.pause()


	def run(self):
		while 1:
			self.__flag.wait()
			self.scMove()
			pass


if __name__ == '__main__':
	sc = ServoCtrl()
	sc.start()
	while 1:
		sc.moveAngle(0,(random.random()*100-50))
		time.sleep(1)
		sc.moveAngle(1,(random.random()*100-50))
		time.sleep(1)
		'''
		sc.singleServo(0, 1, 5)
		time.sleep(6)
		sc.singleServo(0, -1, 30)
		time.sleep(1)
		'''
		'''
		delaytime = 5
		sc.certSpeed([0,7], [60,0], [40,60])
		print('xx1xx')
		time.sleep(delaytime)

		sc.certSpeed([0,7], [0,60], [40,60])
		print('xx2xx')
		time.sleep(delaytime+2)

		# sc.moveServoInit([0])
		# time.sleep(delaytime)
		'''
		'''
		pwm.set_pwm(0,0,560)
		time.sleep(1)
		pwm.set_pwm(0,0,100)
		time.sleep(2)
		'''
		pass
	pass

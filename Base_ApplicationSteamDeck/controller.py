
# this is based on this paper:
# 
# Motion Planning and Control of an Overactuated 4-Wheel Drive with
# Constrained Independent Steering (2025)
# 

from math import tan


WIDTH_LEFT = 0.5
WIDTH_RIGHT = 0.5
LENGHT_FRONT = 0.5
LENGHT_REAR = 0.5

MAX_ANGLE = 0.785 # 1/4 PI
MIN_ANGLE = 0.785

B_MATRIX = [
	[-tan(MAX_ANGLE),1,(LENGHT_FRONT + WIDTH_LEFT * tan(MAX_ANGLE))], # wheel 1 max
	[-tan(MAX_ANGLE),1,-(LENGHT_REAR - WIDTH_LEFT * tan(MAX_ANGLE))], #  wheel 2 max
	[-tan(MAX_ANGLE),1,-(LENGHT_REAR + WIDTH_RIGHT * tan(MAX_ANGLE))],
	[-tan(MAX_ANGLE),1,(LENGHT_FRONT - WIDTH_RIGHT * tan(MAX_ANGLE))],
	[-tan(MIN_ANGLE),-1,-(LENGHT_FRONT + WIDTH_LEFT * tan(MIN_ANGLE))], # wheel 1 min
	[-tan(MIN_ANGLE),-1,(LENGHT_REAR - WIDTH_LEFT * tan(MIN_ANGLE))],
	[-tan(MIN_ANGLE),-1,(LENGHT_REAR + WIDTH_RIGHT * tan(MIN_ANGLE))],
	[-tan(MIN_ANGLE),-1,-(LENGHT_FRONT - WIDTH_RIGHT * tan(MIN_ANGLE))],
]

	#TODO testing
def isFeasible(advance_speed,sidle_speed,rotation_speed):
	is_valid = True
	previous = 0
	for plane in B_MATRIX:
		tmp = plane[0]*advance_speed + plane[1]*sidle_speed + plane[2]*rotation_speed
		if tmp == 0:
			print("plane of discountinuty")
		elif tmp < 0:
			print("behind the plane")
			if(previous > 0):
				is_valid = False
			previous = -1
		elif tmp > 0:
			print("ahead of plane")
			if(previous < 0):
				is_valid = False
			previous = 1
	return is_valid




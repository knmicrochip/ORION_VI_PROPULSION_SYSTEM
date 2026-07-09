
# this is based on this paper:
# 
# Motion Planning and Control of an Overactuated 4-Wheel Drive with
# Constrained Independent Steering (2025)
# 

#                    ▲                       
#                    │x                      
#                    │                       
#      ┌─────────────┼─────────────┐         
#      │             │             │         
#      │             │             │         
#      │          𜰰𜰱 │             │         
#   y  │          🭭ω⊙│             │         
# ◄────┼─────────────┘             │WHEELBASE
#      │                           │         
#      │                           │         
#      │                           │         
#      │  TRACK                    │         
#      └───────────────────────────┘         

from math import tan,atan2,sqrt,pi


TRACK = 0.85
WHEELBASE = 0.90

WIDTH_LEFT = TRACK/2.0
WIDTH_RIGHT = TRACK/2.0
LENGHT_FRONT = WHEELBASE/2.0
LENGHT_REAR = WHEELBASE/2.0

MAX_ANGLE = pi/4 # 1/4 PI
MIN_ANGLE = pi/4

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

    #TODO good testing 
def isFeasible(advance_speed,sidle_speed,rotation_speed):
    # there is an assumption made here that simplifies logic but it works only for angles smaller then 0.5 PI
    # it also removes rotation in place
    is_valid = True
    previous = 0
    for plane in B_MATRIX:
        tmp = plane[0]*advance_speed + plane[1]*sidle_speed + plane[2]*rotation_speed
        if tmp == 0:
            # print("plane of discountinuty")
            pass
        elif tmp < 0:
            # print("behind the plane")
            if(previous > 0):
                is_valid = False
            previous = -1
        elif tmp > 0:
            # print("ahead of plane")
            if(previous < 0):
                is_valid = False
            previous = 1
    return is_valid

def clampToFeasible(advance_speed,sidle_speed,rotation_speed):
    if isFeasible(advance_speed,sidle_speed,rotation_speed):
        return (advance_speed,sidle_speed,rotation_speed)
    for plane in B_MATRIX:
        
        km = plane[0] * advance_speed + plane[1] * sidle_speed + plane[2]
        kd = plane[0]**2 + plane[1]**2 + plane[2]**2
        k = km/kd
        # distance = abs(km)/sqrt(kd)
        new_advance_speed = advance_speed - k * plane[0]
        new_sidle_speed = sidle_speed - k * plane[1]
        new_rotation_speed = rotation_speed - k * plane[2]
        if(isFeasible(new_advance_speed,new_sidle_speed,new_rotation_speed)):
            return (new_advance_speed,new_sidle_speed,new_rotation_speed)

    return (0,0,0)

    pass



    # TODO normalize
    # TODO better tests
def calculateMotorConfiguration(advance_speed,sidle_speed,rotation_speed):

    clamped = clampToFeasible(advance_speed,sidle_speed,rotation_speed)
    
    advance_speed = clamped[0]
    sidle_speed = clamped[1]
    rotation_speed = clamped[2]

    # A = sidle_speed - rotation_speed * WHEELBASE
    # B = sidle_speed + rotation_speed * WHEELBASE
    # C = advance_speed - rotation_speed * TRACK
    # D = advance_speed + rotation_speed * TRACK

    A = advance_speed - rotation_speed * WHEELBASE
    B = advance_speed + rotation_speed * WHEELBASE
    C = sidle_speed - rotation_speed * TRACK
    D = sidle_speed + rotation_speed * TRACK

    # print("\n--- DEBUG: calculateMotorConfiguration Input ---")
    # print(f"Input Advance Speed:  {advance_speed}")
    # print(f"Input Sidle Speed:    {sidle_speed}")
    # print(f"Input Rotation Speed: {rotation_speed}")

    # return {
    # 	"fl":{"speed":sqrt(B**2 + C**2),"angle":atan2(B,C)},
    # 	"rl":{"speed":sqrt(B**2 + D**2),"angle":atan2(B,D)},
    # 	"rr":{"speed":sqrt(A**2 + D**2),"angle":atan2(A,D)},
    # 	"fr":{"speed":sqrt(A**2 + C**2),"angle":atan2(A,C)}
    # 	}

    configuration = {
        "fl": {"speed": sqrt(B**2 + C**2), "angle": atan2( C,  B)},
        "rl": {"speed": sqrt(B**2 + D**2), "angle": atan2( D,  B)},
        "rr": {"speed": sqrt(A**2 + D**2), "angle": atan2( D,  A)},
        "fr": {"speed": sqrt(A**2 + C**2), "angle": atan2( C,  A)}
    }

    # # 3. Print the final calculated output for the rover wheels
    # print("--- DEBUG: Calculated Wheel Outputs ---")
    # for wheel, data in configuration.items():
    #     print(f"Wheel {wheel.upper()} -> Speed: {data['speed']:.3f}, Angle: {data['angle']:.3f}")
    # print("---------------------------------------\n")

    return configuration

    
# print(calculateMotorConfiguration(1.0,0.0,0.0))
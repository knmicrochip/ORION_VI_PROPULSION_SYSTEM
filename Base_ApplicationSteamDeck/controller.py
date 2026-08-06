# Copyright 2026 ludrol
# Licensed under MIT license

# this is based on this paper:
# 
# Motion Planning and Control of an Overactuated 4-Wheel Drive with
# Constrained Independent Steering (2025)
# 





#                    ▲                       
#                    │x                      
#                    │                       
#     1┌─────────────┼─────────────┐4       
#      │             │             │         
#      │             │             │         
#      │          𜰰𜰱 │             │         
#   y  │          🭭ω⊙│             │         
# ◄────┼─────────────┘             │WHEELBASE
#      │                           │         
#      │                           │         
#      │                           │         
#      │  TRACK                    │         
#     2└───────────────────────────┘3        

from math import tan,atan2,sqrt,pi,isclose
from enum import Enum 


class zones(Enum):
    STOP = 0
    FORWARD = 1
    BACKWARD = 2

RaycastVelocity = (0,0,0)

TRACK = 0.85
WHEELBASE = 0.90

WIDTH_LEFT = TRACK/2.0
WIDTH_RIGHT = TRACK/2.0
LENGHT_FRONT = WHEELBASE/2.0
LENGHT_REAR = WHEELBASE/2.0

MAX_ANGLE = 0.785 # 1/4 PI #isFeasibleFromMotorConfiguration needs symmetry
MIN_ANGLE = -0.785
# MAX_ANGLE_HIGH = pi/2  #assumtion that it's not used
# MIN_ANGLE_HIGH = -pi/2

NEAR_ZERO = 1e-09



#       ↗         ↖
# 1, 2, 3, 4,   5, 6, 7, 8
#rr,rl,fl,fr,  rl,rr,fr,fl
#           ,  rr,        

# todo how to be safe
# check intent  to change the direction/zone
    # check safety flag
        # check if vel is 0
            # set safe
        # set vel 0 
# if safe
#   set raycast to zone according to intent
#   

# TODO:
# 1. 
# 
# 

B_MATRIX = [
    [-tan(MAX_ANGLE),1,2*(LENGHT_FRONT + WIDTH_LEFT * tan(MAX_ANGLE))], # wheel 1 max
    [-tan(MAX_ANGLE),1,2*(-LENGHT_REAR + WIDTH_LEFT * tan(MAX_ANGLE))], #  wheel 2 max
    [-tan(MAX_ANGLE),1,2*(-LENGHT_REAR - WIDTH_RIGHT * tan(MAX_ANGLE))],
    [-tan(MAX_ANGLE),1,2*(LENGHT_FRONT - WIDTH_RIGHT * tan(MAX_ANGLE))],
    [tan(MIN_ANGLE),-1,2*(LENGHT_FRONT + WIDTH_LEFT * tan(MIN_ANGLE))], # wheel 1 min
    [tan(MIN_ANGLE),-1,2*(-LENGHT_REAR + WIDTH_LEFT * tan(MIN_ANGLE))],
    [tan(MIN_ANGLE),-1,2*(-LENGHT_REAR - WIDTH_RIGHT * tan(MIN_ANGLE))],
    [tan(MIN_ANGLE),-1,2*(LENGHT_FRONT - WIDTH_RIGHT * tan(MIN_ANGLE))],
]

# counter = set()

# def get_zone_index(advance_speed,sidle_speed,rotation_speed):
#     result = 0
#     for plane in B_MATRIX:
#         tmp = plane[0]*advance_speed + plane[1]*sidle_speed + plane[2]*rotation_speed
#         if tmp < 0:
#             sign = 0
#         elif tmp > 0:
#             sign = 1
#         else:
#             sign = 1
#         result = (result << 1) | sign
#     counter.add(result)
#     print(f"{result},{len(counter)}",flush=True)

    #TODO good testing 
def isFeasible(advance_speed,sidle_speed,rotation_speed):
    # there is an assumption made here that simplifies logic but it works only for angles smaller then 0.5 PI
    # it also removes rotation in place
    is_valid = True
    sign = 0
    first = True
    rotation_speed = rotation_speed*2 #WTF?
    for plane in B_MATRIX:
        tmp = plane[0]*advance_speed + plane[1]*sidle_speed + plane[2]*rotation_speed
        # print(f"{tmp:.2f}, ",end='\t')
        # print(f"{plane[0]*advance_speed:.2f} {plane[1]*sidle_speed:.2f} {plane[2]*rotation_speed:.2f}")
        if first:
            first=False
            if tmp < 0:
                sign = -1
            elif tmp > 0:
                sign = 1
            else:
                first=True
        else:
            if tmp < 0 and sign == 1:
                is_valid = False
            elif tmp > 0 and sign == -1:
                is_valid = False


    # print(f" {is_valid}",flush=True)
    # get_zone_index(advance_speed,sidle_speed,rotation_speed)
    return is_valid

def getZoneIntent(advance_speed,sidle_speed,rotation_speed):
    if advance_speed > NEAR_ZERO:
        return zones.FORWARD
    elif advance_speed < -NEAR_ZERO:
        return zones.BACKWARD
    else:
        return zones.STOP

def isRoverStopped(state):
    isStopped = True
    for odrive_id, odrv in state.o_drives.items():
        if abs(odrv.measured_velocity) > 1:
            isStopped = False
    return isStopped

        

def clampToFeasible(advance_speed,sidle_speed,rotation_speed):
    global RaycastVelocity
    
    if isFeasible(advance_speed,sidle_speed,rotation_speed):
        return (advance_speed,sidle_speed,rotation_speed)

    # return lastValidVelocity

    old_advance_speed = RaycastVelocity[0]
    old_sidle_speed = RaycastVelocity[1]
    old_rotation_speed = 2 * RaycastVelocity[2]

    print("current:",(advance_speed,sidle_speed,rotation_speed))
    print("old:",(old_advance_speed,old_sidle_speed,old_rotation_speed),isFeasible(old_advance_speed,old_sidle_speed,old_rotation_speed))


    clamp_candidates = []
    rotation_speed = rotation_speed*2 #WTF?
    for plane in B_MATRIX:
        
        # based on geogebra solution to 
        # Rozwiąż({x=x_{a}+(x_{a}-x_{b}) t,y=y_{a}+(y_{a}-y_{b}) t,z=z_{a}+(z_{a}-z_{b}) t,a x+b y+c z=0},{x,y,z,t})

        #the ray is wrong



        dzielnik = (
            plane[0] * (advance_speed - old_advance_speed) +
            plane[1] * (sidle_speed - old_sidle_speed) +
            plane[2] * (rotation_speed - old_rotation_speed)
        )

        new_advance_speed = (
            -plane[1] * advance_speed * old_sidle_speed +
            plane[1] * old_advance_speed * sidle_speed +
            -plane[2] * advance_speed * old_rotation_speed +
            plane[2] * old_advance_speed * rotation_speed 
        ) / dzielnik

        new_sidle_speed = (
            plane[0] * advance_speed * old_sidle_speed +
            -plane[0] * old_advance_speed * sidle_speed +
            -plane[2] * sidle_speed * old_rotation_speed +
            plane[2] * old_sidle_speed * rotation_speed
        ) / dzielnik

        new_rotation_speed = (
            plane[0] * advance_speed * old_rotation_speed +
            -plane[0] * old_advance_speed * rotation_speed +
            plane[1] * sidle_speed * old_rotation_speed +
            -plane[1] * old_sidle_speed * rotation_speed
        ) / dzielnik

        distance_cube = (old_advance_speed - new_advance_speed)**2 + (old_sidle_speed - new_sidle_speed)**2 + (old_rotation_speed - new_rotation_speed)**2

        clamp_candidates.append((distance_cube,(new_advance_speed,new_sidle_speed,new_rotation_speed)))




    print(clamp_candidates)
    if clamp_candidates:
        new_clamp = min(clamp_candidates) #python is crazy
    else:
        return (0,0,0)




    # calculateMotorConfigurationClampless(new_clamp[1][0],new_clamp[1][1],new_clamp[1][2])
    return new_clamp[1]
    return (0,0,0)





    # TODO normalize
    # TODO better tests
def calculateMotorConfiguration(advance_speed,sidle_speed,rotation_speed, state = None):

    global RaycastVelocity

    if state is not None:
        intent = getZoneIntent(advance_speed,sidle_speed,rotation_speed)
        if (intent
            != 
            getZoneIntent(RaycastVelocity[0],RaycastVelocity[1],RaycastVelocity[2])):
            print(f"{intent} {getZoneIntent(RaycastVelocity[0],RaycastVelocity[1],RaycastVelocity[2])} {isRoverStopped(state)}")
            if isRoverStopped(state) == True:
                match intent:
                    case zones.FORWARD: RaycastVelocity = (10,0,0)
                    case zones.BACKWARD: RaycastVelocity = (-10,0,0)
                    case zones.STOP: RaycastVelocity = (0,0,0)
            else:
                advance_speed,sidle_speed,rotation_speed = 0,0,0



    clamped = clampToFeasible(advance_speed,sidle_speed,rotation_speed)
    
    lastValidVelocity = clamped

    # isFeasible(advance_speed,sidle_speed,rotation_speed)

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

    # print("\n--- DEBUG: calculateMotorConfiguration Input ---")
    # print(f"Input Advance Speed:  {advance_speed}")
    # print(f"Input Sidle Speed:    {sidle_speed}")
    # print(f"Input Rotation Speed: {rotation_speed}")
    # print("--- DEBUG: Calculated Wheel Outputs ---")
    # for wheel, data in configuration.items():
    #     print(f"Wheel {wheel.upper()} -> Speed: {data['speed']:.3f}, Angle: {data['angle']:.3f}")
    # print("---------------------------------------\n")

    for wheel, data in configuration.items():
        if data["angle"] > pi - MAX_ANGLE:
            data["angle"] = data["angle"] - (pi)
            data["speed"] = -data["speed"]
        if data["angle"] < - pi + MAX_ANGLE:
            data["angle"] = data["angle"] + (pi)
            data["speed"] = -data["speed"]

    # print("\n--- DEBUG: calculateMotorConfiguration Input ---")
    # print(f"Input Advance Speed:  {advance_speed}")
    # print(f"Input Sidle Speed:    {sidle_speed}")
    # print(f"Input Rotation Speed: {rotation_speed}")
    # print("--- DEBUG: Calculated Wheel Outputs ---")
    # for wheel, data in configuration.items():
    #     print(f"Wheel {wheel.upper()} -> Speed: {data['speed']:.3f}, Angle: {data['angle']:.3f}")
    # print("---------------------------------------\n")

    return configuration

        # TODO normalize
    # TODO better tests



def calculateMotorConfigurationClampless(advance_speed,sidle_speed,rotation_speed):



    A = advance_speed - rotation_speed * WHEELBASE
    B = advance_speed + rotation_speed * WHEELBASE
    C = sidle_speed - rotation_speed * TRACK
    D = sidle_speed + rotation_speed * TRACK

    configuration = {
        "fl": {"speed": sqrt(B**2 + C**2), "angle": atan2( C,  B)},
        "rl": {"speed": sqrt(B**2 + D**2), "angle": atan2( D,  B)},
        "rr": {"speed": sqrt(A**2 + D**2), "angle": atan2( D,  A)},
        "fr": {"speed": sqrt(A**2 + C**2), "angle": atan2( C,  A)}
    }

    # # 3. Print the final calculated output for the rover wheels
    # print("--- DEBUG: Calculated Wheel Outputs Without Clamping---")
    # for wheel, data in configuration.items():
    #     print(f"Wheel {wheel.upper()} -> Speed: {data['speed']:.3f}, Angle: {data['angle']:.3f}")
    # print("---------------------------------------\n")

    return configuration

def isFeasibleFromMotorConfiguration(advance_speed,sidle_speed,rotation_speed):
    result = calculateMotorConfigurationClampless(advance_speed,sidle_speed,rotation_speed)

    isFeasible = True
    for wheel in result.values():
        if (MAX_ANGLE < abs(wheel["angle"]) < pi - MAX_ANGLE):
            isFeasible = False
    return isFeasible


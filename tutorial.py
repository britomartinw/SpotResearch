import time
import math
import sys

import bosdyn.client
from bosdyn.client.image import ImageClient

from bosdyn.api import manipulation_api_pb2
from PIL import Image
import io
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_command import blocking_stand, blocking_sit, blocking_selfright
from bosdyn.geometry import EulerZXY

# from bosdyn.client import create_standard_sdk
# from bosdyn.client.lease import LeaseClient
from bosdyn.api.geometry_pb2 import Vec3
from bosdyn.api.geometry_pb2 import Vec3, SE3Pose
# from bosdyn.api.robot_command_pb2 import MobilityParams
from bosdyn.client import ResponseError, RpcError
from bosdyn.client.lease import Error as LeaseBaseError

from bosdyn.api.basic_command_pb2 import RobotCommandFeedbackStatus
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import (BODY_FRAME_NAME, ODOM_FRAME_NAME, VISION_FRAME_NAME, get_se2_a_tform_b)


global command_client
global state_client
def main():
    # Create SDK
    sdk = bosdyn.client.create_standard_sdk('understanding_spot')

    # Create a robot
    robot = sdk.create_robot('192.168.80.3')

    # Retrive robot id
    id_client = robot.ensure_client('robot-id')
    id_client.get_id()

    # Asynchronous call for the robot id
    fut = id_client.get_id_async()
    fut.result()

    # Auttheticating the robot
    robot.authenticate('user', '8w6sm6qeboc9')

    # Retreaving robot state
    state_client = robot.ensure_client('robot-state')
    print(state_client.get_robot_state().battery_states)

    # Capture and view camera images
    image_client = robot.ensure_client(ImageClient.default_service_name)
    sources = image_client.list_image_sources()

    # image_response = image_client.get_image_from_sources(["right_fisheye_image"])[0]
    # image = Image.open(io.BytesIO(image_response.shot.image.data))
    # image.show()

    # E-Stop State
    estop_client = robot.ensure_client('estop')
    estop_client.get_status()

    # # Cretate E-Stop end point 
    # estop_endpoint = bosdyn.client.estop.EstopEndpoint(client=estop_client, name='my_estop', estop_timeout=9.0)
    # estop_endpoint.force_simple_setup()

    # # Clearing E-Stop to allow power
    # estop_keep_alive = bosdyn.client.estop.EstopKeepAlive(estop_endpoint)
    # print(estop_client.get_status())
    
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    # # Acquiring control of spot (ownership/lease)
    # lease_client = robot.ensure_client('lease')
    # lease_client.list_leases()

    # lease = lease_client.acquire()
    # lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)
    # lease_client.list_leases()
    
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):

        # Powering on robot
        robot.power_on(timeout_sec=20)
        print(robot.is_powered_on())

        robot.time_sync.wait_for_sync()


        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        # blocking_selfright(command_client, timeout_sec=10)
        blocking_stand(command_client, timeout_sec=10)
        # time.sleep(1)


        # # this will make it rotate the body and stand up
        # footprint_R_body = EulerZXY(yaw=-0.4, roll=0, pitch=0)
        # cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
        # command_client.robot_command(cmd)
        # time.sleep(2)
        
        # relative_move(0, 0, math.radians(180), ODOM_FRAME_NAME, command_client, state_client, stairs=False)    
        # command_proto = RobotCommandBuilder.synchro_velocity_command(v_x=0.5, v_y=0.0, v_rot=-1.57)
        # end_time_secs = time.time() + 4.0
        # print(end_time_secs)
        # print("before")
        # try:
        #     command_client.robot_command(command=command_proto, end_time_secs=end_time_secs)
        #     print("try")
        #     # command_client.robot_command(cmd)  
        # except(ResponseError,RpcError,LeaseBaseError)as err:
        #     print("failed")
        #     print(f'Failed Moving Forward: {err}')
        # print("done")
        
        relative_move(1.5, 0, math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        
        # for i in range(4):
   
        #     relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        
        # this will make spot move straigt, sideways, and turn all at once
        # relative_move(1, 0 math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(-0.5, -0.5, math.radians(-45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0.5, 0.5, math.radians(45), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(1, 0, math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(1, 0, math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(1, 0, math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
        # relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)




        # Powering off the robot
        # time.sleep(4)
        blocking_sit(command_client, timeout_sec=10)
        robot.power_off(cut_immediately=False)
        
def walk_square(sides_lenght):
    for i in range(4):
        relative_move(1, 0, math.radians(0), ODOM_FRAME_NAME, command_client, state_client, stairs=False)    
        relative_move(0, 0, math.radians(90), ODOM_FRAME_NAME, command_client, state_client, stairs=False)
    

def relative_move(dx, dy, dyaw, frame_name, robot_command_client, robot_state_client, stairs=False):
    transforms = robot_state_client.get_robot_state().kinematic_state.transforms_snapshot

    # Build the transform for where we want the robot to be relative to where the body currently is.
    body_tform_goal = math_helpers.SE2Pose(x=dx, y=dy, angle=dyaw)
    # We do not want to command this goal in body frame because the body will move, thus shifting
    # our goal. Instead, we transform this offset to get the goal position in the output frame
    # (which will be either odom or vision).
    out_tform_body = get_se2_a_tform_b(transforms, frame_name, BODY_FRAME_NAME)
    out_tform_goal = out_tform_body * body_tform_goal

    # Command the robot to go to the goal point in the specified frame. The command will stop at the
    # new position.
    robot_cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(
        goal_x=out_tform_goal.x, goal_y=out_tform_goal.y, goal_heading=out_tform_goal.angle,
        frame_name=frame_name, params=RobotCommandBuilder.mobility_params(stair_hint=stairs))
    end_time = 10.0
    cmd_id = robot_command_client.robot_command(lease=None, command=robot_cmd,
                                                end_time_secs=time.time() + end_time)
    # Wait until the robot has reached the goal.
    while True:
        feedback = robot_command_client.robot_command_feedback(cmd_id)
        mobility_feedback = feedback.feedback.synchronized_feedback.mobility_command_feedback
        if mobility_feedback.status != RobotCommandFeedbackStatus.STATUS_PROCESSING:
            print('Failed to reach the goal')
            break
        traj_feedback = mobility_feedback.se2_trajectory_feedback
        if (traj_feedback.status == traj_feedback.STATUS_AT_GOAL and
                traj_feedback.body_movement_status == traj_feedback.BODY_STATUS_SETTLED):
            print('Arrived at the goal.')
            break
        # time.sleep(1)

    
    

if __name__ == '__main__':
    if not main():
        sys.exit(1)
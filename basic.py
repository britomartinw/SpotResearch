import curses
import math
import sys
import time

import bosdyn.client

from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_command import blocking_stand, blocking_sit, blocking_selfright

from bosdyn.client import ResponseError, RpcError
from bosdyn.client.lease import Error as LeaseBaseError

BASE_SPEED = 0.5  # m/s
BASE_ROTATION = 0.8  # rad/sec
CMD_DURATION = 0.6  # seconds
INPUT_RATE = 0.1

class User_interface():
    
    def __init__(self):
        cmd_list = {
            27: self.exit,
            119: self.foward,
            115: self.backwards,
            100: self.right,
            97: self.left,
            101: self.clockwise,
            113: self.counterclockwise,
            99: self.circle,
            
            
            
        }
    
    def display_error(desc, err, stdscr):
        stdscr.addstr(6, 0, f'Failed {desc}: {err}')  
    
    def try_cmd(self, desc, cmd, stdscr):
        try:
            self.command_client.robot_command(command=cmd, end_time_secs=time.time() + CMD_DURATION)
        except(ResponseError,RpcError,LeaseBaseError)as err:
            self.display_error(desc=desc, err=err,stdscr=stdscr)
        
    def circle(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=BASE_SPEED, v_y=0.0, v_rot=-math.radians(90))
        self.try_cmd(desc='Circle', cmd=cmd, stdscr=stdscr)
        
    def foward(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=BASE_SPEED, v_y=0.0, v_rot=0.0)
        self.try_cmd(desc='Move Forward', cmd=cmd, stdscr=stdscr)
        
    def backwards(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=-BASE_SPEED, v_y=0.0, v_rot=0.0)
        self.try_cmd(desc='Move Backward', cmd=cmd, stdscr=stdscr)
        
    def right(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=-BASE_SPEED, v_rot=0.0)
        self.try_cmd(desc='Move Right', cmd=cmd, stdscr=stdscr)
        
    def left(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=BASE_SPEED, v_rot=0.0)
        self.try_cmd(desc='Move Left', cmd=cmd, stdscr=stdscr)
        
    def clockwise(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=BASE_ROTATION)
        self.try_cmd(desc='Rotate Clockwise', cmd=cmd, stdscr=stdscr)
        
    def counterclockwise(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=-BASE_ROTATION)
        self.try_cmd(desc='Rotate Counterclockwise', cmd=cmd, stdscr=stdscr)   
        
    def exit(stdscr):
        curses.nocbreak()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

    def interface(self, stdscr):
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True) # Enable special keys
        run = True
        try:
            stdscr.addstr(0, 0, "User Interface:")
            stdscr.addstr(1, 0, "[esc]: Exit, [k]: Power-On, [l]: Power-Off")
            stdscr.addstr(2, 0, "[esc]: Exit, [k]: Power-On, [l]: Power-Off")   
            stdscr.addstr(3, 0, "[w, a, s, d]: Move")
            stdscr.addstr(4, 0, "[q, e]: Rotate\n")
            stdscr.addstr(5, 0, "[c]: Circle\n")
            stdscr.refresh()
            while run:
                key = stdscr.getch()
                if key == ord("\x1b"):
                    break
                
                if key == ord("k"):
                    self.robot.power_on(timeout_sec=20)
                    
                elif key == ord("l"):
                    self.robot.power_off(cut_immediately=False)                
                
                if key == ord('y'):
                    blocking_stand(self.command_client, timeout_sec=10)    
                elif key == ord('['):
                    blocking_sit(self.command_client, timeout_sec=10)
                    
                    
                if key == ord('w'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.5, v_y=0.0, v_rot=0.0)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc="Moving Forward", err=err, stdscr=stdscr)
                if key == ord('s'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=-0.5, v_y=0.0, v_rot=0.0)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc="Moving Backward", err=err, stdscr=stdscr)
                if key == ord('d'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=-0.5, v_rot=0.0)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc='Moving_Right', err=err, stdscr=stdscr)
                        
                if key == ord('a'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.5, v_rot=0.0)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc="Moving Left", err=err, stdscr=stdscr)
                if key == ord('q'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=0.8)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc="Rotating Right", err=err, stdscr=stdscr)
                if key == ord('e'):
                    cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=-0.8)
                    try:
                        self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 0.6)
                    except(ResponseError,RpcError,LeaseBaseError)as err:
                        self.display_error(desc="Roatating Left", err=err, stdscr=stdscr)
                if key == ord('c'):
                    self.circle(stdscr)           
                    
                stdscr.refresh()
                time.sleep(0.1)
                            
        finally:
            curses.nocbreak()
            curses.echo()
            stdscr.keypad(False)
            curses.endwin()

    def main(self):
        # Create SDK
        self.sdk = bosdyn.client.create_standard_sdk('understanding_spot')

        # Create a robot
        self.robot = self.sdk.create_robot('192.168.80.3')

        # Retrive robot id
        self.id_client = self.robot.ensure_client('robot-id')

        # Asynchronous call for the robot id
        fut = self.id_client.get_id_async()

        # Auttheticating the robot
        self.robot.authenticate('user', '8w6sm6qeboc9')

        # Retreaving robot state
        self.state_client = self.robot.ensure_client('robot-state')
        print(self.state_client.get_robot_state().battery_states)

        # E-Stop State
        estop_client = self.robot.ensure_client('estop')
        
        assert not self.robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                        'such as the estop SDK example, to configure E-Stop.'

        
        self.lease_client = self.robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
        with bosdyn.client.lease.LeaseKeepAlive(self.lease_client, must_acquire=True, return_at_exit=True):


            self.command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
            
            curses.wrapper(self.interface)

        
def main():
    ui = User_interface()
    ui.main()
    
if __name__ == '__main__':
    if not main():
        sys.exit(1)
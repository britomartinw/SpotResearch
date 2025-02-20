import curses
import math
import sys
import time

import bosdyn.client

from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_command import blocking_stand, blocking_sit, blocking_selfright

from bosdyn.client import ResponseError, RpcError
from bosdyn.client.lease import LeaseClient, Error as LeaseBaseError

from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive

BASE_SPEED = 0.5  # m/s
BASE_ROTATION = 0.8  # rad/sec
CMD_DURATION = 0.6  # seconds
INPUT_RATE = 0.1

# Estop code taken from the python examples in the spot-sdk
class EstopNoGui():
    """Provides a software estop without a GUI.

    To use this estop, create an instance of the EstopNoGui class and use the stop() and allow()
    functions programmatically.
    """

    def __init__(self, client, timeout_sec, name=None):

        # Force server to set up a single endpoint system
        ep = EstopEndpoint(client, name, timeout_sec)
        ep.force_simple_setup()

        # Begin periodic check-in between keep-alive and robot
        self.estop_keep_alive = EstopKeepAlive(ep)

        # Release the estop
        self.estop_keep_alive.allow()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanly shut down estop on exit."""
        self.estop_keep_alive.end_periodic_check_in()

    def stop(self):
        self.estop_keep_alive.stop()

    def allow(self):
        self.estop_keep_alive.allow()

    def settle_then_cut(self):
        self.estop_keep_alive.settle_then_cut()

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
    
    def display_error(self, desc, err, stdscr):
        stdscr.addstr(8, 0, f'Failed {desc}: {err}', curses.color_pair(2))  
    
    def try_cmd(self, desc, cmd, stdscr):
        try:
            self.command_client.robot_command(command=cmd, end_time_secs=time.time() + CMD_DURATION)
        except(ResponseError,RpcError,LeaseBaseError)as err:
            self.display_error(desc=desc, err=err,stdscr=stdscr)
        
    def circle(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=BASE_SPEED, v_y=0.0, v_rot=-math.radians(90))
        try:
            self.command_client.robot_command(command=cmd, end_time_secs=time.time() + 4.4)
        except(ResponseError,RpcError,LeaseBaseError)as err:
            self.display_error(desc='Circle', err=err,stdscr=stdscr)
        
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
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=-BASE_ROTATION)
        self.try_cmd(desc='Rotate Clockwise', cmd=cmd, stdscr=stdscr)
        
    def counterclockwise(self, stdscr):
        cmd = RobotCommandBuilder.synchro_velocity_command(v_x=0.0, v_y=0.0, v_rot=BASE_ROTATION)
        self.try_cmd(desc='Rotate Counterclockwise', cmd=cmd, stdscr=stdscr)   
        
    def exit(self, stdscr):
        curses.nocbreak()
        curses.echo()
        stdscr.keypad(False)
        curses.endwin()

    def interface(self, stdscr):
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True) # Enable special keys
        curses.start_color()
        run = True
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        green = curses.color_pair(1)
        yellow = curses.color_pair(2)
        red = curses.color_pair(3)
        
        stdscr.addstr(0, 0, "User Interface:", yellow)
        stdscr.addstr(1, 0, "[ESC]: Exit, [K]: Power-On, [L]: Power-Off", yellow)
        stdscr.addstr(2, 0, "[T]: Stand, [Y]: Sit", yellow)   
        stdscr.addstr(3, 0, "[SPACE]: Trigger estop, [R]: Release estop, [V]: Settle then cut estop", yellow)   
        stdscr.addstr(4, 0, "[W, A, S, D]: Move", yellow)
        stdscr.addstr(5, 0, "[Q, E]: Rotate", yellow)
        stdscr.addstr(6, 0, "[C]: Circle", yellow)
        try:
 
            stdscr.refresh()
            while run:
                key = stdscr.getch()
                if key == ord("\x1b"):
                    run = False
                    break
                
                if key == ord("k"):
                    self.robot.power_on(timeout_sec=20) 
                elif key == ord("l"):
                    self.robot.power_off(cut_immediately=False)                
                
                if key == ord('t'):
                    blocking_stand(self.command_client, timeout_sec=10)    
                elif key == ord('y'):
                    blocking_sit(self.command_client, timeout_sec=10)
                    
                if key == ord(' '):
                    self.estop_nogui.stop()
                if key == ord('r'):
                    self.estop_nogui.allow()
                if key == ord('v'):
                    self.estop_nogui.settle_then_cut()
                    
                if key == ord('w'):
                    self.foward(stdscr=stdscr)
                elif key == ord('s'):
                    self.backwards(stdscr=stdscr)
                    
                if key == ord('d'):
                    self.right(stdscr=stdscr)                        
                elif key == ord('a'):
                    self.left(stdscr=stdscr)
                    
                if key == ord('q'):
                    self.counterclockwise(stdscr=stdscr)
                elif key == ord('e'):
                    self.clockwise(stdscr=stdscr)
                
                if key == ord('c'):
                    self.circle(stdscr)    
                    
                estop_status = 'NOT_STOPPED\n'
                estop_status_color = green
                estop_states = self.state_client.get_robot_state().estop_states
                for estop_state in estop_states:
                    state_str = estop_state.State.Name(estop_state.state)
                    if state_str == 'STATE_ESTOPPED':
                        estop_status = 'STOPPED\n'
                        estop_status_color = red
                        break
                    elif state_str == 'STATE_UNKNOWN':
                        estop_status = 'ERROR\n'
                        estop_status_color = red
                    elif state_str == 'STATE_NOT_ESTOPPED':
                        pass
                    else:
                        # Unknown estop status
                        run = False
                        break
                        
                stdscr.addstr(7, 0, estop_status, estop_status_color)
                    
                stdscr.refresh()
                time.sleep(INPUT_RATE)
                            
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
        # print(self.state_client.get_robot_state().battery_states.battery.charge_percentage)
        print("Charge Percentage:")
        print([battery.charge_percentage.value for battery in self.state_client.get_robot_state().battery_states])

        # print(self.state_client.get_robot_state().estop_states)

        # E-Stop State
        estop_client = self.robot.ensure_client(EstopClient.default_service_name)
        
        self.estop_nogui = EstopNoGui(estop_client, 5, 'Estop NoGUI')
        
        assert not self.robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                        'such as the estop SDK example, to configure E-Stop.'

        
        self.lease_client = self.robot.ensure_client(LeaseClient.default_service_name)
        with bosdyn.client.lease.LeaseKeepAlive(self.lease_client, must_acquire=True, return_at_exit=True):

            print(self.state_client.get_robot_state().estop_states)

            self.command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
            
            curses.wrapper(self.interface)

        
def main():
    ui = User_interface()
    ui.main()
    
if __name__ == '__main__':
    if not main():
        sys.exit(1)
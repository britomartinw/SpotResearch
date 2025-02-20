import sys
import time
import argparse
import curses
import signal
import threading

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client import ResponseError, RpcError
from bosdyn.client.lease import Error as LeaseBaseError

VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds
COMMAND_INPUT_RATE = 0.1

# Code from the spot-sdk estop_nogui.py example
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
    
class Interface():
    
    def __init__(self , robot):
        self.robot = robot
        # Create clients -- do not use the for communication yet.
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)
        try:
            self._estop_client = self._robot.ensure_client(EstopClient.default_service_name)
            self._estop_endpoint = EstopEndpoint(self._estop_client, 'GNClient', 9.0)
        except:
            # Not the estop.
            self._estop_client = None
            self._estop_endpoint = None
        # self._power_client = robot.ensure_client(PowerClient.default_service_name)
        self._robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        self._robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        # self._robot_state_task = AsyncRobotState(self._robot_state_client)
        # self._image_task = AsyncImageCapture(robot)
        # self._async_tasks = AsyncTasks([self._robot_state_task, self._image_task])
        self._lock = threading.Lock()
        self._command_dictionary = {
            27: self._stop,  # ESC key
            ord('\t'): self._quit_program,
            ord('T'): self._toggle_time_sync,
            ord(' '): self._toggle_estop,
            ord('r'): self._self_right,
            ord('P'): self._toggle_power,
            ord('p'): self._toggle_power,
            ord('v'): self._sit,
            ord('b'): self._battery_change_pose,
            ord('f'): self._stand,
            ord('w'): self._move_forward,
            ord('s'): self._move_backward,
            ord('a'): self._strafe_left,
            ord('d'): self._strafe_right,
            ord('q'): self._turn_left,
            ord('e'): self._turn_right,
            ord('I'): self._image_task.take_image,
            ord('O'): self._image_task.toggle_video_mode,
            ord('u'): self._unstow,
            ord('j'): self._stow,
            ord('l'): self._toggle_lease
        }
        # self._locked_messages = ['', '', '']  # string: displayed message for user
        self._estop_keepalive = None
        self._exit_check = None

        # Stuff that is set in start()
        self._robot_id = None
        self._lease_keepalive = None
        
    def start(self):
        """Begin communication with the robot."""
        # Construct our lease keep-alive object, which begins RetainLease calls in a thread.
        self._lease_keepalive = LeaseKeepAlive(self._lease_client, must_acquire=True,
                                               return_at_exit=True)

        self._robot_id = self._robot.get_id()
        if self._estop_endpoint is not None:
            self._estop_endpoint.force_simple_setup(
            )  # Set this endpoint as the robot's sole estop.
            
    def drive(self, stdscr):
        """User interface to control the robot via the passed-in curses screen interface object."""
        # with ExitCheck() as self._exit_check:
        curses_handler = CursesHandler(self)
        # curses_handler.setLevel(logging.INFO)
        # LOGGER.addHandler(curses_handler)

        stdscr.nodelay(True)  # Don't block for user input.
        stdscr.resize(26, 140)
        stdscr.refresh()

        # for debug
        curses.echo()

        # try:
        while not self._exit_check.kill_now:
            # self._async_tasks.update()
            self._drive_draw(stdscr, self._lease_keepalive)

            try:
                cmd = stdscr.getch()
                # Do not queue up commands on client
                self.flush_and_estop_buffer(stdscr)
                self._drive_cmd(cmd)
                time.sleep(COMMAND_INPUT_RATE)
            except Exception:
                # On robot command fault, sit down safely before killing the program.
                self._safe_power_off()
                time.sleep(2.0)
                raise

            # finally:
            #     LOGGER.removeHandler(curses_handler)
        
    def drive_draw():
        print("Drive Draw")
        
    def _try_grpc(self, desc, thunk):
        try:
            return thunk()
        except (ResponseError, RpcError, LeaseBaseError) as err:
            print(f'Failed {desc}: {err}')
            return None

        
    def _start_robot_command(self, desc, command_proto, end_time_secs=None):

        def _start_command():
            self._robot_command_client.robot_command(command=command_proto,
                                                     end_time_secs=end_time_secs)

        self._try_grpc(desc, _start_command)
        
    def _sit(self):
        self._start_robot_command('sit', RobotCommandBuilder.synchro_sit_command())

    def _stand(self):
        self._start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())

    def _move_forward(self):
        self._velocity_cmd_helper('move_forward', v_x=VELOCITY_BASE_SPEED)

    def _move_backward(self):
        self._velocity_cmd_helper('move_backward', v_x=-VELOCITY_BASE_SPEED)

    def _strafe_left(self):
        self._velocity_cmd_helper('strafe_left', v_y=VELOCITY_BASE_SPEED)

    def _strafe_right(self):
        self._velocity_cmd_helper('strafe_right', v_y=-VELOCITY_BASE_SPEED)

    def _turn_left(self):
        self._velocity_cmd_helper('turn_left', v_rot=VELOCITY_BASE_ANGULAR)

    def _turn_right(self):
        self._velocity_cmd_helper('turn_right', v_rot=-VELOCITY_BASE_ANGULAR)

    def _stop(self):
        self._start_robot_command('stop', RobotCommandBuilder.stop_command())

    def _velocity_cmd_helper(self, desc='', v_x=0.0, v_y=0.0, v_rot=0.0):
        self._start_robot_command(
            desc, RobotCommandBuilder.synchro_velocity_command(v_x=v_x, v_y=v_y, v_rot=v_rot),
            end_time_secs=time.time() + VELOCITY_CMD_DURATION)

        

def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()

    # Create robot object
    sdk = bosdyn.client.create_standard_sdk('User_Interface')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Create estop client for the robot
    estop_client = robot.ensure_client(EstopClient.default_service_name)

    # Create nogui estop
    estop_nogui = EstopNoGui(estop_client, options.timeout, 'Estop NoGUI')

    # Create robot state client for the robot
    state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # Initialize curses screen display
    stdscr = curses.initscr()

    def cleanup_example(msg):
        """Shut down curses and exit the program."""
        print('Exiting')
        #pylint: disable=unused-argument
        estop_nogui.estop_keep_alive.shutdown()

        # Clean up and close curses
        stdscr.keypad(False)
        curses.echo()
        stdscr.nodelay(False)
        curses.endwin()
        print(msg)

    def clean_exit(msg=''):
        cleanup_example(msg)
        exit(0)

    def sigint_handler(sig, frame):
        """Exit the application on interrupt."""
        clean_exit()

    def run_example():
        """Run the actual example with the curses screen display"""
        # Set up curses screen display to monitor for stop request
        curses.noecho()
        stdscr.keypad(True)
        stdscr.nodelay(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        # If terminal cannot handle colors, do not proceed
        if not curses.has_colors():
            return

        # Curses eats Ctrl-C keyboard input, but keep a SIGINT handler around for
        # explicit kill signals outside of the program.
        signal.signal(signal.SIGINT, sigint_handler)

        # Clear screen
        stdscr.clear()

        # Display usage instructions in terminal
        stdscr.addstr('Estop w/o GUI running.\n')
        stdscr.addstr('\n')
        stdscr.addstr('[q] or [Ctrl-C]: Quit\n', curses.color_pair(2))
        stdscr.addstr('[SPACE]: Trigger estop\n', curses.color_pair(2))
        stdscr.addstr('[r]: Release estop\n', curses.color_pair(2))
        stdscr.addstr('[s]: Settle then cut estop\n', curses.color_pair(2))

        # Monitor estop until user exits
        while True:
            # Retrieve user input (non-blocking)
            c = stdscr.getch()

            try:
                if c == ord(' '):
                    estop_nogui.stop()
                if c == ord('r'):
                    estop_nogui.allow()
                if c == ord('q') or c == 3:
                    clean_exit('Exit on user input')
                if c == ord('s'):
                    estop_nogui.settle_then_cut()
            # If the user attempts to toggle estop without valid endpoint
            except bosdyn.client.estop.EndpointUnknownError:
                clean_exit('This estop endpoint no longer valid. Exiting...')

            # Check if robot is estopped by any estops
            estop_status = 'NOT_STOPPED\n'
            estop_status_color = curses.color_pair(1)
            state = state_client.get_robot_state()
            estop_states = state.estop_states
            for estop_state in estop_states:
                state_str = estop_state.State.Name(estop_state.state)
                if state_str == 'STATE_ESTOPPED':
                    estop_status = 'STOPPED\n'
                    estop_status_color = curses.color_pair(3)
                    break
                elif state_str == 'STATE_UNKNOWN':
                    estop_status = 'ERROR\n'
                    estop_status_color = curses.color_pair(3)
                elif state_str == 'STATE_NOT_ESTOPPED':
                    pass
                else:
                    # Unknown estop status
                    clean_exit()

            # Display current estop status
            if not estop_nogui.estop_keep_alive.status_queue.empty():
                latest_status = estop_nogui.estop_keep_alive.status_queue.get()[1].strip()
                if latest_status != '':
                    # If you lose this estop endpoint, report it to user
                    stdscr.addstr(7, 0, latest_status, curses.color_pair(3))
            stdscr.addstr(6, 0, estop_status, estop_status_color)

            # Slow down loop
            time.sleep(0.5)

    # Run all curses code in a try so we can cleanly exit if something goes wrong
    try:
        run_example()
    except Exception as e:
        cleanup_example(e)
        raise e
    

if __name__ == '__main__':
    if not main():
        sys.exit(1)
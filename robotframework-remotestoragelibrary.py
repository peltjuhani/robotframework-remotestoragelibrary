from robotremoteserver import RobotRemoteServer
from StorageLibrary import StorageLibrary
import sys, getopt

def main(argv):
    port = 8270
    host= "0.0.0.0"
    allow_remote_stop = False
    try:
        opts, args = getopt.getopt(argv,"p:h:a",["port=","host=","allowstop"])
    except getopt.GetoptError:
        print('robotframework-remotestoragelibrary.py [-h <IP to listen>] [-p <port to listen>] [-a]')
        print('-h / --host  That IP address of the current server that the remote server will listen at. Defaults to all (0.0.0.0)')
        print('-p / --port  The Port the remote server will listen to. Default 8270')
        print('-a / --allowstop  Allow stopping the remote server with keyword "Stop Remote Server"')
        sys.exit(2)        
    for opt, arg in opts:
        if opt in ("-h", "--host"):
            host = arg
        if opt in ("-p", "--port"):
            port = arg
        if opt in ("-a", "--allowstop"):
            allow_remote_stop = arg
            print('Allowing remote stop')
    RobotRemoteServer(library=StorageLibrary(),host=host,port=port,allow_remote_stop=allow_remote_stop )

if __name__ == "__main__":
   main(sys.argv[1:])
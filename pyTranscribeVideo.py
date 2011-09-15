#plan: this communicates by pipe and controls a video in VLC

#Opath: open video
#T: get timestamp
#M: start mark
#S: stop mark
#R: replay
#Gnn.nn.nn: goto time
#C: continue marking

#states: no video, ready, marking, marked, replaying

import sys
import vlc
import datetime
import threading
import time

class Replayer(threading.Thread):
   def __init__(self, player, startMark, stopMark):
      threading.Thread.__init__(self) # init the thread
      self.startMark = startMark
      self.stopMark = stopMark
      self.player = player
      self.running = False

   def stopReplay(self):
      self.running = False
         
   def run(self):
      player.set_pause(1)
      player.set_time(self.startMark - overlap)
      #player.play()
      player.set_pause(0) # unpause
      self.running = True
      while self.running == True:
         if player.get_time() >= self.stopMark:
            player.set_pause(1)
            self.running = False
         else:
            time.sleep(1)
         

class Enumerate(object):
   def __init__(self, names):
      for number, name in enumerate(names.split()):
         setattr(self, name, number)

global modes
global mode
global startMark #ms
global stopMark #ms
global overlap #ms
overlap = 500 #used to start replay a bit earlier
modes = Enumerate ('SETUP READY MARKING MARKED REPLAYING')

mode = modes.SETUP
startMark = 0
stopMark = 0


def tx(command):
   sys.stdout.write(command + "\n") #write does not include \n, print does
   sys.stdout.flush()

def rx():
   return sys.stdin.readline().strip("\n") # readline reads up to and including \n

def commandOpenVideo(path):
   global player
   sys.stderr.write(path + "\n")
   sys.stderr.flush()
   player = vlc.MediaPlayer(path)
   #if not player.will_play(): # this always fails :S
   #   tx("FAIL")
   #   return
   player.play() #the only time we start it playing
   while not player.is_playing(): # assuming that the video loads and plays ok
      pass
   player.set_pause(1) # just to show video so we can set up windows to taste
   player.set_time(0)
   mode = modes.READY
   tx("OK")

def commandSendTime():
   global player
   if player is None:
      tx("00:00:00")
   else:
      msTime = player.get_time()
      d = datetime.datetime.utcfromtimestamp(msTime/1000)
      tx(d.strftime("%H:%M:%S"))

def commandGotoTime(time):
   global player
   player.set_pause(1)
   #convert to milliseconds
   timeParts = time.split(":") # assumes we got perfect "00:03:02" format 
   ms = (1000 * 60 * 60 * int(timeParts[0])) + (1000 * 60 * int(timeParts[1])) + (1000 * int(timeParts[2]))
   player.set_time(ms)

def commandStartMark():
   global player
   global startMark
   startMark = player.get_time()
   #player.play()
   player.set_pause(0) # unpause

def commandStopMark():
   global player
   global stopMark
   player.set_pause(1)
   stopMark = player.get_time()

def commandContinueMark():
   global player
   #player.play()
   player.set_pause(0) # unpause

def commandReplay():
   global player, startMark, stopMark
   replayer = Replayer(player, startMark, stopMark)
   replayer.start()



running = True;
tx("READY")

while running:
   inputLine = rx()

   command = inputLine[0]
   if command == "O" and mode == modes.SETUP: #open a video
      commandOpenVideo(inputLine[1:]) # assuming that the input is valid
   elif command == "T": #send the current time
      commandSendTime()
   elif command == "G": # goto time
      commandGotoTime(inputLine[1:]) # assuming input is valid
   elif command == "M": # start marking
      commandStartMark()
   elif command == "S": #stop marking
      commandStopMark()
   elif command == "C": #continue marking
      commandContinueMark()
   elif command == "R": #replay marked section
      commandReplay()
   else:
      sys.stderr.write ("saw command: " + inputLine + "\n")
      sys.sdterr.flush()
      running = False



#plan: this plugin forks a new Python process and communicates with it by pipe
#O"path": open video (returns "OK")
#T: get timestamp (returns "00:00:00")
#M: start mark
#S: stop mark
#R: replay
#Gnn.nn.nn: goto time
#C: continue marking

#this bit creates the menu, responds to shortcuts and inserts the timestamps

#states: no video, ready, marking, marked, replaying



import subprocess
import gedit
import gtk
import os
import datetime
import time
import re

#:! cp *.py ~/.gnome2/gedit/plugins/ ; gedit
#while [ 1 ]; do ps auxw | awk '/gedi[t]/{ if($6 > 200000) {print $2}}' | xargs kill -9 ; sleep 1; done


ui_str = """<ui>
<menubar name="MenuBar">
<menu name="TranscribeMenu" action="TranscribeMenuAction">
<placeholder name="TranscribeOps">
<menuitem name="OpenVideo" action="OpenVideo"/>
<menuitem name="GotoInVideo" action="GotoInVideo"/>
<menuitem name="MarkAndPlayVideo" action="MarkAndPlayVideo"/>
<menuitem name="ReplayMarkedVideo" action="ReplayMarkedVideo"/>

</placeholder>
</menu>
</menubar>
</ui>
"""
class Enumerate(object):
      def __init__(self, names):
            for number, name in enumerate(names.split()):
                  setattr(self, name, number)

class ExamplePyWindowHelper:

        global modes
        modes = Enumerate ('SETUP READY MARKING MARKED REPLAYING')

        def __init__(self, plugin, window):
                print "Plugin created for", window
                self.mode = modes.SETUP
                self._window = window
                self._plugin = plugin
                self._insert_menu()
                self._statusbar = window.get_statusbar()
                #self.replayer = None
                

        def deactivate(self):
                print "Plugin stopped for", self._window
                self._remove_menu()
                
                self._window = None
                self._plugin = None
                self._action_group = None
                
        def _insert_menu(self):
                manager = self._window.get_ui_manager()

                self._action_group = gtk.ActionGroup("ExampleActions")
                self._action_group.add_actions([("TranscribeMenuAction", None, "Transcribing", None, "Transcribing", self.update_ui())])
                self._action_group.add_actions([("OpenVideo", None, "Open Video", None, "Open video", self.on_open_video_activate)])
                self._action_group.add_actions([("GotoInVideo", None, "Goto In Video", None, "Goto in video", self.on_goto_in_video_activate)])
                self._action_group.add_actions([("MarkAndPlayVideo", None, "Mark and play video", "<Ctrl>M", "Mark and play video", self.on_mark_and_play_video_activate)])
                self._action_group.add_actions([("ReplayMarkedVideo", None, "Replay marked video", "<Ctrl>R", "Replay marked video", self.on_replay_marked_video_activate)])
                manager.insert_action_group(self._action_group, -1)

                self._ui_id = manager.add_ui_from_string(ui_str)


        def _remove_menu(self):
                manager = self._window.get_ui_manager()
                manager.remove_ui(self._ui_id)
                manager.remove_action_group(self._action_group)
                manager.ensure_update()

        def update_ui(self):
                # Called whenever the window has been updated (active tab changed, etc.)
                print "Plugin update for", self._window
                view = self._window.get_active_view()
                print view
                if view == None:
                      return
                view.connect('key-press-event', self.on_key_press, self._window.get_active_document())
               
        def updateStatus(self):
               self._statusbar.pop(1)
               if self.mode == modes.READY:
                  self._statusbar.push(1, "Ready to play video from " + self.stopMark)
               elif self.mode == modes.MARKING: 
                  self._statusbar.push(1, "Marking started at " + self.startMark)
               elif self.mode == modes.MARKED:
                   self._statusbar.push(1, "Marked from " + self.startMark + " to " +  self.stopMark )

        def responseToDialog(self, entry, dialog, response):
               dialog.response(response)

        def getTextViaDialog(self):
               #base this on a message dialog
               dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_OK, None)
               dialog.set_markup('Goto Time in Video')
               #create the text input field
               entry = gtk.Entry()
               #allow the user to press enter to do ok
               entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
               #create a horizontal box to pack the entry and a label
               hbox = gtk.HBox()
               hbox.pack_start(gtk.Label("Time"), False, 5, 5)
               hbox.pack_end(entry)
               #some secondary text
               dialog.format_secondary_markup("Format: [[hh:]mm:]ss")
               #add it and show it
               dialog.vbox.pack_end(hbox, True, True, 0)
               dialog.show_all()
               #go go go
               dialog.run()
               text = entry.get_text()
               dialog.destroy()
               return text

        def on_goto_in_video_activate(self, action):
               #get time
               rawTime = self.getTextViaDialog()
               #parse time
               timeParts = re.findall('[1234567890]+', rawTime)
               cleanParts = ["00", "00", "00"]
               for part in timeParts:
                  part = part.rjust(2, "0")[0:2] # exactly two digits
                  cleanParts.append(part) 
               cleanTime = ":".join(cleanParts[-3:]) # last three elements of the list
               
               self.tx("G" + cleanTime)
               self.startMark = cleanTime
               self.updateStatus()
              
        def tx(self, command):
                self.childProcess.stdin.write(command + "\n") # write does not include \n
                self.childProcess.stdin.flush()

        def rx(self):
                return self.childProcess.stdout.readline().strip("\n")


        def on_open_video_activate(self, action):
                #offer dialog
                #create child process and pipes
                #tell child to open video
                #wait for ok
                
                #add toolbar

                dialog = gtk.FileChooserDialog(title="Choose a video", parent=self._window, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)) #todo: filters based on VLC?

                if dialog.run() == gtk.RESPONSE_OK:
                         self.videoFilename = dialog.get_filename()
                         dialog.destroy() #why?
                         if not os.path.isfile(self.videoFilename):
                               return #not useful: some bug with opening VLC

                         self.childProcess = subprocess.Popen(['python', '/home/coryy/.gnome2/gedit/plugins/pyTranscribeVideo.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE) # yuk. Can I get the plugin directory via the gEdit API instead?

                         #print self.rx() # wait for ready
                         self.rx() # wait for ready
                         self.tx("O" + self.videoFilename)
                         print self.rx() #wait for ok
                         self.startMark = "00:00:00"
                         self.stopMark = "00:00:00"
                         self.mode = modes.READY
                         self.updateStatus()
                else:
                         dialog.destroy() #why?

        def on_mark_and_play_video_activate(self, action):
                if self.mode == modes.SETUP:
                      pass
                elif self.mode == modes.READY:
                      self.mode = modes.MARKING
                      self.tx("T")
                      self.startMark = self.rx()
                      doc = self._window.get_active_document()
                      doc.insert(doc.get_end_iter(), ("%s\t" % self.startMark))
                      self.tx("M")
                      #self.player.play()
                elif self.mode == modes.MARKING:
                      self.mode = modes.MARKED
                      self.tx("T")
                      self.stopMark = self.rx()
                      self.tx("S")
                elif self.mode == modes.MARKED:
                      self.mode = modes.MARKING
                      self.tx("C")

                self.updateStatus()  


                                       
       

        def on_replay_marked_video_activate(self, action):
                if self.mode == modes.SETUP:
                      pass
                elif self.mode == modes.READY:
                      self.tx("R")
                elif self.mode == modes.MARKING:
                      pass
                elif self.mode == modes.MARKED:
                      #self.mode = modes.REPLAYING
                      self.tx("R")
                elif self.mode == modes.REPLAYING:
                      pass
                self.updateStatus()

        def on_key_press(self, view, event, docbuffer):
                #was it enter?
                key_name = gtk.gdk.keyval_name(event.keyval)
                if key_name == 'Return':
                       if self.mode == modes.SETUP:
                               pass
                       elif self.mode == modes.READY:
                               pass
                       elif self.mode == modes.MARKING:
                               self.mode = modes.READY
                               #self.player.set_pause(1)
                       elif self.mode == modes.MARKED:
                               self.mode = modes.READY
                       self.updateStatus()
class ExamplePyPlugin(gedit.Plugin):
        def __init__(self):
                gedit.Plugin.__init__(self)
                self._instances = {}

        def activate(self, window):
                self._instances[window] = ExamplePyWindowHelper(self, window)

        def deactivate(self, window):
                self._instances[window].deactivate()
                del self._instances[window]

        def update_ui(self, window):
                self._instances[window].update_ui()



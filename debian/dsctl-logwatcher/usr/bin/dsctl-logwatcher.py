#! /usr/bin/python
# Encoding: utf-8

import SocketServer,os,string,re,subprocess,gtk,stat,time, gettext

gettext.install("dsctl-logwatcher", unicode=1)

class myHandler(SocketServer.DatagramRequestHandler):
    def setup(self):
        self.mytimestamp = time.time() - 5.0
        SocketServer.DatagramRequestHandler.setup(self)

    def handle(self):
        while 1:
            self.data = self.rfile.readline().strip()
            if self.data == "" or (time.time() - self.mytimestamp < 5.0) : break
            if self.data.find("FAT: Filesystem error") != -1:
                m = re.search("\(dev ([-_a-z0-9]+)\)",self.data)
                try:
                    cmd=subprocess.Popen("sudo /sbin/blkid -o value -s LABEL /dev/" + m.group(1), stdout=subprocess.PIPE, shell=True)
                    cmd.wait()
                    cmdout=cmd.communicate()
                    cmd.stdout.close()
                except:
                    pass
                warnstring = _("File system error on %(mountpoint)s (/dev/%(device)s. File system has been write protected.") % { "mountpoint":cmdout[0], "device":m.group(1) }
            elif self.data.find("EXT3-fs error") != -1:
                m = re.search("\(device (dm-[0-9]+)\)",self.data)
                try:
                    cmd=subprocess.Popen("egrep \"^E:DM_NAME=.*$\" /dev/.udev/db/block\:%s" % m.group(1), stdout=subprocess.PIPE, shell=True)
                    cmd.wait()
                    cmdout=cmd.communicate()
                    cmd.stdout.close()
                except:
                    pass
                warnstring = _("File system error on %s. Please check as soon as possible!") % cmdout[0].split('=', 1)[1].strip()
            elif self.data.find("Found open truecrypt volumes on") != -1:
                m = re.search("Found open truecrypt volumes on ([^,]+),", self.data)
                warnstring = _("The Volume on %s contained open TrueCrypt Volumes.\nThey have been closed forecfully.") % m.group(1)
            elif self.data.find("disabled by hub (EMI?), re-enabling...") != -1:
                m = re.search("hub ([-.:0-9]+) port ([0-9]+) disabled by hub", self.data)
                warnstring = _("The USB connection %(portnum)i on hub %(hub)s was interrupted and re-activated. This could indicate problems with hardware or cables.") % { "portnumn":int(m.group(2)), "hub":m.group(1) }
            else:
                warnstring = self.data
            self.warndialog(warnstring)
            self.mytimestamp = time.time()
            
    def finish(self):
        pass

    def warndialog(self, warnstring):
        wd = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK)
        wd.set_title(_("WARNING!"))
        wd.set_markup(_("A severe error has occured:"))
        wd.format_secondary_text(warnstring)
        wd.run()
        wd.destroy()
        while gtk.events_pending():
            gtk.main_iteration()

if __name__ == "__main__":
    try:
        os.remove("/tmp/logwatcher.socket")
    except OSError:
        pass

    s = SocketServer.UnixDatagramServer("/tmp/logwatcher.socket", myHandler)
    try:
        os.chmod("/tmp/logwatcher.socket", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except:
        pass
    s.serve_forever()


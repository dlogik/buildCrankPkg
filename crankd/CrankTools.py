#!/usr/bin/env python
#
#    CrankTools.py
#        The OnNetworkLoad method is called from crankd on a network state change, this called the getDNS method which updates a dnsmasq config file.
#
#    Original - 10/07/2013 - Graham Gilbert (graham@grahamgilbert.com)
#    Modified - 06/05/2015 - Ed Wilson

import syslog
import subprocess
from time import sleep
import sys, io

dnsmasq_file = '/usr/local/etc/nameservers.conf'

syslog.openlog("CrankD")

class CrankTools():
    """The main CrankTools class needed for our crankd config plist"""

    def policyRun(self):
        """Checks for an active network connection and calls the jamf binary if it finds one.
            If the network is NOT active, it logs an error and exits
        ---
        Arguments: None
        Returns:  Nothing
        """
        if not self.LinkState('en1'):
            syslog.syslog(syslog.LOG_ALERT, "Updating DNS for en1")
            #self.callCmd(command)
            self.getDNS('en1')
        elif not self.LinkState('en0'):
            syslog.syslog(syslog.LOG_ALERT, "Updating DNS for en0")
            self.getDNS('en0')
        else:
            syslog.syslog(syslog.LOG_ALERT, "Internet Connection Not Found...")

    def LinkState(self, interface):
        """This utility returns the status of the passed interface.
        ---
        Arguments:
            interface - Either en0 or en1, the BSD interface name of a Network Adapter
        Returns:
            status - The return code of the subprocess call
        """
        return subprocess.call(["ipconfig", "getifaddr", interface])

    def OnNetworkLoad(self, *args, **kwargs):
        """Called from crankd directly on a Network State Change. We sleep for 10 seconds to ensure that
            an IP address has been cleared or attained, and then perform a Puppet run and a Munki run.
        ---
        Arguments:
            *args and **kwargs - Catchall arguments coming from crankd
        Returns:  Nothing
        """
        sleep(10)
        self.policyRun()

    def getDNS(self, interface):
        args = '/usr/sbin/ipconfig getoption {0} domain_name_server'
        format_args = args.format(interface)
        dns_file = dnsmasq_file

        p = subprocess.Popen(format_args.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        rc = p.returncode

        if not output:
            print 'No dns discovered'
            return

        try:
            with open(dns_file, 'r') as f:
                lines = f.readlines()
                lines[0] = 'nameserver {}'.format(output)
            with open(dns_file, 'w') as f:
                f.writelines(lines)

        except IOError:
            f.close()
            raise
        finally:
            f.close()

def main():
    crank = CrankTools()
    crank.OnNetworkLoad()

if __name__ == '__main__':
    main()

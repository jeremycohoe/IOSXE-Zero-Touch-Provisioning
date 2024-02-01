Some stuff here to describe how request library can be used at Day 0 ZTP to send a notification.

There is some room for improvement here...


# Example python

```
print ("*** Starting notification on device! ***")
print ("** delete any old files **")
cli_command = "delete /force flash:guest-share/wxt.*"
cli.executep(cli_command)
print ("** copy files **")
cli_command = "copy http://128.107.223.248/wxt.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.sh  flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.tgz flash:guest-share/"
cli.executep(cli_command)
cli_command = "copy http://128.107.223.248/wxt.sh  flash:guest-share/"
cli.executep(cli_command)
print ("** create alias exec **")
# Create alias notification to run the EEM applet with:
cli.configurep(["alias exec wxtnotification event manager run notification", "exit"])
# Enable notification EEM applet and script
print ("*** eem applet ***")
eem_notification_commands = ['no event manager applet notification',
                'event manager applet notification',
                'event none maxrun 600',
                'action 0001 cli command "enable"',
                'action 0002 cli command "guestshell enable"',
                'action 0030 cli command "guestshell run /usr/bin/bash /bootflash/guest-share/wxt.sh"'
                ]
results = configure(eem_notification_commands)
print ("*** call that eem applet ***")
cli_command = "wxtnotification"
cli.executep(cli_command)
print ("*** Successfully configured notification on device! ***")
```

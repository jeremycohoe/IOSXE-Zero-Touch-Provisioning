import requests
import socket
from cli import configure, cli
import cli

url = "https://api.ciscospark.com/v1/messages"

room_id = "your_room_id_here_ok"
bearer = "a_really_long_string_goes_in_here_ok_u_gotta_go_get_it_first"

#message = "This is a test message from the PANDA SourceVM POD 21 yo yo yo"
#message = "C9300: a switch {}".format(socket.gethostname()) + " has rebooted"
#print(socket.gethostname())
#message = "C9300: a switch {}".format(socket.gethostname()) + " has rebooted"

hostname = cli.execute('show version | i uptime')
print(hostname)

payload = {
    "roomId": room_id,
    "text": hostname
    }

headers = {
    "Authorization": "Bearer %s " % bearer
    }

response = requests.post(url, headers=headers, data = payload).json()
print(response)
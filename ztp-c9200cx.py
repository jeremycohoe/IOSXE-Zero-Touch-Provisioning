# Set HTTP proxy !?
import os
import subprocess
os.environ["HTTP_PROXY"] = 'http://proxy.esl.cisco.com:80'
os.environ["HTTPS_PROXY"] = 'http://proxy.esl.cisco.com:80'
os.environ["http_PROXY"] = 'http://proxy.esl.cisco.com:80'
os.environ["https_PROXY"] = 'http://proxy.esl.cisco.com:80'
os.environ["no_proxy"] = '10.85.134.66,10.85.134.103,10.85.134.200'

print("\n *** Use os.system to curl GET some file *** \n")
os.system("curl http://128.107.223.8/c9200cx.txt")

print("\n *** Use subprocess to curl GET some file *** \n")
result = subprocess.run(['/usr/bin/curl http://128.107.223.8/c9200cx.txt'], shell=True)
print(result.stdout)

import requests

mydata = {"nama": "Kamms"}
req = requests.post("http://127.0.0.1:8080/cobarequest", data=mydata)
print(req.text)

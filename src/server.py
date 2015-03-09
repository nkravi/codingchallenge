from flask import Flask,jsonify,request
from jsonschema import validate,ValidationError,SchemaError
import phonenumbers

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello world!"

@app.route("/handle",methods=['POST'])
def handle_request():
	result = HandleRoutes().handle_request(request.json)
	return jsonify(result)

class HandleRoutes:
	def __init__(self):
		self.server_dtls={1:{'server_ip':'10.0.1.0','server_name':'small','server_cost':0.01},
				  5:{'server_ip':'10.0.2.0','server_name':'medium','server_cost':0.05},
				  10:{'server_ip':'10.0.3.0','server_name':'large','server_cost':0.10},
				  25:{'server_ip':'10.0.4.0','server_name':'super','server_cost':0.25}}
		self.schema     = {
					"title": "SendHub Challenge Schema",
					"type": "object",
					"properties": {
						"message": {
							"type": "string"
						},
					"recipients": {
						"type": "array",
						"minItems": 1,
						"items": {"type": "string"},
						"uniqueItems": True
						}
					},
					"required": ["message", "recipients"]
				}
		
	def validate_request(self,request):
                try:
                	validate(request,self.schema)
			invalidPhoneNumbers = []
			for num in request['recipients']:
				phn = phonenumbers.parse(num,"US")
				if not phonenumbers.is_valid_number(phn):
					invalidPhoneNumbers += [str(num)]
			if len(invalidPhoneNumbers) > 0:
				return (False,'The following phone numbers are invalid '+','.join(invalidPhoneNumbers))
                except ValidationError as v:
			return (False,v.message)
		except SchemaError as s:
			return (False,s.message)
		return (True,"OK")

	def calculate_servers(self,sList,noOfMessages,minServers,serversUsed):
		for pNoMsg in range(noOfMessages+1):
      			serverCount = pNoMsg
      			newServer = 1
      			for j in [c for c in sList if c <= pNoMsg]:
            			if minServers[pNoMsg-j] + 1 < serverCount:
               				serverCount = minServers[pNoMsg-j]+1
               				newServer = j
      				minServers[pNoMsg] = serverCount
      				serversUsed[pNoMsg] = newServer
   		tmp = noOfMessages
   		result = []
   		while tmp > 0 :
      			result += [serversUsed[tmp]]
      			tmp = tmp - serversUsed[tmp]
		return result

	def form_reply_json(self,message,phoneNumbers,msgServerList):
                i = 0
                reply = {'message':message,'routes':[]}
		for server in msgServerList:
			recipients = phoneNumbers[i:i+server]
			i = i+server
                        ip = self.server_dtls[server]['server_ip']
			reply['routes'].append({'ip':ip,'recipients':recipients})
		return reply	
		
	def process_request(self,request):
		noOfMessages = len(request['recipients'])
		sList = self.server_dtls.keys()
		serversUsed = [0]*(noOfMessages+1)
                minServers = [0]*(noOfMessages+1)
                msgServerList = self.calculate_servers(sList,noOfMessages,minServers,serversUsed)
		reply = self.form_reply_json(request['message'],request['recipients'],msgServerList)
                return reply


	def handle_request(self,request):
		ret,error_code = self.validate_request(request)
		if ret:
			return self.process_request(request)
		else:
			return {'error':error_code}
		
if __name__ == "__main__":
	#app.debug = True
	app.run()

#!/usr/bin/env python3
import http.client, urllib.parse, json, os, uuid, io, codecs, sys, mimetypes

class luxand:
	def __init__(self, token):
		self.token = token

	def add_person(self, name, photos = []):
		person_id = int(self.send_request("/subject", {"name": name})["id"])

		for p in photos:
			self.add_photo_to_person(person_id, p)

		return person_id

	def delete_person(self, id):
		return self.send_request("/subject/%d" % id, method = "DELETE")

	def list_persons(self):
		return self.send_request("/subject", method = "GET", check_status = False)

	def add_photo_to_person(self, id, photo):
		return self.send_request("/subject/%d" % id, {"photo": photo})["id"]

	def recognize(self, photo):
		return self.send_request("/photo/search", {"photo": photo}, check_status = False)

	def liveness(self, photo):
		return self.send_request("/photo/liveness", {"photo": photo}, check_status = False)

	def verify(self, id, photo):
		return self.send_request("/photo/verify/%d" % id, {"photo": photo}, check_status = False)

	def detect(self, photo):
		return self.send_request("/photo/detect", {"photo": photo}, check_status = False)

	def emotions(self, photo):
		return self.send_request("/photo/emotions", {"photo": photo}, check_status = False)["faces"]

	def landmarks(self, photo):
		return self.send_request("/photo/landmarks", {"photo": photo}, check_status = False)["landmarks"]

	def celebrity(self, photo):
		return self.send_request("/photo/celebrity", {"photo": photo}, check_status = False)		

	def send_request(self, url, payload = {}, method = "POST", check_status = True):
		content_type = "application/x-www-form-urlencoded"
		files = [(a, payload[a]) for a in payload.keys() if a in ["photo"] and os.path.exists(payload[a])]
		if len(files) > 0:	
			payload = [(a, payload[a]) for a in payload.keys() if a not in ["photo"]]
			content_type, payload = MultipartFormdataEncoder().encode(payload, files)
		else:
			payload =  urllib.parse.urlencode(payload)

		conn = http.client.HTTPSConnection("api.luxand.cloud")
		headers = {
			"token": self.token,
			"content-type": content_type
			}

		conn.request(method, url, payload, headers)
		res = conn.getresponse()
		return self.check_response(res.read(), check_status)

	

	def check_response(self, result, check_status = True):
		try:
			result = json.loads(result.decode("utf-8"))
		except:
			raise Exception('Incorrect answer', result)

		if check_status:
			if "status" not in result.keys():
				raise Exception('Incorrect answer', result)

			if result["status"] != "success":
				raise Exception('Failure', result["message"])

		return result	



class MultipartFormdataEncoder(object):
    def __init__(self):
        self.boundary = uuid.uuid4().hex
        self.content_type = 'multipart/form-data; boundary={}'.format(self.boundary)

    @classmethod
    def u(cls, s):
        if sys.hexversion < 0x03000000 and isinstance(s, str):
            s = s.decode('utf-8')
        if sys.hexversion >= 0x03000000 and isinstance(s, bytes):
            s = s.decode('utf-8')
        return s

    def iter(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, file-type) elements for data to be uploaded as files
        Yield body's chunk as bytes
        """
        encoder = codecs.getencoder('utf-8')
        for (key, value) in fields:
            key = self.u(key)
            yield encoder('--{}\r\n'.format(self.boundary))
            yield encoder(self.u('Content-Disposition: form-data; name="{}"\r\n').format(key))
            yield encoder('\r\n')
            if isinstance(value, int) or isinstance(value, float):
                value = str(value)
            yield encoder(self.u(value))
            yield encoder('\r\n')
        for (key, fpath) in files:
        	filename = os.path.basename(fpath)
        	key = self.u(key)
        	filename = self.u(filename)
        	yield encoder('--{}\r\n'.format(self.boundary))
        	yield encoder(self.u('Content-Disposition: form-data; name="{}"; filename="{}"\r\n').format(key, filename))
        	yield encoder('Content-Type: {}\r\n'.format(mimetypes.guess_type(filename)[0] or 'application/octet-stream'))
        	yield encoder('\r\n')
        	with open(fpath,'rb') as fd:
        		buff = fd.read()
        		yield (buff, len(buff))
        	yield encoder('\r\n')
        yield encoder('--{}--\r\n'.format(self.boundary))

    def encode(self, fields, files):
        body = io.BytesIO()
        for chunk, chunk_len in self.iter(fields, files):
            body.write(chunk)
        return self.content_type, body.getvalue()

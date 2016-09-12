from flask import render_template, request,Flask,Response,abort,jsonify
from flask.ext.cors import CORS
from werkzeug import secure_filename
from werkzeug.security import safe_str_cmp
from pyweed import WeedFS
from pyweed.utils import post_file
from flask_jwt import JWT, jwt_required,current_identity
import mimetypes
import requests
from datetime import timedelta
from ast import literal_eval
import logging
from logging.handlers import TimedRotatingFileHandler
app_log_file = '/data/weedfs/logs/app.log'
weed = WeedFS('10.0.31.10',9333) 
mimetypes.init()

class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user

def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-really-fuckedup'
app.config['JWT_EXPIRATION_DELTA'] = timedelta(days=30)
jwt = JWT(app, authenticate, identity)
CORS(app)

handler = TimedRotatingFileHandler(app_log_file, when='midnight', interval=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)


@app.route('/upload', methods=['POST'])
@jwt_required()
def uploadfile(): 
    filestream = request.files['Filedata']
    filename = secure_filename(filestream.filename)
    res = weed.upload_file(name=filename,stream=filestream.stream)
    fid , size = (res['fid'],str(res['size']))
    app.logger.info('{0} uploaded {1} size: {2} fid: {3} '.format(current_identity.username,filename,size,fid))
    return jsonify({'fid':fid,'filename':filename,'size:':size})

@app.route('/update/<fid>',methods=['POST','PUT'])
@jwt_required()
def update_file(fid):
    filestream = request.files['Filedata']
    location = weed.get_file_location(fid)
    post_url = 'http://{0}/{1}'.format(location.public_url,fid)
    rsp = post_file(post_url,filestream.filename,filestream.stream)
    rsp_dict = literal_eval(rsp)
    app.logger.info('{0} updated {1} size: {2} fid: {3} '.format(current_identity.username,filestream.filename,rsp_dict['size'],fid))
    return rsp

@app.route('/delete/<fid>',methods=['POST','DELETE'])
@jwt_required()
def delete_file(fid):
    return 'OK: file deleted' if weed.delete_file(fid) else 'FAIL: operation failed'

@app.route('/get/<fid>/<s_filename>', methods=['GET'])
def getfile(fid,s_filename):
    file_content = weed.get_file(fid)
    if file_content and s_filename:
        return Response(file_content,mimetype=mimetypes.guess_type(s_filename)[0] or 'text/html')
    return abort(404,'file not found or invalid request')

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True,port=80)

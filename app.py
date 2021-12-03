from ms_api_rest import create_app
from flask_restful import Api
from ms_api_rest.modelos import db
from ms_api_rest.vistas import VistaAuthLogIn, VistaAuthSignUp, VistaTasks, VistaTask, VistaFiles, VistaHealth
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = create_app('default')
app_context = app.app_context()
app_context.push()

db.init_app(app)
with app.app_context():
    db.create_all() 
cors = CORS(app)

api = Api(app)
api.add_resource(VistaAuthSignUp, '/api/auth/signup')
api.add_resource(VistaAuthLogIn, '/api/auth/login')
api.add_resource(VistaTasks, '/api/tasks')
api.add_resource(VistaTask, '/api/tasks/<int:id_task>')
api.add_resource(VistaFiles, '/api/files/<string:filename>')

api.add_resource(VistaHealth, '/api/health')


jwt = JWTManager(app)
import requests
from uuid import uuid4
from flask import send_file, current_app
from flask.globals import request, session
from flask_jwt_extended.utils import get_jwt_identity
from flask_restful import Resource
from werkzeug.utils import secure_filename
from ms_api_rest.modelos.modelos import Status, Task, db, Usuario, UsuarioSchema, TaskSchema
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy.exc import IntegrityError
from pathlib import Path
import os
import json

from ms_api_rest.vistas.aws_client import delete_file_from_s3, send_message_to_sqs, upload_file_to_s3


usuario_schema = UsuarioSchema()
task_schema = TaskSchema()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CARPETA_CARGA = BASE_DIR.joinpath("files/upload")
CARPETA_DESCARGA = BASE_DIR.joinpath("files/download")
FORMATOS_ARCHIVO = ['aac', 'mp3', 'ogg', 'wav', 'wma']

class VistaHealth(Resource):
    def get(self):
        return "Servicio API Rest funcionando", 200

class VistaAuthSignUp(Resource):
    def post(self):
        usuario = Usuario.query.filter(
            Usuario.email == request.json["email"]).first()
        if usuario is not None:
            return "El usuario ya existe", 400
        else:
            if request.json["password1"] != request.json["password2"]:
                return "Contraseñas diferentes", 400
            else:
                nuevo_usuario = Usuario(
                    email=request.json["email"], username=request.json["username"], password=request.json["password1"])
                db.session.add(nuevo_usuario)
                db.session.commit()
                token_de_acceso = create_access_token(
                    identity=nuevo_usuario.id)
                return {"mensaje": "usuario creado exitosamente", "token": token_de_acceso}


class VistaAuthLogIn(Resource):
    def post(self):
        usuario = Usuario.query.filter(
            Usuario.email == request.json["email"], Usuario.password == request.json["password"]).first()
        db.session.commit()
        if usuario is None:
            return "El usuario no existe", 404
        else:
            token_de_acceso = create_access_token(identity=usuario.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token_de_acceso}


class VistaTasks(Resource):
    @jwt_required()
    def get(self):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)
        tasks = [task_schema.dump(t) for t in usuario.tasks]
        return tasks

    @jwt_required()
    def post(self):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)

        try:
            file = request.files["fileName"]
            filename = secure_filename(file.filename)

            extension = filename.split(".")[-1]
            new_format = str(request.form.get("newFormat"))
            filename = f"{uuid4()}.{extension}"
            nuevo_task = Task(
                fileName=filename, newFormat=new_format)
            usuario.tasks.append(nuevo_task)

            # S3
            s3_result = upload_file_to_s3(file, filename)
            if not s3_result:
                return f'Error en AWS S3 cargando el archvio', 422

            db.session.commit()

            # SQS
            message = json.dumps({"taskId": nuevo_task.id})
            sqs_result = send_message_to_sqs(message)
            if not sqs_result:
                session.rollback()
                return f'Error en AWS SQS enviando mensaje a la cola', 422

        except IntegrityError:
            db.session.rollback()
            return f'Error de integridad: ', 422
        except Exception as ex:
            db.session.rollback()
            print(f"Exception cargar archivo: {ex.args}")
            return f'Error creando el archvio: 1 {ex} \n 2 {ex.args}', 400
        
        return task_schema.dump(nuevo_task)


class VistaTask(Resource):
    @jwt_required()
    def get(self, id_task):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)
        task = Task.query.get_or_404(id_task)
        return task_schema.dump(task)

    @jwt_required()
    def put(self, id_task):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)
        task = Task.query.get_or_404(id_task)

        # Borrar archivo
        file_name = task.fileName.split(".", 1)[0]
        file_key=f'files/download/{file_name}.{task.newFormat.name}'
        delete_file_from_s3(file_key)

        task.newFormat = request.json.get("newFormat", task.newFormat)
        task.status = Status.UPLOADED
        db.session.commit()

        # SQS
        message = json.dumps({"taskId": task.id})
        sqs_result = send_message_to_sqs(message)
        if not sqs_result:
            session.rollback()
            return f'Error en AWS SQS enviando mensaje a la cola', 422
        
        return task_schema.dump(task)

    @jwt_required()
    def delete(self, id_task):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)
        task = Task.query.get_or_404(id_task)

        db.session.delete(task)
        db.session.commit()

        file_name = task.fileName
        CARPETA_CARGA = BASE_DIR.joinpath("files/upload")
        source_file = CARPETA_CARGA.joinpath(file_name).resolve()
        os.remove(source_file)

        # Borrar archivo
        file_key=f'files/upload/{task.fileName}'
        delete_file_from_s3(file_key)

        if(task.status == Status.PROCESSED):
            # Borrar archivo
            file_name = task.fileName.split(".", 1)[0]
            file_key=f'files/download/{file_name}.{task.newFormat.name}'
            delete_file_from_s3(file_key)

        return '', 204


class VistaFiles(Resource):

    @jwt_required()
    def get(self, filename):
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get_or_404(usuario_id)
        task = Task.query.filter(filename == filename).first_or_404()
        if task is None:
            return '', 404
        else:
            if(task.status == Status.UPLOADED):
                file_name = task.fileName
                CARPETA_CARGA = BASE_DIR.joinpath("files/upload")
                source_file = CARPETA_CARGA.joinpath(file_name).resolve()
            else:
                file_name = task.fileName.split(".", 1)[0]
                CARPETA_DESCARGA = BASE_DIR.joinpath("files/download")
                source_file = CARPETA_DESCARGA.joinpath(f"{file_name}.{task.newFormat.name}").resolve()
            return send_file(open(str(source_file), "rb"), attachment_filename=file_name)
        return '', 404


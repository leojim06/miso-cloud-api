from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import fields, Schema
import datetime
import enum

db = SQLAlchemy()

class Status(enum.Enum):
    UPLOADED = 1
    PROCESSED = 2

class AudioFormat(enum.Enum):
    MP3 = 1
    WAV = 2
    OGG = 3
    WMA = 4
    AAC = 5

class Usuario(db.Model):
    # __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200))
    username = db.Column(db.String(200))
    password = db.Column(db.String(50))
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')

class Task(db.Model):
    # __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"))
    fileName = db.Column(db.String(512))
    newFormat = db.Column(db.Enum(AudioFormat))
    timeStamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.Enum(Status), default=Status.UPLOADED)


class EnumADiccionario(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return {"llave": value.name, "valor": value.value}

class TaskSchema(Schema):
    id = fields.Integer()
    usuario = fields.String()
    fileName = fields.String()
    newFormat = EnumADiccionario(attribute=("newFormat"))
    timeStamp = fields.DateTime()
    status = EnumADiccionario(attribute=("status"))

class UsuarioSchema(Schema):
    id = fields.Integer()
    email = fields.String()
    username = fields.String()
    tasks = fields.List(fields.Nested(TaskSchema))
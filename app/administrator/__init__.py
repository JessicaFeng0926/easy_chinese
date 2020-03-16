from flask import Blueprint

administrator = Blueprint('administrator',__name__)

from . import views
from flask import Blueprint

pay = Blueprint('pay',__name__)

from . import views
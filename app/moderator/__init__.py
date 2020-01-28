from flask import Blueprint

moderator = Blueprint('moderator',__name__)

from . import views
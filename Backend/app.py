from typing import Final
from flask import Flask

app: Final[Flask] = Flask(__name__)

@app.route('/')
def index():
    return '''
        <p>Hello, world!</p>
    '''

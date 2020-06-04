from wificonnection.handlers import setup_handlers
# Jupyter Extension points
def _jupyter_server_extension_paths():
    return [{
        'module': 'wificonnection',
    }]

def _jupyter_nbextension_paths():
    return [{
        "section": "notebook",
        "dest": "wificonnection",
        "src": "static",
        "require": "wificonnection/main"
    }]

def load_jupyter_server_extension(nbapp):
    setup_handlers(nbapp.web_app)

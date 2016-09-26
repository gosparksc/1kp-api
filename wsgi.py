import os

from app.app import create_app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    application = create_app()
    app = application
    app.run(host='0.0.0.0', port=port, debug=True)

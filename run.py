from app import create_app, db
import logging

file_handler = logging.FileHandler('flask_errors.log')
file_handler.setLevel(logging.ERROR)

app = create_app(debug=True)
app.logger.addHandler(file_handler)
if __name__ == '__main__':
    app.run()
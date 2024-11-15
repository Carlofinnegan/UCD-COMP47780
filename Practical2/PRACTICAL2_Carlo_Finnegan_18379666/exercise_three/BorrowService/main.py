from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pika
import json
import os
import threading
import time
import requests  
from datetime import datetime

import logging
import sys


logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  
    ]
)

logger = logging.getLogger(__name__)

time.sleep(5)




db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = os.getenv('POSTGRES_PORT')
db_name = os.getenv('POSTGRES_DB')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Borrow(db.Model):
    __tablename__ = 'borrows'

    id = db.Column(db.Integer, primary_key=True)
    studentid = db.Column(db.String(20), nullable=False)
    bookid = db.Column(db.String(20), nullable=False)
    date_borrowed = db.Column(db.Date, nullable=False)
    date_returned = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "studentid": self.studentid,
            "bookid": self.bookid,
            "date_borrowed": self.date_borrowed.isoformat(),
            "date_returned": self.date_returned.isoformat() if self.date_returned else None
        }



with app.app_context():
    db.create_all()
    




def process_borrow_request(ch, method, properties, body):
    data = json.loads(body)
    logger.info(f"Received borrow request: {data}")

    studentid = data.get('studentid')
    bookid = data.get('bookid')
    date_returned = data.get('date_returned')

    with app.app_context():
        try:
            user_response = requests.get(f"http://user:5002/users/{studentid}")
            logger.debug(f"User response: {user_response.status_code} - {user_response.text}")

            if user_response.status_code != 200:
                logger.warning(f"Student {studentid} does not exist")
                return

            book_response = requests.get(f"http://book:5006/books/{bookid}")
            logger.debug(f"Book response: {book_response.status_code} - {book_response.text}")

            if book_response.status_code != 200:
                logger.warning(f"Book {bookid} does not exist")
                return

            # Check if student has borrowed less than 5 books
            active_borrows = Borrow.query.filter_by(studentid=studentid).count()
            if active_borrows >= 5:
                logger.info(f"Student {studentid} has reached borrow limit")
                return 


            new_borrow = Borrow(
                studentid=studentid,
                bookid=bookid,
                date_returned=date_returned,
                date_borrowed=datetime.utcnow().date()
            )
            db.session.add(new_borrow)
            db.session.commit()
            logger.info(f"Borrow request processed and saved for student {studentid}")


        except Exception as e:
            logger.error(f"An error occurred while processing borrow request: {e}", exc_info=True)
            ch.basic_ack(delivery_tag=method.delivery_tag)


@app.route('/borrows/<studentid>', methods=['GET'])
def get_borrows_by_student(studentid):
    borrows = Borrow.query.filter_by(studentid=studentid).all()
    return jsonify([borrow.to_dict() for borrow in borrows]), 200



def start_pika_consumer():
    pika_user = os.getenv('RABBITMQ_DEFAULT_USER')
    pika_password = os.getenv('RABBITMQ_DEFAULT_PASS')
    credentials = pika.PlainCredentials(pika_user, pika_password)
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq", 5672, "/", credentials))
    channel = connection.channel()
    channel.queue_declare(queue='borrow_book')
    channel.basic_consume(queue='borrow_book', on_message_callback=process_borrow_request, auto_ack=False)
    print("BorrowService is listening for borrow requests...")
    channel.start_consuming()




if __name__ == "__main__":
    threading.Thread(target=start_pika_consumer).start()
    app.run(host="0.0.0.0", port=5008)
    



    






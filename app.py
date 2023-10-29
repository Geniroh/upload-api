from flask import Flask, request, jsonify
from google.cloud import storage, firestore
import os
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

print(os.getenv("credential_path"))
current_directory = os.getcwd()
service_key_file = 'windy-cedar-403413-d9fd4f98d4bb.json'
service_key_file_path = os.path.join(current_directory, service_key_file)

def configure_gcs_client():
    client = storage.Client.from_service_account_json(service_key_file_path)
    return client

gcs_client = configure_gcs_client()
bucket_name = 'upload-test-matic'  

db = firestore.Client.from_service_account_json(service_key_file_path)

@app.route("/")
def hello_world():
    return "Hello World"

@app.route('/upload', methods=['POST'])
def upload_video():
    uploaded_file = request.files['video']
    allowed_video_formats = ['.mp4', '.avi', '.mov', '.mkv']

    if uploaded_file:
        file_extension = os.path.splitext(uploaded_file.filename)[1].lower()

        if file_extension in allowed_video_formats:
            blob = gcs_client.bucket(bucket_name).blob(uploaded_file.filename)
            blob.upload_from_file(uploaded_file)

            metadata = {
                'file_name': uploaded_file.filename,
                'file_size': uploaded_file.content_length,
                'upload_time': firestore.SERVER_TIMESTAMP
            }

            try:
                doc_ref = db.collection('video').add(metadata)
                return jsonify({"message": "File uploaded to Google Cloud Storage and metadata stored in Firestore successfully."})
            except Exception as e:
                error_message = f'Error storing metadata in Firestore: {str(e)}'
                return jsonify({"error": True, "message": error_message})   
        else:
            return jsonify({"error": True , "message": 'Invalid file format. Allowed formats: ' + ', '.join(allowed_video_formats)})
    else:
        return jsonify({"error": True , "message": 'No file provided.'})

if __name__ == '__main__':
    app.run(debug=True)
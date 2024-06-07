import firebase_admin
from firebase_admin import credentials, storage

from food_tracker_backend.settings import env

# Path to your service account key file
service_account_path = env('SERVICE_ACCOUNT_PATH', default='/app/api/serviceAccountKey.json')

cred = credentials.Certificate(service_account_path)

# Initialize the Firebase app
firebase_admin.initialize_app(cred, {
    'storageBucket': 'munch-f2d84.appspot.com'
})


def upload_image_to_firebase(image_file):
    # Get the default bucket
    bucket = storage.bucket()
    # Create a new blob and upload the file's content
    blob = bucket.blob(image_file.name)
    blob.upload_from_file(image_file)
    # Make the blob publicly viewable
    blob.make_public()
    # Return the public url
    return blob.public_url
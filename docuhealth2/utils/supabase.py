from supabase import create_client, Client
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import uuid

# Initialize Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
bucket_name  = settings.SUPABASE_BUCKET_NAME 

def upload_file_to_supabase(file, folder: str, bucket_name=bucket_name, custom_name: str = None):
    """
    Upload any file to Supabase storage and return the public URL.

    Args:
        file: The uploaded file object (Django InMemoryUploadedFile or similar)
        folder (str): The folder/path in the bucket (e.g., 'hospital_docs', 'avatars', etc.)
        bucket_name (str): The Supabase storage bucket name
        custom_name (str): Optional custom name for the uploaded file (without extension)

    Returns:
        str | Response: The public URL on success, or DRF Response on failure.
    """
    try:
        if not file:
            raise ValueError("No file provided.")
        if not folder:
            raise ValueError("Folder path is required.")

        file_ext = file.name.split('.')[-1]
        file_name = f"{custom_name or uuid.uuid4().hex}.{file_ext}"
        path = f"{folder}/{file_name}"

        file_bytes = file.read()

        # Upload to Supabase
        response = supabase.storage.from_(bucket_name).upload(
            path, 
            file_bytes,
            file_options={"content_type": file.content_type}
        )
        print(response)

        public_url = supabase.storage.from_(bucket_name).get_public_url(path)

        if not public_url:
            raise Exception("Failed to retrieve public URL from Supabase.")

        return public_url

    except Exception as e:
        raise Exception(f"File upload failed: {str(e)}")

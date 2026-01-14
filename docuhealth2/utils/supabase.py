from supabase import create_client, Client
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import uuid

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
bucket_name  = settings.SUPABASE_BUCKET_NAME 

def upload_file_to_supabase(file_bytes, filename, content_type, folder: str, bucket_name=bucket_name, custom_name: str = None):
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
    from supabase import create_client
    thread_supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    try:
        if not file_bytes:
            raise ValueError("No file provided.")
        if not folder:
            raise ValueError("Folder path is required.")

        file_ext = filename.split('.')[-1]
        file_name = f"{custom_name or uuid.uuid4().hex}.{file_ext}"
        path = f"{folder}/{file_name}"

        response = thread_supabase.storage.from_(bucket_name).upload(
            path, 
            file_bytes,
            file_options={"content_type": content_type}
        )
        print(response)

        public_url = thread_supabase.storage.from_(bucket_name).get_public_url(path)

        if not public_url:
            raise Exception("Failed to retrieve public URL from Supabase.")

        return {
            "id": str(uuid.uuid4()),
            "url": public_url, 
            "path": path,
            "filename": file_name,
            "content_type": content_type,
        }

    except Exception as e:
        raise Exception(f"File upload failed: {str(e)}")
    
def delete_from_supabase(path: str, bucket_name=bucket_name):
    """
    Deletes a file from Supabase storage using its path.
    """
    try:
        response = supabase.storage.from_(bucket_name).remove([path])
        return response
    except Exception as e:
        print(f"Cleanup failed for {path}: {str(e)}")
        return None

from django.db import transaction
from concurrent.futures import ThreadPoolExecutor
from docuhealth2.utils.supabase import upload_file_to_supabase, delete_from_supabase
from accounts.models import User

def upload_onboarding_files(documents):
    files_data = [{"bytes": doc.read(), "name": doc.name, "type": doc.content_type} for doc in documents]
    uploaded_data = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(upload_file_to_supabase,  file['bytes'], file['name'], file['type'],  "pharmacy_verification_docs") for file in files_data
        ]
        
        try:
            for future in futures:
                uploaded_data.append(future.result())
                
            return uploaded_data
                
        except Exception as e:
            for doc in uploaded_data:
                delete_from_supabase(doc['path'])
            raise e
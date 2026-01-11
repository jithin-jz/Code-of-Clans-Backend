import os
from supabase import create_client, Client
from django.conf import settings

def get_supabase_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        return None
    # Ensure URL doesn't have a trailing slash for the client creation, 
    # but some internal libs might need it. The warning suggests ADDING it, 
    # but standard setup often doesn't need manual tweaking.
    # However, creating the client usually handles normalization.
    return create_client(url, key)

class StorageService:
    @staticmethod
    def upload_file(file, path, bucket='Code of Clans'):
        """
        Uploads a file to Supabase Storage.
        Returns the public URL of the uploaded file.
        """
        supabase = get_supabase_client()
        if not supabase:
            raise Exception("Supabase credentials not configured")

        try:
            # Read file content
            file_content = file.read()
            
            # Upload file
            res = supabase.storage.from_(bucket).upload(
                path=path,
                file=file_content,
                file_options={"content-type": file.content_type, "upsert": "true"}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(bucket).get_public_url(path)
            return public_url
            
        except Exception as e:
            print(f"Supabase upload error: {str(e)}")
            raise e

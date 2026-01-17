import os
from supabase import create_client, Client
from django.conf import settings

def get_supabase_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    
    if not url or not key:
        print("Supabase credentials missing in settings.")
        return None

    # Fix: Ensure URL starts with https:// and has no trailing slash
    if not url.startswith("http"):
        url = f"https://{url}"
    
    url = url.rstrip('/')
    
    print(f"Initializing Supabase Client with URL: {url}")
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
            print(f"Starting upload for {path} to bucket {bucket}...")
            
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
            print(f"Upload successful. Public URL: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Supabase upload error for {path}: {str(e)}")
            # Raise the original exception to be caught by the view
            raise e

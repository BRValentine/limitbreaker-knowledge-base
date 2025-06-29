import os
import io
import fitz  # PyMuPDF for PDF text extraction
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import markdownify

# Configuration
FOLDER_ID = '1NsTM9z2SoVAa-q6xbVFgGxgbat5POSQ9'  # Your Credit_Repair_Bot_Docs folder ID
OUTPUT_DIR = 'markdown_output'  # Directory to save markdown files
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Google Docs Editors MIME types and export formats
DOCS_MIME_TYPES = {
    'application/vnd.google-apps.document': ('text/html', '.html'),
    'application/vnd.google-apps.spreadsheet': ('text/csv', '.csv'),
    'application/vnd.google-apps.presentation': ('application/pdf', '.pdf')
}

def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def convert_to_markdown(content, file_ext):
    if file_ext in ['.html', '.csv', '.txt']:
        return markdownify.markdownify(content.decode('utf-8', errors='ignore'))
    elif file_ext == '.pdf':
        # Extract text from PDF content
        try:
            pdf_document = fitz.open(stream=content, filetype='pdf')
            text = ''
            for page in pdf_document:
                text += page.get_text()
            pdf_document.close()
            return markdownify.markdownify(text)
        except Exception as e:
            return f"Error converting PDF to markdown: {str(e)}"
    return content.decode('utf-8', errors='ignore')

def get_folder_path(drive_service, folder_id, cache=None):
    if cache is None:
        cache = {}
    if folder_id in cache:
        return cache[folder_id]
    
    path = []
    current_id = folder_id
    while current_id != FOLDER_ID:
        file = drive_service.files().get(fileId=current_id, fields='id, name, parents').execute()
        path.append(file['name'])
        if 'parents' not in file:
            break
        current_id = file['parents'][0]
    path.append('root')  # Represent the top-level folder
    path = '/'.join(reversed(path))
    cache[folder_id] = path
    return path

def process_folder(drive_service, folder_id, base_output_path, folder_cache):
    # Create output directory if it doesn't exist
    if not os.path.exists(base_output_path):
        os.makedirs(base_output_path)

    # Query items in the folder
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name, mimeType, parents)").execute()
    items = results.get('files', [])

    if not items:
        print(f'No items found in folder ID {folder_id}.')
        return

    for item in items:
        item_id = item['id']
        item_name = item['name']
        mime_type = item['mimeType']

        if mime_type == 'application/vnd.google-apps.folder':
            # Recursively process subfolder
            print(f'Entering folder: {item_name}')
            subfolder_path = os.path.join(base_output_path, item_name)
            process_folder(drive_service, item_id, subfolder_path, folder_cache)
        else:
            # Process file
            print(f'Processing file: {item_name} ({mime_type})...')
            try:
                if mime_type in DOCS_MIME_TYPES:
                    # Export Google Docs Editors files
                    export_mime, file_ext = DOCS_MIME_TYPES[mime_type]
                    request = drive_service.files().export_media(fileId=item_id, mimeType=export_mime)
                else:
                    # Download binary files (e.g., PDFs, text files)
                    request = drive_service.files().get_media(fileId=item_id)
                    file_ext = os.path.splitext(item_name)[1].lower() or '.txt'

                # Download the file content
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

                # Convert content to markdown
                content = fh.getvalue()
                markdown_content = convert_to_markdown(content, file_ext)

                # Save markdown file
                output_file = os.path.join(base_output_path, f"{os.path.splitext(item_name)[0]}.md")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                print(f'Saved markdown to {output_file}')

            except Exception as e:
                print(f'Error processing {item_name}: {str(e)}')

def main():
    # Authenticate and build Drive service
    drive_service = authenticate_drive()

    # Initialize folder path cache
    folder_cache = {}

    # Get the name of the root folder
    root_folder = drive_service.files().get(fileId=FOLDER_ID, fields='name').execute()
    root_folder_name = root_folder['name']

    # Process the root folder and its subfolders
    output_path = os.path.join(OUTPUT_DIR, root_folder_name)
    process_folder(drive_service, FOLDER_ID, output_path, folder_cache)

if __name__ == '__main__':
    main()
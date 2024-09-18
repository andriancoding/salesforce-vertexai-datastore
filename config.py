import os

class Config:
    def __init__(self):
        self.sf_client_id = os.getenv('SF_CLIENT_ID')
        self.sf_client_secret = os.getenv('SF_CLIENT_SECRET')
        self.sf_username = os.getenv('SF_USERNAME')
        self.sf_password = os.getenv('SF_PASSWORD')
        self.sf_security_token = os.getenv('SF_SECURITY_TOKEN')
        self.sf_domain = "https://yourdomain-dev-ed.develop.my.salesforce.com"
        self.sf_article_base_url = "https://yourdomain-dev-ed.develop.lightning.force.com/lightning/r/Knowledge__kav/"
        self.gcp_project_id = os.getenv('GCP_PROJECT_ID')
        self.gcp_location = os.getenv('GCP_LOCATION') # Location of the datastore. ex: global
        self.data_store_id = os.getenv('DATA_STORE_ID') #ex: sf-articles
        self.data_store_display_name = os.getenv('DATA_STORE_DISPLAY_NAME') #ex: Salesforce Articles
        self.branch_id = "default_branch"
        self.collection_id = "default_collection"
        self.document_name_path = f"projects/{self.gcp_project_id}/locations/{self.gcp_location}/collections/{self.collection_id}/dataStores/{self.data_store_id}/branches/{self.branch_id}/documents"
        self.parent = f"projects/{self.gcp_project_id}/locations/{self.gcp_location}"
import json, requests
from google.cloud import discoveryengine_v1beta
from google.protobuf import struct_pb2
from google.api_core.exceptions import NotFound
from config import Config

def check_data_store_exists(data_store_id, parent, data_store_client):
    """
    Checks if a data store with the given `data_store_id` exists under the specified `parent` resource.

    Args:
        data_store_id (str): The ID of the data store to check.
        parent (str): The parent resource path (e.g., "projects/{project_id}/locations/{location}").
        data_store_client (DataStoreServiceClient): The client used to interact with the data store service.

    Returns:
        bool: True if the data store exists, False otherwise.
    """
    try:
        response = data_store_client.list_data_stores(parent=parent)
        for data_store in response:
            if data_store.name.split("/")[-1] == data_store_id:
                print(f"Datastore with id {data_store_id} already exists")
                return True
    except Exception as e:
        print(f"An error occurred while listing data stores: {e}")
        return False

    return False

def create_data_store(project_id, location, data_store_id, data_store_client, data_store_display_name):
    """
    Creates a new data store in the specified project and location if it doesn't already exist.

    Args:
        project_id (str): The GCP project ID.
        location (str): The GCP location where the data store will be created.
        data_store_id (str): The ID for the new data store.
        data_store_client (DataStoreServiceClient): The client used to interact with the data store service.
        data_store_display_name (str): A display name for the data store.

    Returns:
        bool: True if the data store is created or already exists, False if creation fails.
    """
    parent = f"projects/{project_id}/locations/{location}"

    if not check_data_store_exists(data_store_id, parent, data_store_client):
        data_store = discoveryengine_v1beta.DataStore()
        data_store.name = f"{parent}/dataStores/{data_store_id}"
        data_store.display_name = data_store_display_name
        data_store.industry_vertical = "GENERIC"
        try:
            response = data_store_client.create_data_store(parent=parent, data_store=data_store, data_store_id=data_store_id)
            print(f"Data store {data_store_id} created successfully")
            return True
        except Exception as e:
            print(f"An error occurred while creating data store: {e}")
            return False
    else:
        return True

def import_documents_to_data_store(articles, document_service_client, document_name_path, parent, data_store_id, branch_id):
    """
    Imports a list of articles into a data store. If an article already exists, it is updated; otherwise, it is inserted.

    Args:
        articles (list): List of articles to import.
        document_service_client (DocumentServiceClient): Client for interacting with the document service.
        document_name_path (str): Path to the document resource.
        parent (str): The parent resource path (e.g., "projects/{project_id}/locations/{location}").
        data_store_id (str): The data store ID where documents are stored.
        branch_id (str): The branch ID where documents are stored.
    """
    for article in articles:
        document_id = article['id']
        if not is_document_in_data_store(document_service_client, document_name_path, document_id):
            insert_a_single_document_to_data_store(document_id, article, parent, data_store_id, document_service_client, branch_id)
        else:
            update_a_single_document(document_service_client, document_name_path, document_id, article)

def insert_a_single_document_to_data_store(document_id, article, parent, data_store_id, document_service_client, branch_id):
    """
    Inserts a single document (article) into the data store.

    Args:
        document_id (str): The ID of the document to insert.
        article (dict): The article data to be inserted as a document.
        parent (str): The parent resource path.
        data_store_id (str): The data store ID.
        document_service_client (DocumentServiceClient): The client to interact with the document service.
        branch_id (str): The branch ID where the document is stored.
    """
    document = convert_article_to_document(article)
    if document is not None:
        try:
            response = document_service_client.create_document(
                parent=f"{parent}/dataStores/{data_store_id}/branches/{branch_id}",
                document=document,
                document_id=document_id
            )
            print(f"Document {document_id} uploaded successfully")
        except Exception as e:
            print(f"An error occurred while uploading the document: {e}")

def update_a_single_document(document_service_client, document_name_path, document_id, article):
    """
    Updates an existing document (article) in the data store.

    Args:
        document_service_client (DocumentServiceClient): Client for interacting with the document service.
        document_name_path (str): Path to the document resource.
        document_id (str): The ID of the document to update.
        article (dict): The updated article data to replace the existing document.
    """
    name = f"{document_name_path}/{document_id}"
    document = convert_article_to_document(article)
    document.name = name
    try:
        request = discoveryengine_v1beta.UpdateDocumentRequest(
            document=document
        )
        response = document_service_client.update_document(request=request)
        print(f"Document {document_id} updated")
    except NotFound as e:
        print(f"Document {document_id} not found")
    except Exception as e:
        print(f"Something went wrong when updating document: {e}")
        return False

def is_document_in_data_store(document_service_client, document_name_path, document_id):
    """
    Checks if a document with the given ID exists in the data store.

    Args:
        document_service_client (DocumentServiceClient): Client for interacting with the document service.
        document_name_path (str): Path to the document resource.
        document_id (str): The ID of the document to check.

    Returns:
        bool: True if the document exists, False otherwise.
    """
    name = f"{document_name_path}/{document_id}"
    try:
        request = discoveryengine_v1beta.GetDocumentRequest(
            name=name,
        )
        response = document_service_client.get_document(request=request)
        return True
    except NotFound as e:
        return False
    except Exception as e:
        print(f"Something went wrong when getting document: {e}")
        return False

def convert_article_to_document(article):
    """
    Converts an article dictionary into a Discovery Engine Document object.

    Args:
        article (dict): The article data.

    Returns:
        Document: The converted document object, or None if an error occurs.
    """
    try:
        struct_fields = {
            key: struct_pb2.Value(string_value=value) for key, value in article.items()
        }

        document = discoveryengine_v1beta.Document(
            struct_data=struct_pb2.Struct(fields=struct_fields)
        )
        return document
    except Exception as e:
        print(f"An error occurred while converting article object to a document: {e}")
    return None

def get_sf_knowledge_articles(access_token, domain, article_base_url):
    """
    Retrieves published Salesforce Knowledge articles.

    Args:
        access_token (str): The Salesforce access token for authentication.
        domain (str): The Salesforce domain URL.
        article_base_url (str): The base URL for accessing articles.
        

    Returns:
        list: A list of formatted Salesforce articles.
    """
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            "Accept-Language": "en-US"
        }
        params = {
            "published": "true"
        }

        url = f"{domain}/services/data/v61.0/support/knowledgeArticles?pageSize=100"
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        nextPageUrl = data['nextPageUrl']
        
        articles = []
        while True:
            for article in data['articles']:
                article_details_url = f"{domain}{article['url']}"
                article_details_response = requests.get(article_details_url, headers=headers)
                article_details_data = json.loads(article_details_response.text)
                url = f"{article_base_url}{article['id']}/view"
                formatted_article = {
                    "articleNumber": article['articleNumber'],
                    "id": article['id'],
                    "title": article['title'],
                    "lastPublishedDate": article['lastPublishedDate'],
                    "text": article_details_data['layoutItems'][0]['value'],
                    "url": url,
                }
                articles.append(formatted_article)

            if nextPageUrl:
                url = f"{domain}/{nextPageUrl}"
                response = requests.get(url, headers=headers, params=params)
                data = json.loads(response.text)
                nextPageUrl = data['nextPageUrl']
            else:
                break

        return articles
    except Exception as e:
        print(f"Something went wrong when getting knowledge articles: {e}")
        exit(1)

def generate_sf_access_token():
    """
    Generates a Salesforce access token using the OAuth2 password grant type.

    Returns:
        str: The Salesforce access token.
    """
    try:
        config = Config()
        auth_url = 'https://login.salesforce.com/services/oauth2/token'
        auth_data = {
            'grant_type': 'password',
            'client_id': config.sf_client_id,
            'client_secret': config.sf_client_secret,
            'username': config.sf_username,
            'password': f'{config.sf_password}{config.sf_security_token}',
        }

        response = requests.post(auth_url, data=auth_data)
        access_token = response.json().get('access_token')
        return access_token
    except Exception as e:
        print(f"Something went wrong when generating an access token: {e}")
        exit(1)

def main(request):
    try:
        config = Config()
        document_service_client = discoveryengine_v1beta.DocumentServiceClient()
        data_store_client = discoveryengine_v1beta.DataStoreServiceClient()
        access_token = generate_sf_access_token()
        if access_token:
            articles = get_sf_knowledge_articles(access_token, config.sf_domain, config.sf_article_base_url)
            if articles:
                data_store_created = create_data_store(config.gcp_project_id, config.gcp_location, config.data_store_id, data_store_client, config.data_store_display_name)
                if data_store_created:
                    import_documents_to_data_store(articles, document_service_client, config.document_name_path, config.parent, config.data_store_id, config.branch_id)
                    return "Document import completed.", 200
                else:
                    return "Data store not created.", 500
            else:
                return "No Salesforce Knowledge articles returned.", 404
        else:
            return "No access token returned.", 403
    except Exception as e:
        print(e)
        return str(e), 500
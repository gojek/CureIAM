from google.oauth2 import service_account
from googleapiclient import discovery
from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

def set_service_account(key_file_path=None, scopes=[]):

	return service_account.Credentials.from_service_account_file(
            key_file_path)

def get_service_account_class():

    return service_account.Credentials


def build_resource(service_name, key_file_path, version='v1'):
        """Create a ``Resource`` object for interacting with Google APIs.

        Arguments:
            service_name (str): Name of the service of resource object.
            version (str): Version of the API for resource object.

        Returns:
            googleapiclient.discovery.Resource: Resource object for
                interacting with Google APIs.
        """

        credential = set_service_account(key_file_path)

        # Entire set of service list can be obatinaed from this gcloud command
        # gcloud services list --available

        return discovery.build(service_name,
                               version,
                               credentials=credential,
                               cache_discovery=False)

def get_resource_iterator(resource, key, **list_kwargs):
    """Generate resources for specific record types. This function is useful to when API returns
    pageToken and there is need to make subsequent calls.

    Arguments:
        resource (Resource): GCP resource object.
        key (str): The key that we need to look up in the GCP
            response JSON to find the list of resources.
        key_file_path (str): Path to key file (for logging only).
        list_kwargs (dict): Keyword arguments for
            ``resource.list()`` call.
    Yields:
        dict: A GCP configuration record.
    """
    try:
        request = resource.list(**list_kwargs)

        while request is not None:
            response = request.execute()
            if key is None:
                yield response
            else:
                for item in response.get(key, []):
                    yield item
            request = resource.list_next(previous_request=request,
                                         previous_response=response)
    except Exception as e:
        _log.error('Failed to fetch resource list; key: %s; '
                   'list_kwargs: %s; '
                   'error: %s: %s', key, list_kwargs,
                    type(e).__name__, e)

def outline_gcp_project(project_index, project, zone, key_file_path):
    """Return a summary of a GCP project for logging purpose.

    Arguments:
        project_index (int): Project index.
        project (Resource): GCP Resource object of the project.
        zone (str): Name of the zone for the project.
        key_file_path (str): Path of the service account key file
            for a project.

    Returns:
        str: Return a string that can be used in log messages.

    """
    zone_log = '' if zone is None else 'zone: {}; '.format(zone)
    return ('project #{}: {} ({}) ({}); {}key_file_path: {}'
            .format(project_index, project.get('projectId'),
                    project.get('name'), project.get('lifecycleState'),
                    zone_log, key_file_path))
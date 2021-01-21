"""Plugin to read the data from the GCP IAM recommendation API
"""

import json
import logging

from google.oauth2 import service_account
from googleapiclient import discovery

from IAMRecommending import ioworkers, util


"""OAuth 2.0 scopes for Google APIs required by this plugin.

See https://developers.google.com/identity/protocols/googlescopes for
more details on OAuth 2.0 scopes for Google APIs."""
# TODO: Redefine scopes
_GCP_SCOPES = ['https://www.googleapis.com/*']

_log = logging.getLogger(__name__)


class GCPCloudIAMRecommendations:
    """GCP cloud IAM recomendation plugin."""

    def __init__(self, key_file_path, projects='*', processes=4, threads=10):
        """Create an instance of :class:`GCPCloudIAMRecommendations` plugin.

        Arguments:
            key_file_path (str): Path of the service account key file for a project.
            processes (int): Number of processes to launch.
            threads (int): Number of threads to launch in each process.

        """
        self._key_file_path = key_file_path
        self._projects = projects
        self._processes = processes
        self._threads = threads
        

        # Create credentials for python client from service account key file
        credentials = service_account.Credentials.from_service_account_file(
            self._key_file_path, scopes=_GCP_SCOPES)

        # Scan needs to be done for list of projects or all the projects
        # projects='*' indicates all projects
        if self._projects == '*':
            _log.info('Plugin started in Scan-All-Project-Mode')
            # Get the list of all the projects available
            self._projects = []
            cloudresourcemanager_service = self._build_resource(
                                            'cloudresourcemanager',
                                            'v1')
            for project in _get_resource_iterator(
                cloudresourcemanager_service.projects(),
                'projects'):
                self._projects.append(project['projectId'])
            _log.info('Projects %s', len(self._projects))

        # Service account key file also has the client email under the key
        # client_email. We will use this key file to get the client email for
        # this request.
        try:
            with open(self._key_file_path) as f:
                self._client_email = json.loads(f.read()).get('client_email')
        except OSError as e:
            self._client_email = '<unknown>'
            _log.error('Failed to read client_email from key file: %s; '
                       'error: %s: %s', self._key_file_path,
                       type(e).__name__, e)

        _log.info('Initialized; key_file_path: %s; processes: %s; threads: %s;' 
                  'projects to scan: %d',
                  self._key_file_path, 
                  self._processes, self._threads, 
                  len(self._projects))

    def read(self):
        """Return a GCP cloud infrastructure configuration record.

        Yields:
            dict: A GCP cloud infrastructure configuration record.

        """
        pass
        
        yield from ioworkers.run(self._get_projects,
                                 self._get_recommendations,
                                 self._processes,
                                 self._threads,
                                 __name__)

    def _build_resource(self, service_name, version='v1'):
        """Create a ``Resource`` object for interacting with Google APIs.

        Arguments:
            service_name (str): Name of the service of resource object.
            version (str): Version of the API for resource object.

        Returns:
            googleapiclient.discovery.Resource: Resource object for
                interacting with Google APIs.

        """
        credential = service_account.Credentials.from_service_account_file(
            self._key_file_path)

        # Entire set of service list can be obatinaed from this gcloud command
        # gcloud services list --available

        return discovery.build(service_name,
                               version,
                               credentials=credential,
                               cache_discovery=False)

    def _get_projects(self):
        """Generate tuples of record types and projects.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_resources`. Each such tuple represents a single unit
        of work that :meth:`_get_resources` can work on independently in
        its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_resources`.

        """
        try:

            for project in self._projects:
                yield ('project_record', '', project, 'global')

        except Exception as e:
            _log.error('Failed to fetch projects; key_file_path: %s; '
                       'error: %s: %s', self._key_file_path,
                       type(e).__name__, e)

    def _get_recommendations(self, record_type, project_index, project, zone=None):
        parent_string = 'projects/{project}/locations/{location}/recommenders/{recommenders}'.format(
            project=project,
            location='global',
            recommenders='google.iam.policy.Recommender'
        )

        recommendations_service = self._build_resource('recommender', 'v1')
        recommendations_iterator = _get_resource_iterator((recommendations_service
                            .projects()
                            .locations()
                            .recommenders()
                            .recommendations()), 'recommendations', parent=parent_string)
    
        for _, recommendation in enumerate(recommendations_iterator):
            yield {'GCPIAMRaw': recommendation}

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('GCP IAM Audit done')


def _get_resource_iterator(resource, key, **list_kwargs):
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
            for item in response.get(key, []):
                yield item
            request = resource.list_next(previous_request=request,
                                         previous_response=response)
    except Exception as e:
        _log.error('Failed to fetch resource list; key: %s; '
                   'list_kwargs: %s; key_file_path: %s; '
                   'error: %s: %s', key, list_kwargs,
                   key_file_path, type(e).__name__, e)
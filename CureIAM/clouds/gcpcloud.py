"""Plugin to read the data from the GCP IAM recommendation API
"""

import json
import logging

from google.oauth2 import service_account

from CureIAM import ioworkers, util


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
            _log.info('Plugin started in Scan-All-Projects-Mode')
            # Get the list of all the projects available
            self._projects = []
            cloudresourcemanager_service = util.build_resource(
                                            'cloudresourcemanager',
                                            self._key_file_path,
                                            'v1')
            for project in util.get_resource_iterator(
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
        yield from ioworkers.run(self._get_projects,
                                 self._get_recommendations,
                                 self._processes,
                                 self._threads,
                                 __name__)

    def _get_projects(self):
        """Generate tuples of record types and projects.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_recommendations`. Each such tuple represents a single unit
        of work that :meth:`_get_recommendations` can work on independently in
        its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_recommendations`.

        """
        try:

            for project in self._projects:
                yield ('project_record', '', project, 'global')

        except Exception as e:
            _log.error('Failed to fetch projects; key_file_path: %s; '
                       'error: %s: %s', self._key_file_path,
                       type(e).__name__, e)

    def _get_recommendations(self, record_type, project_index, project, zone=None):
        """Generate tuples of record as recommendation for a specific project.

        The yielded tuples when unpacked would become arguments for processor workers

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_recommendations`.

        """
        _log.info('Fetching recommendations for project : %s ...', project)

        parent_string = 'projects/{project}/locations/{location}/recommenders/{recommenders}'.format(
            project=project,
            location='global',
            recommenders='google.iam.policy.Recommender'
        )

        recommendations_service = util.build_resource('recommender',
                                                      self._key_file_path,
                                                      'v1')
        recommendations_iterator = util.get_resource_iterator((recommendations_service
                            .projects()
                            .locations()
                            .recommenders()
                            .recommendations()), 'recommendations', parent=parent_string)
        
        for _, recommendation in enumerate(recommendations_iterator):
            recommendation.update({'project': project})

            # Fetch the insights for each recommendation
            _insights = []

            for insight in recommendation.get('associatedInsights', None):
                _pattern = insight.get('insight', None)
                if _pattern:
                    i = (recommendations_service
                                .projects()
                                .locations()
                                .insightTypes()
                                .insights().get(name=_pattern).execute())
                    _insights.append(i)

            recommendation.update(
                { 'insights': _insights }
            )

            yield {
                'raw': recommendation
            }

        _log.info('Fetched recommendations for project : %s', project)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('GCP IAM Audit done')
 
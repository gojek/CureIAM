"""Plugin to process the data retrieved from `gcpcloud.IAMRecommending` plugin
"""

import json
import logging

from IAMRecommending.models.iamriskscore import IAMRiskScoreModel
from IAMRecommending.models.applyrecommendationmodel import IAMApplyRecommendationModel

_log = logging.getLogger(__name__)

class GCPIAMRecommendationProcessor:
    """SimpleProcessor plugin to perform processing on 
        gcpcloud.IAMRecommending IAMRecommendation_record."""

    def __init__(self):
        """Create an instance of :class:`GCPIAMRecommendationProcessor` plugin.
        """
        pass

    def eval(self, record):
        """Function to perform data processing.

        Arguments:
            record (dict): Record to evaluate.
                {
                    'raw': {
                        "name": "projects/{project-id}/locations/{location}/recommenders/google.iam.policy.Recommender/recommendations/{recommendation-id}",
                        "description": "Replace the current role with a smaller role to cover the permissions needed.",
                        "lastRefreshTime": "2021-01-18T08:00:00Z",
                        "primaryImpact": {
                            "category": "SECURITY"
                        },
                        "content": {
                            "operationGroups": [
                                {
                                    "operations": [
                                    {
                                        "action": "add",
                                        "resourceType": "cloudresourcemanager.googleapis.com/Project",
                                        "resource": "//cloudresourcemanager.googleapis.com/projects/565961175665",
                                        "path": "/iamPolicy/bindings/*/members/-",
                                        "value": "user:foo@bar.com",
                                        "pathFilters": {
                                        "/iamPolicy/bindings/*/condition/expression": "",
                                        "/iamPolicy/bindings/*/role": "roles/storage.objectCreator"
                                        }
                                    },
                                    {
                                        "action": "remove",
                                        "resourceType": "cloudresourcemanager.googleapis.com/Project",
                                        "resource": "//cloudresourcemanager.googleapis.com/projects/565961175665",
                                        "path": "/iamPolicy/bindings/*/members/*",
                                        "pathFilters": {
                                        "/iamPolicy/bindings/*/condition/expression": "",
                                        "/iamPolicy/bindings/*/members/*": "user:kenny.g@go-jek.com",
                                        "/iamPolicy/bindings/*/role": "roles/storage.objectAdmin"
                                        }
                                    }
                                }
                            ]
                        },
                        "stateInfo": {
                            "state": "ACTIVE"
                        },
                        "etag": "\"ef625ab631b20e49\"",
                        "recommenderSubtype": "REPLACE_ROLE",
                        "associatedInsights": [
                            {
                                "insight": "projects/{project-id}/locations/{location}/recommenders/google.iam.policy.Recommender/recommendations/{recommendation-id}"
                            }
                        ]
                    }
                }
        Yields:
            dict: Processed record.
                {
                    'GCPIAMProcessor':  {
                            'record_type': 'iam_recommendation'
                            'recommendation_name' : name,
                            'project': project,
                            'recommendation_description' : description,
                            'recommendation_action': content.operationGroups.operations[i],
                            'recommendetion_recommender_subtype': recommenderSubtype,
                            'recommendation_insights': associatedInsights
                    }
                }
        """
        # Extract the different `IAMRecommending_record.recommendation_action.value`
        # from the gcpcloud.GCPCloudIAMRecommendations

        iam_raw_record = record.get('raw', {})
        recommendation_dict = dict()

        if iam_raw_record is not None:
            recommendation_dict.update(
                {
                    'project' : iam_raw_record['project'],
                    'recommendation_id': iam_raw_record['name'],
                    'recommendation_description': iam_raw_record['description'],
                    'recommendation_actions' : iam_raw_record['content']['operationGroups'][0]['operations'],
                    'recommendetion_recommender_subtype': iam_raw_record['recommenderSubtype'],
                    'recommendation_insights': [ i.get('insights') for i in iam_raw_record['associatedInsights']]
                }
            )
            # Identify the account type on which recommendation is fetched
            # If iam_raw_record['recommenderSubtype'] is REPLACE_ROLE, then user 
            # info will be present as iam_raw_record['content']['operationGroups']['operations'] list
            _actor = ''
            _actor_total_permissions = 0
            _actor_exercised_permissions = 0
            _actor_exercised_permissions_category = ''

            for op_grp in iam_raw_record['content']['operationGroups']:
                for op in op_grp['operations']:
                    if op['action'] == 'remove':
                        _actor = op['pathFilters']['/iamPolicy/bindings/*/members/*']
                # After above parsing _actor would contain something like
                # <account_type>:<account_id>
                _actor_type, _actor = _actor.split(':')
                recommendation_dict.update(
                    {
                    'account_type': _actor_type,
                    'account_id': _actor
                    }
                )

            # Get all the Permissions the current actor have
            # insights is a list, in case of multiple insights
            # all insights will have same `currentTotalPermissionsCount`
            # So we are good to include the results from the first one
            # only.
            insights = iam_raw_record.get('insights', None)
            if insights:
                _content = insights[0].get('content', None)
                if _content:
                    _actor_exercised_permissions = len(_content.get(
                        'exercisedPermissions',
                        []
                    )) + len(
                        _content.get(
                            'inferredPermissions',
                            []
                        )
                    )
                    _actor_total_permissions = _content.get(
                        'currentTotalPermissionsCount',
                        '0'
                    )
                    _actor_exercised_permissions_category = insights[0].get(
                        'category',
                        ''
                    )

            recommendation_dict.update(
                {
                    'account_total_permissions': int(_actor_total_permissions),
                    'account_used_permissions': _actor_exercised_permissions,
                    'account_permission_insights_category': _actor_exercised_permissions_category
                }
            )   

            _res =  { 
                'raw': iam_raw_record,
                'processor':  recommendation_dict ,
                'score': IAMRiskScoreModel(recommendation_dict).score(),
                'apply_recommendation': IAMApplyRecommendationModel(recommendation_dict).model()
            }

            _res['apply_recommendation'].update(
                {
                    'safe_to_apply_score': _res['score']['safe_to_apply_recommendation_score']
                }
            )

            yield _res
            
    def done(self):
        """Perform cleanup work.
        Since this is a mock plugin, this method does nothing. However,
        a typical event plugin may or may not need to perform cleanup
        work in this method depending on its nature of work.
        """
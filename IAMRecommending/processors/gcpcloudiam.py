"""Plugin to process the data retrieved from `gcpcloud.IAMRecommending` plugin
"""

import json
import logging

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
                    'raw': { _raw_record_ }
                    'processed': {
                        'IAMRecommending_record': {
                            'record_type': 'iam_recommendation'
                            'recommendation_name' : name,
                            'recommendation_description' : description,
                            'recommendation_action': content.operationGroups.operations[i],
                            'recommendetion_recommender_subtype': recommenderSubtype,
                            'recommendation_insights': associatedInsights
                        }
                    }
                }
        """
        # Extract the different `IAMRecommending_record.recommendation_action.value`
        # from the gcpcloud.GCPCloudIAMRecommendations

        iam_raw_record = record.get('GCPIAMRaw', {})
        recommendation_dict = dict()

        if iam_raw_record is not None:
            recommendation_dict.update(
                {
                    'recommendation_name': iam_raw_record['name'],
                    'recommendation_description': iam_raw_record['description'],
                    'recommendation_actions' : iam_raw_record['content']['operationGroups'][0]['operations'],
                    'recommendetion_recommender_subtype': iam_raw_record['recommenderSubtype'],
                    'recommendation_insights': iam_raw_record['associatedInsights']
                }
            )
            yield {
                    'GCPIAMProcessor':{
                        'IAMRecommendation_record': recommendation_dict
                    }
                }
            
    def done(self):
        """Perform cleanup work.
        Since this is a mock plugin, this method does nothing. However,
        a typical event plugin may or may not need to perform cleanup
        work in this method depending on its nature of work.
        """
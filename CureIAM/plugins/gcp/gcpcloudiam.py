"""Plugin to process the data retrieved from `gcpcloud.CureIAM` plugin
"""

import json
import datetime

""" . = CureIAM which is the current module, for now it changes, to remove any depedency name incase if there is any changes folder name in the future
"""

from CureIAM.models.iamriskscore import IAMRiskScoreModel
from CureIAM.models.applyrecommendationmodel import IAMApplyRecommendationModel
from CureIAM.helpers import hlogging
from . import util_gcp #call function from same folder

# Define module-level logger.
_log = hlogging.get_logger(__name__)

class GCPIAMRecommendationProcessor:
    """SimpleProcessor plugin to perform processing on 
        gcpcloud.CureIAM IAMRecommendation_record."""

    """
        SECTION for initiation that has been done only once to generate the list of value
    """

    def __init__(self, mode_scan=False, mode_enforce=False, enforcer=None):
        """Create an instance of :class:`GCPIAMRecommendationProcessor` plugin.
        """
        self._recommendation_applied = 0
        self._recommendation_applied_today = 0

        # Checking the mode, if scan mode is on, then run the scan. If mode enforce is on, then enforce the change according to the recommendation
        self._mode_scan = mode_scan
        self._mode_enforce = mode_enforce

        # List of enforcement
        self._enforcer = enforcer

        if self._enforcer:
            # init blocklist 
            self.init_blocklist(self._enforcer)

            # init whitelist
            self.init_whitelist(self._enforcer)

            # init safe score
            self.init_safe_score(self._enforcer)

            # init cloud resources
            self.init_cloud_resource(self._enforcer)
    
    def init_blocklist(self, enforcer=None):
        # Don't perform operations on these projects
        self._apply_recommendation_blocklist_projects = enforcer.get('blocklist_projects', None)

        # Don't perform operations on these accounts_ids
        self._apply_recommendation_blocklist_accounts = enforcer.get('blocklist_accounts', None)
        self._apply_recommendation_blocklist_account_types = enforcer.get('blocklist_account_types', ['serviceAccount'])

    def init_whitelist(self, enforcer=None):
        # Perform allowlist projects
        self._apply_recommendation_allowlist_projects = enforcer.get('allowlist_projects', None)
        self._apply_recommendation_allowlist_account_types = enforcer.get('allowlist_account_types', ['user', 'group'])

    def init_safe_score(self, enforcer=None):

        # will change into this in the future
        self._apply_recommendation_min_score = {} 

        # Min recommendation apply score is 60 to default for user
        self._apply_recommendation_min_score["user"] = enforcer.get('min_safe_to_apply_score_user', 60)
        
        # Min recommendation apply score is 60 to default for groups
        self._apply_recommendation_min_score["group"] = enforcer.get('min_safe_to_apply_score_group', 60)

        # Min recommendation apply score is 60 to default for SA
        self._apply_recommendation_min_score["serviceaccount"] = enforcer.get('min_safe_to_apply_score_SA', 60) 

    def init_cloud_resource(self, enforcer=None):

        self._apply_recommendations_svc_acc_key_file = enforcer.get('key_file_path', None)

        self._cloud_resource = util_gcp.build_resource(
            service_name='cloudresourcemanager',
            key_file_path=self._apply_recommendations_svc_acc_key_file
        )
        self._recommender_resource = util_gcp.build_resource(
            service_name='recommender',
            key_file_path=self._apply_recommendations_svc_acc_key_file
        )

    """
        SECTION for initiation that has been done only once to generate the list of value
    """

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
                                        "/iamPolicy/bindings/*/members/*": "user:<user-name>@<doamin.com>",
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
        # Extract the different `CureIAM_record.recommendation_action.value`
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

            # To shorten the logging mechanism
            recommendation_info = recommendation_dict['recommendation_id'].split("/")
            # print ("{}".format(hlogging.obfuscated(recommendation_info[1])))
            # print ("{}".format(hlogging.obfuscated(recommendation_info[7])))

            # If recommendation was applied in past
            # update the risk score and safe_to_apply_
            # _score to 0

            if _res['raw']['stateInfo']['state']=='SUCCEEDED':
                _res['score'].update(
                        {
                            'risk_score': 0,
                            'over_privilege_score': 0
                        }
                    )
                
                self._recommendation_applied += 1
                # _log.info('APPLIED in the past, setting score to 0#Project:%s,Recommendations:%s', recommendation_info[1], recommendation_info[7])
            
            # enforce the recommendation before saving it in DB.
            # Also dont re-apply the recommendation is it is already applied
            if self._enforcer and _res['raw']['stateInfo']['state']=='ACTIVE':
                _log.info('ENFORCING#Project:%s,Recommendations:%s', hlogging.obfuscated(recommendation_info[1]), hlogging.obfuscated(recommendation_info[7]))
                _recomemndation_applied = self._enforce_recommendation(_res)

                if _recomemndation_applied:
                    _res['raw']['stateInfo']['state'] = 'SUCCEEDED'
                    _res['apply_recommendation'].update(
                        {
                            'recommendation_state': 'Applied',
                            'recommendation_applied_time': str(datetime.datetime.utcnow().isoformat())
                        }
                    )
                    _res['score'].update(
                        {
                            'risk_score': 0,
                            'over_privilege_score': 0
                        }
                    )
                    self._recommendation_applied_today += 1
                    _log.info('APPLIED#Project:%s,Recommendations:%s', hlogging.obfuscated(recommendation_info[1]), hlogging.obfuscated(recommendation_info[7]))
                
                else:
                    _log.info('NOT-APPLIED#Project:%s,Recommendations:%s', hlogging.obfuscated(recommendation_info[1]), hlogging.obfuscated(recommendation_info[7]))
            
            yield _res
            

    def _enforce_recommendation(self, record):
        """Method to perform Recommendation enforcement
        
        IAM recommendation doesn't have API to apply the recommendation
        directly rather we will have to create IAM resource which will
        perform the policy enforcement. This method does the same.

        Arguments:
            record(dict): dict record contaning raw + processor record

        Returns:
            bool: Indicating if the we were able to successfully apply
            recommendation or not.
        """

        """
        Flow:
        Apply IAM policy from recommender
            - success
                - mark recommendation as succeeded
                - return True
            - no
                - dont change the recommendation status
                - return False
        """
        if not self._mode_scan:
            return
        
        cloud_resource = self._cloud_resource
        recommender_resource = self._recommender_resource

        _processor_record = record.get('processor', None)
        _score_record = record.get('score', None)

        if _processor_record and _score_record:
            _project = _processor_record.get('project', None)
            _recommendation_actions = _processor_record.get('recommendation_actions', None)
            _recommendation_id = _processor_record.get('recommendation_id', None)
            _account_id = _processor_record.get('account_id')
            _account_type = _processor_record.get('account_type')
            _safety_score = _score_record.get('safe_to_apply_recommendation_score', None)

            _we_want_to_apply_recommendation = False

            # Check blacklist validation
            flag_blacklist = self._validate_blacklist(_project=_project,_account_id=_account_id, _account_type=_account_type)
            
            # Check whitelist validation
            flag_whitelist = self._validate_whitelist(_account_type=_account_type)
    
            if flag_blacklist and flag_whitelist:
                # If Recommendation is for SA, apply only for ['REMOVE_ROLE', 'REPLACE_ROLE']
                if (
                    _account_type == 'serviceAccount'
                    and _processor_record.get('recommendetion_recommender_subtype') in ['REMOVE_ROLE', 'REPLACE_ROLE']
                ):
                    _we_want_to_apply_recommendation = True
                
                else:
                    if _account_type != 'serviceAccount': 
                        # If user is owner of any project dont apply recommendation
                        # <TODO> this is very bad of detecting owners, need to find better way of doing this.
                        if not 'owner' in str(record['raw']['content']['operationGroups']):
                            _we_want_to_apply_recommendation = True

                _we_want_to_apply_recommendation = self._validate_safety_score(_account_type=_account_type, _safety_score=_safety_score)
                

            if _we_want_to_apply_recommendation:
                # Execute recommendation
                _log.info('SHOULD BE APPLIED TO TARGET=project:%s,account:%s,account_type(%s)',
                          hlogging.obfuscated(_project),
                          hlogging.obfuscated(_account_id),
                          _account_type)
                if self._mode_enforce:
                    _log.info('XXX# END of enforcing mode #XXX\n\n')            
                    # _status = self._execute_recommendation(cloud_resource=cloud_resource, _project=_project)
                else:
                    _log.info('XXX# END of scan only mode #XXX\n\n')
                    return False
            
                # So we have applied recommendation and we are good.
                return True
        
        return False


    """
        Section for validation that has been break down into a multiple small function
    """

    def _validate_blacklist(self, _project, _account_id, _account_type): # will do the cleanup code later
        if (_project in self._apply_recommendation_blocklist_projects):
            _log.warn("Project %s is in excluded list", hlogging.obfuscated(_project))
            return False

        if (_account_id in self._apply_recommendation_blocklist_accounts):
            _log.warn("Account %s is in excluded list", hlogging.obfuscated(_account_id))
            return False

        if (_account_type in self._apply_recommendation_blocklist_account_types):
            _log.warn("Account type %s is in excluded list", _account_type)
            return False

        return True

    def _validate_whitelist(self, _account_type):
        if (_account_type in self._apply_recommendation_allowlist_account_types):
            return True

        return False

    def _validate_safety_score(self, _account_type, _safety_score): # Logic from defining whether we'll remove or not based on the pre-configuration score
        
        _account_type = _account_type.lower()
        std_min_score = self._apply_recommendation_min_score[_account_type]

        _log.info("GCP Recommendation Safety Score(%s) >= Minimum Score Accepted(%s)", _safety_score, std_min_score)

        if _safety_score >= std_min_score:
            return True

        return False


    """
        SECTION for execute in GCP
    """
    def _execute_recommendation(self,cloud_resource, _project): #will do more cleanup

        _policies = (
            cloud_resource.projects()
            .getIamPolicy(
                resource=_project,
                body={"options": {"requestedPolicyVersion": "1"}}
            ).execute()
        )

        _updated_policies = _policies

        for _recommendation_action in _recommendation_actions:
            if _recommendation_action.get('action') == 'remove':
                member = (
                    _recommendation_action.get('pathFilters')
                    .get('/iamPolicy/bindings/*/members/*')
                )
                role = (
                    _recommendation_action.get('pathFilters')
                    .get('/iamPolicy/bindings/*/role')
                )
                _updated_policies = self.modify_policy_remove_member(
                    _updated_policies,
                    role,
                    member
                )
                
            elif _recommendation_action.get('action') == 'add':
                member = _recommendation_action.get('value')
                role = (
                    _recommendation_action.get('pathFilters')
                    .get('/iamPolicy/bindings/*/role')
                )
                _updated_policies = self.modify_policy_add_member(
                    _updated_policies,
                    role,
                    member
                )
                

        #Apply the policies present in recommendations
        policy = (
            cloud_resource.projects()
            .setIamPolicy(resource=_project, body={'policy': _updated_policies})
            .execute()
        )
        # print(policy)

        # Update the recommendation status.
        status = (
            recommender_resource
            .projects()
            .locations()
            .recommenders()
            .recommendations()
            .markSucceeded(
                body={
                    'etag': record.get('raw').get('etag'),
                    'stateMetadata': {
                        'reviewed-by': 'cureiam',
                        'owned-by': 'security'
                    }
                },
                name=_recommendation_id)
            .execute()
        )

        return _status

    def modify_policy_remove_member(self, policy, role, member):
        """Removes a  member from a role binding."""
        try:
            binding = next(b for b in policy["bindings"] if b["role"] == role)
            if "members" in binding and member in binding["members"]:
                binding["members"].remove(member)
        except StopIteration:
            # Policy removed in previous iterations
            pass
        return policy

    def modify_policy_add_member(self, policy, role, member):
        """Adds a new role binding to a policy."""
        binding = {"role": role, "members": [member]}
        policy["bindings"].append(binding)
        return policy
            
    def done(self):
        """Perform cleanup work.
        Since this is a mock plugin, this method does nothing. However,
        a typical event plugin may or may not need to perform cleanup
        work in this method depending on its nature of work.
        """
        _log.info('Recommendation applied: %s; Recommendations applied today: %s',
                  self._recommendation_applied, self._recommendation_applied_today)
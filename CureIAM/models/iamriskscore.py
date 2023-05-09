""" IAM Risk score model class implementation
"""

from CureIAM.helpers import hlogging

_log = hlogging.get_logger(__name__)

class IAMRiskScoreModel:
    """IAMRiskScoreModel plugin for GCP IAM Recommendation records."""

    def __init__(self, record):
        """Create an instance of :class:`IAMRiskScoreModel` plugin.
        
        This model class generates scores for the recommendation record.
        Arguments:
            record: dict for GCP record
        """
        self._record = record

        self._score = {
            'safe_to_apply_recommendation_score': None,
            'safe_to_apply_recommendation_score_factors': None,
            'risk_score': None,
            'risk_score_factors': None,
        }

    def score(self):
        """This function will return the score for a specific record
        This will work on the paramters and will create risk score and
        safe_to_apply_score
        
        parameters:
        - account_type:
            - service_account
            - user_account
            - group_account
        - suggestion_type:
            - REMOVE_ROLE
            - REPLACE_ROLE
            - REPLACE_ROLE_CUSTOMIZABLE
        - recommendation_impact_type:
            - Security
        - inferred_parameters:
            - used_permissions
            - total_permissions

        inferences:
        - helpful_in_collector_enforement:
            - safe_to_apply_recommendation_score ∝ (account_type == {user, group})
            - safe_to_apply_recommendation_score ∝ (last time permissions used)
            - safe_to_apply_recommendation_score 1/∝ (account_type == {service_account, terraform_account, provisioned throught IaC scripts})
            - safe_to_apply_recommendation_score ∝ (suggestion_type == {REMOVE_ROLE}
            - safe_to_apply_recommendation_score 1/∝ (suggestion_type == {REPLACE_ROLE, REPLACE_ROLE_CUSTOMIZABLE})
            - safe_to_apply_recommendation_score 1/∝ (excess_permissions) -- Code Cracking changes ??
        - helpful_in_auditing_dashabord:
            - risk_index ∝ (account_type == {account_type == service_account})
            - risk_index 1/∝ (account_type == {user, group})
            - risk_index ∝ {excess_permissions}
            - risk_index ∝ {recommendation_impact_type}
            - risk_index ∝ {total_permissions}
        """
        # print (self._record)

        _account_type = self._record['account_type']
        _suggestion_type = self._record['account_permission_insights_category']
        _used_permissions = int(self._record['account_used_permissions'])
        _total_permissions = int(self._record['account_total_permissions'] if self._record['account_total_permissions'] is not None else _used_permissions + 1)

        _excess_permissions = _total_permissions - _used_permissions
        # In case excess permissions are 0, make sure the excess permissions are set to 1, other wise this
        # will throw error in production.
        if _excess_permissions < 1 :
            _excess_permissions = 1

        if _total_permissions < 1 :
            _total_permissions = 1
           
        _excess_permissions_percent = _excess_permissions / _total_permissions

        safe_to_apply_recommendation_score = 0

        # Based on the parameters above lets calculate safety
        if _account_type == 'user': 
            safe_to_apply_recommendation_score = 60
        elif _account_type == 'group':
            safe_to_apply_recommendation_score = 30
        else:
            safe_to_apply_recommendation_score = 0
        
        if _suggestion_type == 'REMOVE_ROLE':
            safe_to_apply_recommendation_score += 30
        elif _suggestion_type == 'REPLACE_ROLE':
            safe_to_apply_recommendation_score += 20
        else:
            safe_to_apply_recommendation_score += 10
        
        safe_to_apply_recommendation_score /= _excess_permissions_percent 

        self._score.update(
            {
                'safe_to_apply_recommendation_score': round(safe_to_apply_recommendation_score),
                'safe_to_apply_recommendation_score_factors': 3
            }
        )
        
        risk_score = 0
        # Based on the parameters above lets calculate risk_profile
        # Risk can be calculated as compound function ??
        # (1+r)^n 
        n = {
            'user': 2,
            'group': 3,
            'serviceAccount': 5
        }
        r = _excess_permissions / _total_permissions
        risk_score = r**n[_account_type] * 100

        self._score.update(
            {
                'risk_score': round(risk_score),
                'risk_score_factors': 2
            }
        )
        self._score.update(
            {
                'over_privilege_score': round(_excess_permissions_percent * 100)
            }
        )
        return self._score
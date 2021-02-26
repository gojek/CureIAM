"""IAM Risk score model class implementation
"""

import logging

_log = logging.getLogger(__name__)

class IAMApplyRecommendationModel:
    """IAMRiskScoreModel plugin for GCP IAM Recommendation records."""

    def __init__(self, record):
        """Create an instance of :class:`IAMRiskScoreModel` plugin.
        
        This model class generates scores for the recommendation record.
        Arguments:
            record: dict for GCP record
        """
        self._record = record

        self._model = {
            'recommendation_id': record['recommendation_id'],
            'project_id': record['project'],
            'account_type': record['account_type'],
            'account_id': record['account_id'],
            'safe_to_apply_score': None,
            'recommendation_state': None,
            'recommendation_applied_time': None
        }

        # There should be three different types of recommendation state
        # applied by IAMRecommending/Claimed/Will not be applied


    def model(self):
        """This function will create model for applyRecommendation 
        functionality."""
        return self._model
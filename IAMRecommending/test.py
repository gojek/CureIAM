from google.oauth2 import service_account
from googleapiclient import discovery

credentials = service_account.Credentials.from_service_account_file(
            '../sec-infra-svc.json')


service = discovery.build("recommender",
                        'v1',
                        credentials=credentials,
                        cache_discovery=False)


'''
http GET "https://recommender.googleapis.com/v1/projects/${PROJECT_ID}/locations/global/recommenders/google.iam.policy.Recommender/recommendations?pageSize=${PAGE_SIZE}&pageToken=${PAGE_TOKEN}&filter=${FILTER}" "Authorization: Bearer ${ACCESS_TOKEN}"
'''
# recommender discovery doc location
# res = service.projects().locations().recommenders().recommendations().list(
#     parent='projects/565961175665/locations/global/recommenders/google.iam.policy.Recommender'
# ).execute()

res = service.projects().locations().recommenders().recommendations().list(
    parent='projects/sec-infra/locations/global/recommenders/google.iam.policy.Recommender'
).execute()

print(res)
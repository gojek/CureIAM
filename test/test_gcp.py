from google.oauth2 import service_account
from googleapiclient import discovery

def main(argv):
    saccount = argv.saccount
    project = argv.project

    credentials = service_account.Credentials.from_service_account_file(
            saccount)

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

    str_project = 'projects/{}/locations/global/recommenders/google.iam.policy.Recommender'.format(project)

    res = service.projects().locations().recommenders().recommendations().list(
        parent=str_project
    ).execute()

    print(res)

if __name__== "__main__":
    import sys, argparse
    parser = argparse.ArgumentParser(description='Testing gcloud credentials & permission')
    parser.add_argument('--saccount','-s', nargs='?', default='cureiamSA.json',help='Service account json file')
    parser.add_argument('--project','-p', nargs='?', default='something',help='Project name')
    args = parser.parse_args()
    main(args)

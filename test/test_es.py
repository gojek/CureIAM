from datetime import datetime
from elasticsearch import Elasticsearch
ghost = '127.0.0.1'
gport = 9200
gusername = '<username>' 
gpassword = '<password>'
gscheme = 'http'

def main(argv):
    host = argv.host if argv.host != None else ghost
    port = argv.port if argv.port != None else gport
    username = argv.username if argv.username != None else gusername
    password = argv.password if argv.password != None else gpassword
    scheme = argv.scheme if argv.scheme != None else gscheme

    es = Elasticsearch([{'host': host, 'port': port, 'scheme': scheme}], http_auth=(username, password))

    doc = {
        'author': 'author_name',
        'text': 'Interensting content...',
        'timestamp': datetime.now(),
    }
    resp = es.index(index="test-index", id=1, document=doc)
    print(resp['result'])


if __name__== "__main__":
    import sys, argparse
    parser = argparse.ArgumentParser(description='Testing ELK connection')
    parser.add_argument('--host','-t', nargs='?', default=None,help='Host')
    parser.add_argument('--port','-p', nargs='?', default=None,help='Port')
    parser.add_argument('--username','-u', nargs='?', default=None,help='ELK Username')
    parser.add_argument('--password','-c', nargs='?', default=None,help='ELK Password')
    parser.add_argument('--scheme','-s', nargs='?', default=None,help='http or https')
    args = parser.parse_args()
    main(args)

# simple app to allow GraphiQL interaction with the schema and verify it is
# structured how it ought to be. 
from flask import Flask, jsonify, request
from flask_graphql import GraphQLView
from flask.views import MethodView
from schema import schema
from ac_schema import ac_schema
import graphene
import urllib2

app = Flask(__name__)
app.debug = True

# Function to handle access control allow headers
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response

app.after_request(add_cors_headers)

sample_fma_body_site = {"description": "The FMA body site related to the sample", "doc_type": "cases", "field": "samples.fma_body_site", "full": "cases.fma_body_site", "type": "string"}
project_name = {"description": "The Project Name", "doc_type": "cases", "field": "project.name", "full": "cases.project.name", "type": "string"}

@app.route('/gql/_mapping', methods=['GET'])
def get_maps():
    add_cors_headers
    res = jsonify({"sample.fma_body_site": sample_fma_body_site, "project.name": project_name})
    return res

@app.route('/cases', methods=['GET','OPTIONS'])
def get_cases():
    
    filters = request.args.get('filters')
    from_num = request.args.get('from')
    size = request.args.get('size')
    sort = request.args.get('sort')

    if(request.args.get('expand')):
        facets = request.args.get('expand')
        return jsonify({"expand": filters})

    # Processing autocomplete here as well as finding counts for the set category
    if(request.args.get('facets')):
        acProp = request.args.get('facets').split('.') # expects something like... sample.fma_body_site
        n = acProp[0].capitalize() # change to... Sample
        p = acProp[1].capitalize() # change to... Fma_body_site
        p.replace("_","") # change to... Fmabodysite
        acs = '%s%s' % (n,p) # build... SampleFmabodysite
        # Construct the query that finds and returns GQL
        beg = "http://localhost:5000/ac_schema?query=%7Bpagination%7Bcount%2Csort%2CfromNum%2Cpage%2Ctotal%2Cpages%2Csize%7Daggregations%7B"
        mid = acs
        end = "%7Bbuckets%7Bkey%2CdocCount%7D%7D%7D%7D"
        url = '%s%s%s' % (beg,mid,end)
        response = urllib2.urlopen(url)
        return response.read()

    else:
        return jsonify({"filters": filters})

@app.route('/status', methods=['GET','OPTIONS'])
def get_status():
    return 'hi'

@app.route('/status/user', methods=['GET','OPTIONS','POST'])
def get_status_user():
    return 'hi'

@app.route('/files', methods=['GET','OPTIONS'])
def get_files():
    return 'hi'

@app.route('/projects', methods=['GET','POST'])
def get_project():
    return 'hi'

@app.route('/annotations', methods=['GET','OPTIONS'])
def get_annotation():
    return 'hi'

@app.route('/ui/search/summary', methods=['GET','OPTIONS','POST'])
def get_ui_search_summary():
    return 'hi'

app.add_url_rule(
    '/casesGQL',
    view_func=GraphQLView.as_view(
        'graphqlCases',
        schema=schema,
        graphiql=True
    )
)

app.add_url_rule(
    '/filesGQL',
    view_func=GraphQLView.as_view(
        'graphqlFiles',
        schema=schema,
        graphiql=False
    )
)

app.add_url_rule(
    '/ac_schema',
    view_func=GraphQLView.as_view(
        'ac_graphql',
        schema=ac_schema,
        graphiql=True
    )
)

if __name__ == '__main__':
    app.run(threaded=True)

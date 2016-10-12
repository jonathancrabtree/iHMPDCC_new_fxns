# simple app to allow GraphiQL interaction with the schema and verify it is
# structured how it ought to be. 
from flask import Flask, jsonify, request, abort, redirect
from flask_graphql import GraphQLView
from flask.views import MethodView
from sum_schema import sum_schema
from ac_schema import ac_schema
from files_schema import files_schema
from table_schema import table_schema
from indiv_files_schema import indiv_files_schema
from models import get_url_for_download
import graphene
import urllib2
import sys

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

sample_fma_body_site = {"description": "The FMA body site related to the sample", "doc_type": "cases", "field": "SampleFmabodysite", "full": "cases.SampleFmabodysite", "type": "string"}
project_name = {"description": "The Project Name", "doc_type": "cases", "field": "ProjectName", "full": "cases.ProjectName", "type": "string"}

@app.route('/gql/_mapping', methods=['GET'])
def get_maps():
    add_cors_headers
    res = jsonify({"cases.SampleFmabodysite": sample_fma_body_site, "cases.ProjectName": project_name})
    return res

@app.route('/cases', methods=['GET','OPTIONS'])
def get_cases():
    
    filters = request.args.get('filters')
    from_num = request.args.get('from')
    size = request.args.get('size')
    order = request.args.get('sort')
    url = ""

    if(request.args.get('expand')): # Here need to process simple/advanced queries, handling happens at GQL
        p1 = "http://localhost:5000/ac_schema?query=%7Bpagination(cy%3A%22"
        p2 = "%22%2Cs%3A"
        p3 = "%2Cf%3A"
        p4 = ")%7Bcount%2Csort%2Cfrom%2Cpage%2Ctotal%2Cpages%2Csize%7D%2Chits(cy%3A%22"
        p5 = "%22%2Cs%3A"
        p6 = "%2Co%3A%22"
        p7 = "%22%2Cf%3A"
        p8 = ")%7Bproject%7Bproject_id%2Cdisease_type%2Cprimary_site%7D%2Ccase_id%7Daggregations%7BProjectName%7Bbuckets%7Bkey%2Cdoc_count%7D%7DSampleFmabodysite%7Bbuckets%7Bkey%2Cdoc_count%7D%7D%7D%7D"
        if len(filters) < 3:
            url = "%s%s%s%s%s%s%s%s%s%s%s%s" % (p1,p2,size,p3,from_num,p4,p5,size,p6,p7,from_num,p8)
        else:
            # HACK until I figure out portal syntax, can use new pie charts to lay foundation for this change
            filters = filters.replace("cases.ProjectName","Project.name")
            filters = filters.replace("cases.SampleFmabodysite","Sample.body_site")
            filters = filters.replace('"','|')
            url = "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (p1,filters,p2,size,p3,from_num,p4,filters,p5,size,p6,order,p7,from_num,p8)
        response = urllib2.urlopen(url)
        r = response.read()
        return ('%s, "warnings": {}}' % r[:-1])

    # Processing autocomplete here as well as finding counts for the set category
    elif(request.args.get('facets')):
        beg = "http://localhost:5000/ac_schema?query=%7Bpagination%7Bcount%2Csort%2Cfrom%2Cpage%2Ctotal%2Cpages%2Csize%7D%2Chits%7Bproject%7Bproject_id%2Cdisease_type%2Cprimary_site%7D%7Daggregations%7B"
        mid = request.args.get('facets')
        end = "%7Bbuckets%7Bkey%2Cdoc_count%7D%7D%7D%7D"
        url = '%s%s%s' % (beg,mid,end)
        response = urllib2.urlopen(url)
        r = response.read()
        return ('%s, "warnings": {}}' % r[:-1])

    else:
        return jsonify({"data": {"hits": [], "pagination": {"count": 0, "sort": "case_id.raw:asc", "from": 1, "page": 1, "total": 166, "pages": 166, "size": 0}}, "warnings": {}, "filters": filters})


# Route for specific cases endpoints that associates with various files
@app.route('/cases/<case_id>', methods=['GET','OPTIONS'])
def get_case_files(case_id):
    id = '"%s"' % case_id
    p1 = 'http://localhost:5000/files_schema?query=%7Bproject(id%3A'
    p2 = ')%7Bproject_id%2Cname%7D%2Cfiles(id%3A'
    p3 = ')%7Bdata_type%2Cfile_name%2Cdata_format%2Caccess%2Cfile_id%2Cfile_size%7D%2Ccase_id(id%3A'
    p4 = ')%2Csubmitter_id%7D'
    url = '%s%s%s%s%s%s%s' % (p1,id,p2,id,p3,id,p4) # inject ID into query
    response = urllib2.urlopen(url)
    r = response.read()
    return ('%s, "warnings": {}}' % r[:-1])

@app.route('/files/<file_id>', methods=['GET','OPTIONS'])
def get_file_metadata(file_id):
    beg = "http://localhost:5000/indiv_files_schema?query=%7BfileHit(id%3A%22"
    end = "%22)%7Bdata_type%2Cfile_name%2Cfile_size%2Cdata_format%2Canalysis%7Bupdated_datetime%2Cworkflow_type%2Canalysis_id%2Cinput_files%7Bfile_id%7D%7D%2Csubmitter_id%2Caccess%2Cstate%2Cfile_id%2Cdata_category%2Cassociated_entities%7Bentity_id%2Ccase_id%2Centity_type%7D%2Ccases%7Bproject%7Bproject_id%7D%2Ccase_id%7D%2Cexperimental_strategy%7D%7D"
    url = "%s%s%s" % (beg,file_id,end)
    response = urllib2.urlopen(url)
    r = response.read()
    trimmed_r = r.replace(':{"fileHit"',"") # HACK for formatting
    final_r = trimmed_r[:-1]
    return ('%s, "warnings": {}}' % final_r[:-1])

@app.route('/status', methods=['GET','OPTIONS'])
def get_status():
    return 'hi'

@app.route('/status/user', methods=['OPTIONS'])
def get_status_user():
    return 'hi'

@app.route('/status/user', methods=['GET','OPTIONS','POST'])
def get_status_user_unauthorized():
    abort(401)

@app.route('/status/api/data', methods=['GET','OPTIONS','POST'])
def get_status_api_data():
    id = request.form.get('ids')
    return redirect(get_url_for_download(id))

@app.route('/files', methods=['GET','OPTIONS','POST'])
def get_files():
    url = "http://localhost:5000/table_schema?query=%7Bpagination%7Bcount%2Csort%2Cfrom%2Cpage%2Ctotal%2Cpages%2Csize%7D%2Chits%7Bdata_type%2Cfile_name%2Cdata_format%2Csubmitter_id%2Caccess%2Cstate%2Cfile_id%2Cdata_category%2Cfile_size%2Ccases%7Bproject%7Bproject_id%2Cname%7D%2Ccase_id%7Dexperimental_strategy%7D%2Caggregations%7Bdata_type%7Bbuckets%7Bkey%2Cdoc_count%7D%7Ddata_format%7Bbuckets%7Bkey%2Cdoc_count%7D%7D%7D%7D"
    response = urllib2.urlopen(url)
    r = response.read()
    return ('%s, "warnings": {}}' % r[:-1])

@app.route('/projects', methods=['GET','POST'])
def get_project():
    facets = request.args.get('facets')

    # HACK - hard-code a couple of syntactically-correct return values so the UI runs error-free
    # request without facets parameter
    if facets is None:
        return """
  {"data" :
   {"hits" :
    [
      {"dbgap_accession_number": "N/A", "disease_type": "N/A", "released": true, "state": "legacy", "primary_site": "N/A", "project_id": "DEMO", "name": "HMP Demonstration Project"},
      {"dbgap_accession_number": "N/A", "disease_type": "N/A", "released": true, "state": "legacy", "primary_site": "N/A", "project_id": "HHS", "name": "HMP Healthy Human Subjects (HHS)"},
      {"dbgap_accession_number": "N/A", "disease_type": "Crohn's Disease", "released": true, "state": "legacy", "primary_site": "GI tract", "project_id": "CD", "name": "Crohn's Disease"},
      {"dbgap_accession_number": "N/A", "disease_type": "Type 2 Diabetes", "released": true, "state": "legacy", "primary_site": "Endocrine pancreas", "project_id": "T2D", "name": "Type 2 Diabetes"},
      {"dbgap_accession_number": "N/A", "disease_type": "Pre-Term Birth", "released": true, "state": "legacy", "primary_site": "N/A", "project_id": "PTB", "name": "Pre-Term Birth"}
    ],
  "pagination": {"count": 5, "sort": "summary.case_count:desc", "from": 1, "page": 1, "total": 5, "pages": 1, "size": 100}},
  "warnings": {}}
"""

    # request with facets parameter
    return """
  {"data" :
   { 
   "aggregations": { "primary_site": { "buckets": [ 
      { "key": "N/A", "doc_count": 3 } ,
      { "key": "GI tract", "doc_count": 1 } ,
      { "key": "Endocrine pancreas", "doc_count": 1 } 
     ] }},
   "hits" :
    [
      {"primary_site": "N/A", "project_id": "DEMO", "summary": { "case_count": 50, "file_count": 100 }},
      {"primary_site": "N/A", "project_id": "HHS", "summary": { "case_count": 150, "file_count": 300 }},
      {"primary_site": "GI tract", "project_id": "CD", "summary": { "case_count": 25, "file_count": 50 }},
      {"primary_site": "Endocrine pancreas", "project_id": "T2D", "summary": { "case_count": 75, "file_count": 175 }},
      {"primary_site": "N/A", "project_id": "PTB", "summary": { "case_count": 60, "file_count": 120 }}
    ],
  "pagination": {"count": 5, "sort": "summary.case_count:desc", "from": 1, "page": 1, "total": 5, "pages": 1, "size": 100},
  "warnings": {}}}
"""

@app.route('/annotations', methods=['GET','OPTIONS'])
def get_annotation():
    return 'hi'

# Calls sum_schema endpoint/GQL instance in order to return the necessary data
# to populate the pie charts
@app.route('/ui/search/summary', methods=['GET','OPTIONS','POST'])
def get_ui_search_summary():
    empty_cy = "http://localhost:5000/sum_schema?query=%7BSampleFmabodysite(cy%3A%22%22)%7Bbuckets%7Bcase_count%2Cdoc_count%2Cfile_size%2Ckey%7D%7DProjectName(cy%3A%22%22)%7Bbuckets%7Bcase_count%2Cdoc_count%2Cfile_size%2Ckey%7D%7Dfs(cy%3A%22%22)%7Bvalue%7D%7D"
    p1 = "http://localhost:5000/sum_schema?query=%7BSampleFmabodysite(cy%3A%22" # inject Cypher into body site query
    p2 = "%22)%7Bbuckets%7Bcase_count%2Cdoc_count%2Cfile_size%2Ckey%7D%7DProjectName(cy%3A%22" # inject Cypher into project name query
    p3 = "%22)%7Bbuckets%7Bcase_count%2Cdoc_count%2Cfile_size%2Ckey%7D%7Dfs(cy%3A%22" # inject Cypher into file size query
    p4 = "%22)%7Bvalue%7D%7D"
    filters = request.get_data()
    url = ""
    if filters: # only modify call if filters arg is present
        filters = filters[:-1] # hack to get rid of "filters" root of JSON data
        filters = filters[11:]
        # Next two lines guarantee URL encoding (seeing errors with urllib and hacking for demo)
        filters = filters.replace('"','|')
        filters = filters.replace(" ","%20")
        # Errors in Graphene mapping prevent the syntax I want, so ProjectName is converted to 
        # Cypher ready Project.name here (as are the other possible query parameters).
        filters = filters.replace("cases.ProjectName","Project.name")
        filters = filters.replace("cases.SampleFmabodysite","Sample.body_site")
        if len(filters) > 2: # need actual content in the JSON, not empty
            url = "%s%s%s%s%s%s%s" % (p1,filters,p2,filters,p3,filters,p4) 
        else:
            url = empty_cy # no Cypher parameters entered
    else:
        url = empty_cy
    response = urllib2.urlopen(url)
    # another hack, remove "data" root from GQL results
    r1 = response.read()[8:]
    r2 = r1[:-1]
    return r2

app.add_url_rule(
    '/sum_schema',
    view_func=GraphQLView.as_view(
        'sum_graphql',
        schema=sum_schema,
        graphiql=True
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

app.add_url_rule(
    '/files_schema',
    view_func=GraphQLView.as_view(
        'files_graphql',
        schema=files_schema,
        graphiql=True
    )
)

app.add_url_rule(
    '/table_schema',
    view_func=GraphQLView.as_view(
        'table_graphql',
        schema=table_schema,
        graphiql=True
    )
)

app.add_url_rule(
    '/indiv_files_schema',
    view_func=GraphQLView.as_view(
        'indiv_files_graphql',
        schema=indiv_files_schema,
        graphiql=True
    )
)

if __name__ == '__main__':
    app.run(threaded=True)

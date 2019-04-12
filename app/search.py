from app import app

def add_to_index(index, model):
    #currently, elasticsearch will always be running so this conditional isn't necessary
    if not app.elasticsearch:
        return
    
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    app.elasticsearch.index(index=index, doc_type=index, id=model.id, body=payload)

def remove_from_index(index, model):
    if not app.elasticsearch:
        return
    app.elasticsearch.delete(index=index, doc_type=index, id=model.id)

def query_index(index, query, page, per_page):
    if not app.elasticsearch:
        return [], 0

    #generate elasticsearch search object
    #search will return a JSON object with the search diagnostics
    search = app.elasticsearch.search(
        index=index,
        #doc_type=index,
        body = {
            'query': {
                'multi_match': {
                    'query': query, 
                    'fields': ['*']
                }
            },
            'from': (page - 1) * per_page,
            'size': per_page
        }
    )

    #all we care about are the list of IDs of objects in the 'hits' field of the JSON object
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']

# Many thanks to https://wellfire.co/blog/custom-haystack-elasticsearch-backend/ for
# the detailed sample code on how to do this. -mhuyck, 2015-08-24

from django.conf import settings
from haystack.backends.elasticsearch_backend import \
    ElasticsearchSearchBackend, ElasticsearchSearchEngine

def merge_dicts(a, b):
    """
    Merge dict b into dict a, allowing new leaf values from b to override the 
    original corresponding value found in a. Intended use is to provide a 
    flexible method of augmenting and overriding default settings maintained 
    in a dict. Code heavily borrowed from the excellent Stack Overflow 
    discussion at:
    http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
    """
    for key in b:
        if key in a and isinstance(a[key], dict) and isinstance(b[key], dict):
            merge_dicts(a[key], b[key])
        else:
            # in our case, we want b to replace a so we can override defaults
            a[key] = b[key]
    return a

class ADAGEElasticBackend(ElasticsearchSearchBackend):
    """
    Subclass ElasticsearchSearchBackend so we can make our own adjustments to 
    the settings
    """
    
    DEFAULT_ANALYZER = "snowball"
    
    def __init__(self, connection_alias, **connection_options):
        super(ADAGEElasticBackend, self).__init__(
            connection_alias, **connection_options
        )
        user_settings = getattr(settings, 'ELASTICSEARCH_INDEX_SETTINGS', {})
        if user_settings:
            es_defaults = getattr(self, 'DEFAULT_SETTINGS')
            es_defaults = merge_dicts(es_defaults, user_settings)
            setattr(self, 'DEFAULT_SETTINGS', es_defaults)
        user_analyzer = getattr(settings, 'ELASTICSEARCH_DEFAULT_ANALYZER', "")
        if user_analyzer:
            setattr(self, 'DEFAULT_ANALYZER', user_analyzer)
        user_kwargs = getattr(settings, 'ELASTICSEARCH_DEFAULT_KWARGS', "")
    
    def build_search_kwargs(self, query_string, sort_by=None, start_offset=0, end_offset=None,
                            fields='', highlight=False, facets=None,
                            date_facets=None, query_facets=None,
                            narrow_queries=None, spelling_query=None,
                            within=None, dwithin=None, distance_point=None,
                            models=None, limit_to_registered_models=None,
                            result_class=None):
        # run the superclass's implementation
        kwargs = super(ADAGEElasticBackend, self).build_search_kwargs(query_string, 
                            sort_by, start_offset, end_offset,
                            fields, highlight, facets,
                            date_facets, query_facets,
                            narrow_queries, spelling_query,
                            within, dwithin, distance_point,
                            models, limit_to_registered_models,
                            result_class)
        # modify the results with our additions before returning
        if user_kwargs:
            kwargs = merge_dicts(kwargs, user_kwargs)
        return kwargs
    
    def build_schema(self, fields):
        # run the superclass's implementation
        content_field_name, mapping = super(ADAGEElasticBackend, self).build_schema(fields)
        
        # modify the results to allow us to use our own DEFAULT_ANALYZER
        for field_name, field_class in fields.items():
            field_mapping = mapping[field_class.index_fieldname]
            
            if field_mapping['type'] == 'string' and field_class.indexed:
                if not hasattr(field_class, 'facet_for') and not \
                                field_class.field_type in ('ngram', 'edge_ngram'):
                    field_mapping['analyzer'] = self.DEFAULT_ANALYZER
            mapping.update({field_class.index_fieldname: field_mapping})
        return (content_field_name, mapping)

class ADAGEElasticsearchSearchEngine(ElasticsearchSearchEngine):
    backend = ADAGEElasticBackend

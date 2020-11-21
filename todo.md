- Read controller
- Read models
- Read paths

```py
{
    'method_type': ['GET'],
    'output': 'SampleController@one',
    'route_url': '/sample/@id',
    'request': None,
    'named_route': 'sample.one',
    'required_domain': None,
    'module_location': 'app.http.controllers',
    'list_middleware': [],
    'default_parameters': {},
    'e': False,
    'controller': <class 'app.http.controllers.SampleController.SampleController'>,
    'controller_method': 'one',
    'url_list': ['id'],
    '_compiled_regex': re.compile('^\\/sample\\/([\\w.-]+)$'),
    '_compiled_regex_end': re.compile('^\\/sample\\/([\\w.-]+)\\/$'),
    '_compiled_url': '^\\/sample\\/([\\w.-]+)\\/$'
}
```
""" Web Routes """
from masonite.routes import Get, Post

ROUTES = [
    Get('/', 'IndexController@show').name('index.show'),
    Get('/samples', 'SampleController@many').name('sample.many'),
    Get('/sample/@id', 'SampleController@one').name('sample.one'),
    Post('/samples/create', 'SampleController@create').name('sample.create')
]

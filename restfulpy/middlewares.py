
def create_router_option_extender(urls):
    def router_option_extender(options):
        from wheezy.routing import PathRouter
        from wheezy.web.middleware.routing import PathRoutingMiddleware
        path_router = PathRouter()
        path_router.add_routes(urls() if callable(urls) else urls)
        options['path_router'] = path_router
        options['path_for'] = path_router.path_for
        return PathRoutingMiddleware(path_router)

    return router_option_extender

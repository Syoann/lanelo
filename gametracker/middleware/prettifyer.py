from bs4 import BeautifulSoup


class PrettifyHtml(object):
    """HTML code prettification middleware."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            response.content = BeautifulSoup(response.content, 'html.parser').prettify()
        except:
            pass
        return response

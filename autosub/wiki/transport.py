from urllib.parse import urljoin
from typing import Dict, Optional
from requests import Request, Response, Session

from autosub.models.wiki import WikiCode, WikiPage


class WikiTransport:
    def __init__(
        self,
        *,
        base_url: str,
        user_agent: str,
    ):
        self._base_url = base_url
        self._user_agent = user_agent

    def _check_status(self, response: Response):
        if response.status_code >= 200 and response.status_code < 300:
            return
        raise Exception(f"Unexpected status code ({response.status_code}) from Wikipedia API")

    def _send_request(
        self,
        *,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, str]] = None
    ) -> Response:
        session = Session()
        request = Request(
            method=method,
            url=urljoin(self._base_url, endpoint),
            params=params,
            headers={
                'user_agent': self._user_agent,
                'Accept-Encoding': 'gzip'
            }
        )
        return session.send(request.prepare())

    def retrieve_wikipage(self, title: str) -> WikiPage:
        result = []

        response = self._send_request(
            method='GET',
            endpoint='/w/api.php',
            params={
                'action': 'query',
                'prop': 'revisions',
                'rvprop': 'content',
                'format': 'json',
                'rvslots': 'main',
                'formatversion': '2',
                'redirects': '1',
                'titles': title,
            }
        )
        self._check_status(response)
        response_content = response.json()
        pages = [
            page
            for page
            in response_content.get('query', {}).get('pages', [])
            if not page.get('missing', False)
        ]

        if len(pages) == 0:
            raise Exception(f"Wikipedia page not found for '{title}'")

        for page in pages:
            revisions = page.get('revisions', [])
            if len(revisions) == 0:
                continue
            wikitext = revisions[0].get('slots', {}).get('main', {}).get('content', None)
            if wikitext is not None:
                result.append(WikiCode(raw=wikitext))

        return WikiPage(
            title=title,
            wikicodes=result
        )

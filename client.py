import json
import urlparse

class Client(object):
    """Wraps a test client for convenience."""
    def __init__(self, test_client, with_admin=False):
        self.client = test_client
        self.with_admin = with_admin

    def _request(self, uri, fn, with_user=None, with_admin=False, to_json=True,
                 headers={}, data=None, query_string=None):
        response = fn(uri, follow_redirects=True, query_string=query_string, headers=headers, data=data)
        if to_json:
            try:
                return (json.loads(response.data), response.status_code)
            except:
                if (response.status_code == 404 or
                        response.status_code == 204 or
                        response.status_code == 401):
                    return None
                else:
                    raise Exception(response)
        return response

    def get(self, uri, with_user=None, with_admin=False, to_json=True, query_string=None):
        return self._request(uri, self.client.get, with_user=with_user,
                             with_admin=with_admin, to_json=to_json,
                             query_string=query_string)

    def post(self, uri, data={}, with_user=None, with_admin=False,
            to_json=True, from_json=True):
        headers = {}
        if from_json:
            headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        encoded_data = json.dumps(data) if from_json else data
        return self._request(uri, self.client.post, with_user=with_user,
                             with_admin=with_admin, to_json=to_json,
                             headers=headers, data=encoded_data)

    def put(self, uri, data={}, with_user=None, with_admin=False,
            to_json=True, from_json=True):
        headers = {}
        if from_json:
            headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        encoded_data = json.dumps(data) if from_json else data
        return self._request(uri, self.client.put, with_user=with_user,
                             with_admin=with_admin, to_json=to_json,
                             headers=headers, data=encoded_data)

    def delete(self, uri, with_user=None, with_admin=False):
        return self._request(uri, self.client.delete, with_user=with_user,
                             with_admin=with_admin, to_json=False)
import flask
import requests


class OAuthProvider(object):
    _ACCESS_TOKEN_METHOD = "GET"
    _ACCESS_TOKEN_URL = None
    _AUTHORISE_URL = None
    _BASE_URL = None
    _REQUEST_TOKEN_PARAMS = {}
    _RESPONSE_MAPPING = {}

    def __init__(self, name, oauth):
        self.service = oauth.remote_app(name, app_key=name, access_token_method=self._ACCESS_TOKEN_METHOD, access_token_url=self._ACCESS_TOKEN_URL,
                                        authorize_url=self._AUTHORISE_URL, base_url=self._BASE_URL, request_token_params=self._REQUEST_TOKEN_PARAMS)

    def authorise(self):
        return self.service.authorize(callback=self.callback_url, _external=True)

    def callback(self):
        response = self.service.authorized_response()
        if response is None:
            return None
        response = requests.get(self._USER_INFO_URL, headers={"Authorization": "Bearer %s" % response["access_token"]})
        if response.status_code != requests.codes.ok:
            return None
        response_json = response.json()
        user_info = self._RESPONSE_MAPPING.copy()
        for key, value in self._RESPONSE_MAPPING.items():
            user_info[key] = response_json[value]
        return user_info

    @property
    def callback_url(self):
        return flask.url_for("callback", provider=self.service.name, _external=True)


class FacebookOAuth(OAuthProvider):
    _ACCESS_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
    _AUTHORISE_URL = "https://www.facebook.com/dialog/oauth"
    _BASE_URL = "https://graph.facebook.com"
    _RESPONSE_MAPPING = {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "avatar_url": "picture"
    }


class GoogleOAuth(OAuthProvider):
    _ACCESS_TOKEN_METHOD = "POST"
    _ACCESS_TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    _AUTHORISE_URL = "https://accounts.google.com/o/oauth2/auth"
    _BASE_URL = "https://www.googleapis.com/oauth2/v4/"
    _REQUEST_TOKEN_PARAMS = {"scope": ["profile", "email"]}
    _RESPONSE_MAPPING = {
        "email": "email",
        "first_name": "given_name",
        "last_name": "family_name",
        "avatar_url": "picture"
    }
    _USER_INFO_URL = "https://www.googleapis.com/userinfo/v2/me"

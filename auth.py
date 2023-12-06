#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   auth.py --- Description
#
#   Copyright (C) 2023, Schspa, all rights reserved.
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import requests
import logging
import json
import urllib.parse
import time
from tenacity import retry, stop_after_attempt, wait_random
from loguru import logger
import keyring
import http.server
from urllib.parse import urlparse, parse_qs
import requests_cache

# https://github.com/waditu/czsc/blob/master/czsc/fsa/__init__.py
# const

@retry(stop=stop_after_attempt(3), wait=wait_random(min=1, max=5))
def request(method, url, headers, payload=None) -> dict:
    """飞书API标准请求

    :param method: 请求方法
    :param url: 请求地址
    :param headers: 请求头
    :param payload: 传参
    :return:
    """
    payload = {} if not payload else payload
    response = requests.request(method, url, headers=headers, json=payload)
    logger.debug(f"{'+' * 88}")
    logger.debug(f"URL: {url} || X-Tt-Logid: {response.headers['X-Tt-Logid']}")
    logger.debug(f"headers: {headers}")
    logger.debug(f"payload: {payload}")

    resp = {}
    if response.text[0] == '{':
        resp = response.json()
        logger.debug(f"response: {resp}")
    else:
        logger.debug(f"response: {response.text}")

    code = resp.get("code", -1)
    if code == -1:
        code = resp.get("StatusCode", -1)
    if code == -1 and response.status_code != 200:
        response.raise_for_status()
    if code != 0:
        logger.debug(f"request fail: code={code}, msg={resp.get('msg', '')}")
        raise ValueError(f"request fail: code={code}, msg={resp.get('msg', '')}")
    return resp

class UserAccessTokenException(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

pre_auth_code = None
# Define a custom request handler to process incoming requests
class MyHandler(http.server.BaseHTTPRequestHandler):
    ## https://open.feishu.cn/document/server-docs/authentication-management/login-state-management/obtain-code
    # https://open.feishu.cn/document/uQjL04CN%2fucDOz4yN4MjL3gzM?code={AuthorizationCode}&state=RANDOMSTATE

    def do_GET(self):
        global pre_auth_code

        # Parse the query string from the URL
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        # pre_auth_code = request.args.get('code')
        # trigger_uri = request.args.get('state')
        # auth.get_user_access_token(pre_auth_code)


        # Get user input from the query string
        pre_auth_code = query_params.get('code')[0]
        state = query_params.get('state')[0]

        # Process the user input (you can replace this with your logic)
        response = f"Received access_token, state: {state}"

        # Send the response to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response.encode())

# 开放接口 URI
TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
JSAPI_TICKET_URI = "/open-apis/jssdk/ticket/get"
APP_ACCESS_TOKEN_URI = "/open-apis/auth/v3/app_access_token/internal"

class FeishuAuth(object):

    def __init__(self, feishu_host, app_id, app_secret):
        self.feishu_host = feishu_host
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = ""
        self.session = requests_cache.CachedSession(os.path.join(
            os.getenv('HOME'), '.cache', 'feishu-request-cache'
        ))
        try:
            self.user_access_token_data = json.loads(keyring.get_password("feishu", "user_access_token_data"))
        except:
            self.user_access_token_data = None

    def request(self, method, url, params = {}, headers = {}, payload=None) -> dict:
        """飞书API标准请求

        :param method: 请求方法
        :param url: 请求地址
        :param headers: 请求头
        :param payload: 传参
        :return:
        """
        auth_headers = {
            "Authorization": "Bearer " + self.user_access_token,
            'Content-Type' : 'application/json; charset=utf-8'
        }
        r_headers = {**auth_headers, **headers}
        payload = {} if not payload else payload
        response = self.session.request(method, url, params = params, headers=r_headers, json=payload)
        logger.debug(f"{'+' * 88}")
        logger.debug(f"URL: {url} || X-Tt-Logid: {response.headers['X-Tt-Logid']}")
        logger.debug(f"headers: {r_headers}")
        logger.debug(f"payload: {payload}")

        resp = {}
        if response.text[0] == '{':
            resp = response.json()
            logger.debug(f"response: {resp}")
        else:
            logger.debug(f"response: {response.text}")

        code = resp.get("code", -1)
        if code == -1:
            code = resp.get("StatusCode", -1)
        if code == -1 and response.status_code != 200:
            response.raise_for_status()
        if code != 0:
            logger.debug(f"request fail: code={code}, msg={resp.get('msg', '')}")
            raise ValueError(f"request fail: code={code}, msg={resp.get('msg', '')}")
        return resp

    def get_ticket(self):
        # 获取jsapi_ticket，具体参考文档：https://open.feishu.cn/document/ukTMukTMukTM/uYTM5UjL2ETO14iNxkTN/h5_js_sdk/authorization
        self.authorize_tenant_access_token()
        url = "{}{}".format(self.feishu_host, JSAPI_TICKET_URI)
        headers = {
            "Authorization": "Bearer " + self.tenant_access_token,
            "Content-Type": "application/json",
        }
        resp = requests.post(url=url, headers=headers)
        FeishuAuth._check_error_response(resp)
        return resp.json().get("data").get("ticket", "")

    def get_tenant_access_token(self):
        if self.tenant_access_token == "":
            self.authorize_tenant_access_token()

        return self.tenant_access_token

    def authorize_tenant_access_token(self):
        # 获取tenant_access_token，基于开放平台能力实现，具体参考文档：https://open.feishu.cn/document/ukTMukTMukTM/ukDNz4SO0MjL5QzM/auth-v3/auth/tenant_access_token_internal
        url = "{}{}".format(self.feishu_host, TENANT_ACCESS_TOKEN_URI)
        req_body = {"app_id": self.app_id, "app_secret": self.app_secret}
        response = requests.post(url, req_body)
        FeishuAuth._check_error_response(response)
        self.tenant_access_token = response.json().get("tenant_access_token")

    def get_app_access_token(self):
        url = "{}{}".format(self.feishu_host, APP_ACCESS_TOKEN_URI)
        req_body = {"app_id": self.app_id, "app_secret": self.app_secret}
        response = requests.post(url, req_body)
        FeishuAuth._check_error_response(response)
        logger.debug(response.json())
        self.app_access_token = response.json().get("app_access_token")
        return self.app_access_token

    def get_user_access_token_url(self, trigger_uri = '/'):
        params = urllib.parse.urlencode({'app_id': self.app_id, 'redirect_uri': 'http://localhost:3000/user_appcess_token', 'state': trigger_uri})
        url = "{}{}?{}".format(self.feishu_host, "/open-apis/authen/v1/index", params)
        return url

    @property
    def user_access_token(self):
        global pre_auth_code
        try:
            return self.get_user_access_token()
        except UserAccessTokenException as e:
            import socketserver
            pre_auth_code = None
            target_url = self.get_user_access_token_url()
            os.system("open '{:s}'".format(target_url))
            with socketserver.TCPServer(("", 3000), MyHandler) as httpd:
                httpd.handle_request()

            if pre_auth_code is not None:
                return self.get_user_access_token(pre_auth_code)

    def get_user_access_token(self, code = None):
        '''
{
    "code": 0,
    "msg": "success",
    "data": {
        "access_token": "u-Q7JWnaIM_kRChuLfreHmpArjOEayt.5XUBJcZr.V0Gst4FdQCtvrd9sAViLXQnQgkpL19brGOjKZQTxb",
        "token_type": "Bearer",
        "expires_in": 7140,
        "name": "zhangsan",
        "en_name": "Three Zhang",
        "avatar_url": "www.feishu.cn/avatar/icon",
        "avatar_thumb": "www.feishu.cn/avatar/icon_thumb",
        "avatar_middle": "www.feishu.cn/avatar/icon_middle",
        "avatar_big": "www.feishu.cn/avatar/icon_big",
        "open_id": "ou_caecc734c2e3328a62489fe0648c4b98779515d3",
        "union_id": "on_d89jhsdhjsajkda7828enjdj328ydhhw3u43yjhdj",
        "email": "zhangsan@feishu.cn",
        "enterprise_email": "demo@mail.com",
        "user_id": "5d9bdxxx",
        "mobile": "+86130002883xx",
        "tenant_key": "736588c92lxf175d",
        "refresh_expires_in": 2591940,
        "refresh_token": "ur-oQ0mMq6MCcueAv0pwx2fQQhxqv__CbLu6G8ySFwafeKww2Def2BJdOkW3.9gCFM.LBQgFri901QaqeuL",
        "sid": "AAAAAAAAAANjgHsqKEAAEw=="
    }
}
        '''
        if self.user_access_token_data is not None:
            if time.time() <= self.user_access_token_data.get('expires_at'):
                return self.user_access_token_data.get('access_token')

        if code is None:
            raise UserAccessTokenException('No valid user_access_token')

        app_access_token = self.get_app_access_token();
        logger.debug("app_access_token: {}".format(app_access_token))
        url = "{}{}".format(self.feishu_host, '/open-apis/authen/v1/access_token')
        payload = json.dumps({
	    "code": code,
	    "grant_type": "authorization_code"
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + app_access_token
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        FeishuAuth._check_error_response(response)

        self.user_access_token_data = response.json().get('data')
        self.user_access_token_data.update({'expires_at' : time.time() + self.user_access_token_data.get('expires_in') - 5})
        keyring.set_password("feishu", "user_access_token_data", json.dumps(self.user_access_token_data))

        return self.user_access_token_data.get('access_token')
        # self.app_access_token = response.json().get("tenant_access_token")


    @staticmethod
    def _check_error_response(resp):
        # 检查响应体是否包含错误信息
        if resp.status_code != 200:
            raise resp.raise_for_status()
        response_dict = resp.json()
        code = response_dict.get("code", -1)
        if code != 0:
            logging.error(response_dict)
            raise FeishuException(code=code, msg=response_dict.get("msg"))


class FeishuException(Exception):
    # 处理并展示飞书侧返回的错误码和错误信息
    def __init__(self, code=0, msg=None):
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return "{}:{}".format(self.code, self.msg)

    __repr__ = __str__

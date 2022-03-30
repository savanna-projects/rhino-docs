import os
import selenium.webdriver.support.expected_conditions as ec

from flask import Flask, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait

app = Flask(__name__)
root_dir = os.path.dirname(os.path.abspath(__file__))


@app.errorhandler(500)
def handle_internal_error(e):
    print(e)
    return 'got an error', 500


@app.route('/api/v0/gravity/actions/<_id>', methods=['GET'])
def get(_id):
    try:
        # setup
        manifest = os.path.join(f'{root_dir}', 'manifests', f'{_id}.json')

        # read manifest
        with open(manifest) as f:
            content = f.readlines()

        # demo plugin
        return app.response_class(response=content, mimetype='application/json')
    except Exception as e:
        print(e)
        return app.response_class(status=404)


@app.route('/api/v0/gravity/actions/invoke', methods=['POST'])
def invoke():
    # setup
    action_request = request.json
    url = action_request['driverUrl']
    session_id = action_request['sessionId']

    # build
    driver = __mount_session(url, session_id)

    # factory
    if action_request['actionRule']['actionType'] == 'DemoAction':
        return __demo_action(driver, action_request)

    # get
    return app.response_class(status=404)


def __demo_action(driver: WebDriver, action_request):
    # setup
    wait = WebDriverWait(driver, timeout=15)
    action_rule = action_request['actionRule']

    # build
    locator = (By.XPATH, action_rule['elementToActOn'])
    keys = action_rule['argument']

    # invoke
    wait.until(ec.presence_of_element_located(locator)).send_keys(keys)

    # get (if you want to send back data)
    return {
        'applicationParams': {
            'externalApplicationParam1': 1,
            'externalApplicationParam2': 'application param value',
            'externalApplicationParam3': False,
        },
        'sessionParams': {
            'externalSessionParam1': 1,
            'externalSessionParam2': 'application param value',
            'externalSessionParam3': False,
        },
        'exceptions': [],
        'extractions': []
    }


def __mount_session(url: str, session_id: str) -> WebDriver:
    # the original executor from the WebDriver state
    execute = WebDriver.execute

    # override newSession command
    def local_executor(self, command, params=None):
        if command != "newSession":
            return execute(self, command, params)
        return {'success': 0, 'value': None, 'sessionId': session_id}

    # mount
    WebDriver.execute = local_executor
    new_driver = webdriver.Remote(command_executor=url, desired_capabilities={})
    new_driver.session_id = session_id

    # restore original functionality
    WebDriver.execute = execute

    # get
    return new_driver


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5003, debug=True)

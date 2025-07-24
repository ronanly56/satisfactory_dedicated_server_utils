import http.client
import json
import ssl
from datetime import datetime, time
import time as t

# Constants
server_ip = "127.0.0.1"
query_port = "7777"
api_key = "YOUR API KEY"  # See README.md on how to generate your api key for your server.
restart_interval_hours = 3  # You can change the interval here (default : 3 hours)


class SatisfactoryResponse:

    def __init__(self, status_code, data):
        self.data = data
        self.status_code = status_code


class SatisfactoryHttpClient:

    def __init__(self, ip, query_port, debug):
        # Use it if you know what you are doing,
        # I'll be using this directly from the server so no need for secure connection
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.conn = http.client.HTTPSConnection(ip, query_port, context=context)
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.debug = debug

    def set_bearer_token(self, token):
        self.headers['Authorization'] = "Bearer " + token

    def execute(self, data):
        self.conn.request("POST", "/api/v1", body=data, headers=self.headers)
        response = self.conn.getresponse()
        data = response.read()
        response_status = response.status
        decoded_data = data.decode("utf-8")
        if self.debug:
            log(self.headers)
            log("response_status=" + str(response_status) + ", decoded_data=" + decoded_data)
        if response_status == 204 or response_status == 404:
            return SatisfactoryResponse(response_status, None)
        else:
            return SatisfactoryResponse(response_status, json.loads(decoded_data))

    def is_the_server_alive(self):
        data = json.dumps({
            "function": "HealthCheck",
            "data": {
                "ClientCustomData": ""
            }
        })
        response = self.execute(data)
        return response.data["data"]["health"] == "healthy"

    def query_server_state(self):
        data = json.dumps({
            "function": "QueryServerState"
        })
        response = self.execute(data)
        if self.debug:
            log(response["data"])

    def get_server_options(self, option):
        data = json.dumps({
            "function": "GetServerOptions"
        })
        response = self.execute(data)
        return response.data["data"]["serverOptions"][option]

    def apply_server_option(self, option, new_value):
        data = json.dumps({
            "function": "ApplyServerOptions",
            "data": {
                "UpdatedServerOptions": {
                    option: new_value
                }
            }
        })
        response = self.execute(data)
        return response.status_code == 204


def convert_minutes_to_datetime(restart_minutes):
    # Converts the restart minutes (ex : FG.ServerRestartTimeSlot = 660 stand for : 660 min/60 min = 11h or 11am)
    restart_hour = restart_minutes // 60
    restart_minute = restart_minutes % 60

    # Creates a time object meant to be compared with now
    return time(hour=restart_hour, minute=restart_minute)


def is_restart_past(restart_minutes):
    restart_time = convert_minutes_to_datetime(restart_minutes)
    now = datetime.now().time()

    # True is restart_time is after now else False
    return now >= restart_time


def get_next_restart_minutes(old_restart_minutes):
    # Adds c.restart_interval_hours (ex 3 hours) * 60 minutes to the restart_minutes
    # There is 1440 minutes in a day, so the modulo resets the day if we go higher than 1440 minutes
    return int((old_restart_minutes + restart_interval_hours * 60) % 1440)


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


if __name__ == '__main__':
    # Activates request debugging
    debug = False

    client = SatisfactoryHttpClient(server_ip, query_port, debug)
    client.set_bearer_token(api_key)

    retries = 0
    success_on_update_restart_minutes = False
    while retries < 5 and success_on_update_restart_minutes is False:
        if client.is_the_server_alive():
            restart_minutes = int(float(client.get_server_options("FG.ServerRestartTimeSlot")))
            if is_restart_past(restart_minutes):
                # Set new restart time
                new_restart_minutes = get_next_restart_minutes(restart_minutes)
                log("The restart time must be updated : old=" + str(restart_minutes) + ", new=" + str(
                    new_restart_minutes))
                is_response_204 = client.apply_server_option("FG.ServerRestartTimeSlot", new_restart_minutes)
                t.sleep(2)
                restart_minutes_check = int(float(client.get_server_options("FG.ServerRestartTimeSlot")))
                success_on_update_restart_minutes = is_response_204 and restart_minutes_check == new_restart_minutes
                if success_on_update_restart_minutes:
                    log("Successfully set next restart to " + str(convert_minutes_to_datetime(new_restart_minutes)))
                if debug:
                    log("is_response_204=" + str(is_response_204) + ", restart_minutes_check=" + str(
                        restart_minutes_check) + ", new_restart_minutes=" + str(new_restart_minutes))
            else:
                # No need to change anything on this execution
                log("The restart time don't need to be updated : next_restart_time=" + str(
                    convert_minutes_to_datetime(restart_minutes)))
                success_on_update_restart_minutes = True
        else:
            # Tries once every two minutes for 5 times (10 min) so if the server is restarting, we can still update the restart time when up
            retries += 1
            log("Cannot reach server. Is the server running ? tries=" + str(retries))
            if retries < 5:
                t.sleep(120)
    if retries <= 5 and success_on_update_restart_minutes is False:
        log("Could not reach the server. Is the server running ? Aborting execution.")

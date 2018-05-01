import os
import json
import requests
from fuzzywuzzy import process


station_file = open('stations.txt', 'r')
station_data = json.load(station_file)

def lambda_handler(event, context):
    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
         return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
         return on_session_ended(event["request"], event["session"])

def on_launch(launch_request, session):
     return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "GetStatus":
        return get_metro_status()
    elif intent_name == "GetTrainTimes":
        return get_train_times(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def handle_session_end_request():
    card_title = "WMATA - Thanks"
    speech_output = "Thank you for using the DC Metro Times skill!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))

def get_welcome_response():
    session_attributes = {}
    should_end_session = False
    card_title = "WMATA Times"
    speech_output = "Welcome to the Alexa W.M.A.T.A. metro times skill. " \
                    "You can ask me for train times from any station, or " \
                    "ask me for the metro system status. "
    reprompt_text = "Please ask me for trains from a station, " \
                    "for example Foggy Bottom. "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_metro_status():
    session_attributes = {}
    card_title = "WMATA System Status"
    reprompt_text = ""
    should_end_session = False

    speech_output = "W.M.A.T.A. System Status. "

    api_url = 'https://api.wmata.com/Incidents.svc/json/Incidents'
    system_status = make_request(api_url, None)

    if len(system_status["Incidents"]) > 0:
        for i in system_status["Incidents"]:
            speech_output += i["Description"] + " "
    else:
        speech_output += "There are currently no reported problems"

    final_speech = replace_short_words(speech_output)
    return build_response(session_attributes, build_speechlet_response(
        card_title, final_speech, reprompt_text, should_end_session))

def get_train_times(intent):
    session_attributes = {}
    card_title = "Metro Departures"
    speech_output = "I'm not sure which station you wanted train times for. " \
                    "Please try again. "
    reprompt_text = "I'm not sure which station you wanted train times for. " \
                    "Try asking about Foggy Bottom or Gallery Place. "
    should_end_session = False

    if "Station" in intent["slots"] and "value" in intent["slots"]["Station"]:
        input_name = intent["slots"]["Station"]["value"]

        station_name = get_station_name(input_name)
        station_code = get_station_code(station_name)

        if station_code == "dne":
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

        card_title = "WMATA from " + station_name.title()

        departures = get_station_prediction(station_code)

        speech_output = "Train departures from " + station_name + " are as follows: "

        if len(departures["Trains"]) == 0:
            speech_output += "There are no trains currently available. "
            reprompt_text = ""
            return build_response(session_attributes, build_speechlet_response(
                card_title, speech_output, reprompt_text, should_end_session))

        for destination in departures["Trains"]:
            if destination["Min"] == "ARR":
                speech_output += get_color_string(destination["Line"]) + " line train to " + \
                                        destination["DestinationName"] + "is arriving. "
            elif destination["Min"] == "BRD":
                speech_output += get_color_string(destination["Line"]) + " line train to " + \
                                        destination["DestinationName"] + "is boarding. "
            elif destination["Min"] == "---":
                speech_output += get_color_string(destination["Line"]) + " line train to" + \
                                        destination["DestinationName"] + " has no time info. "
            elif "Min" in destination.keys():
                speech_output += get_color_string(destination["Line"]) + " line train to " + \
                                    destination["DestinationName"] + " will be here in " + \
                                    build_minute_string(destination["Min"])
        reprompt_text = ""
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def build_minute_string(input_time):
    if input_time == "":
        return "an unspecified amount of time, sorry for the missing information. "
    else:
        return input_time + get_minutes(int(input_time))

def replace_short_words(input_string):
    input_string = input_string.replace("btwn", "between")
    input_string = input_string.replace("svc", "service")
    input_string = input_string.replace("wmata.com", "wmata.com.")
    input_string = input_string.replace("&", "and")
    input_string = input_string.replace("w/", "with ")
    return input_string


def get_minutes(time):
    if time > 1:
        return " minutes. "
    return " minute. "

def get_station_name(input_string):
    station_names = list(station_data.keys())
    match = process.extractOne(input_string, station_names)
    if match[1] > 75:
        return match[0]
    else:
        return 'dne'

def get_station_code(station_string):
    if station_string == 'dne':
        return 'dne'
    else:
        return station_data[station_string]

def get_color_string(color_code):
    if color_code == "BL":
        return "blue"
    elif color_code == "SV":
        return "silver"
    elif color_code == "OR":
        return "orange"
    elif color_code == "RD":
        return "red"
    elif color_code == "GR":
        return "green"
    elif color_code == "YL":
        return "yellow"

def get_station_prediction(station_code):
    api_url = 'https://api.wmata.com/StationPrediction.svc/json/GetPrediction/'
    final_url = api_url + station_code
    station_predictions = make_request(final_url, None)
    return station_predictions

def make_request(url, params):
    api_key = os.environ['api_key_env']
    key = {'api_key': api_key}
    if params == None:
        payload = key
    else:
        payload = {**key, **params}

    return requests.get(url, payload).json()

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }

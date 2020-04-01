# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractRequestInterceptor, AbstractResponseInterceptor, AbstractExceptionHandler)
import ask_sdk_core.utils as ask_utils
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

from ask_sdk_model import Response

import os
import requests
import random

base = os.environ["AIRTABLE_BASE"]
api_key = os.environ["AIRTABLE_API_KEY"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DYNAMO_DB_TABLE_NAME = 'GET_DOWN_SKILL_DEV'
WELCOME_MESSAGE = "Welcome to Get Down, a skill for couch potatoes. Hopefully by the end of this, you’ll be able to do some squats."
HELLO_MSG = "Hello Python World from Classes!"
HELP_MSG = "You can say hello to me! How can I help?"
GOODBYE_MSG = "Goodbye!"
REFLECTOR_MSG = "You just triggered {}"
ERROR = "Sorry, I had trouble doing what you asked. Please try again."

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        attr = handler_input.attributes_manager

        print("START - ATTRIBUTES AT LAUNCH REQUEST ")
        print(attr)
        print("END - ATTRIBUTES AT LAUNCH REQUEST ")

        if "skill_use_count" in attr.persistent_attributes:
            # this is not the first time the user has opened this skill
            skill_use_count = attr.persistent_attributes["skill_use_count"] + 1
            squat_knowledge = attr.persistent_attributes["squat_knowledge"]
            situation = attr.persistent_attributes["situation"]
            last_squat_target = attr.persistent_attributes["last_squat_target"]
            next_squat_target = last_squat_target + 3

            if situation == "pending_squat_knowledge":
                WELCOME_MESSAGE = getResponseFromAirtable(handler_input)

                message = f"Welcome back! Do you know how to squat?"
            else:
                WELCOME_MESSAGE = getResponseFromAirtable(handler_input)
                message = f"{WELCOME_MESSAGE} This time, you need to get down {next_squat_target} squats. Are you ready?"
                situation = "pending_squat_start_confirmation"
        else:
            # this is the first time the user has opened this skill
            # situation = "1st time"
            WELCOME_MESSAGE = getResponseFromAirtable(handler_input)
            message = f"{WELCOME_MESSAGE} Do you know how to do a proper squat?"
            skill_use_count = 1
            squat_knowledge = "unknown"
            situation = "pending_squat_knowledge"
            last_squat_target = 2
            next_squat_target = 3

        attr.persistent_attributes.update({"skill_use_count": skill_use_count,"squat_knowledge": squat_knowledge, "situation":situation,"last_squat_target":last_squat_target,"next_squat_target":next_squat_target})

        # STORE IN PERSISTENT ATTRIBUTES, TO SAVE TO DYNAMO DB
        attr.save_persistent_attributes()
        speak_output = message

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class SetFavoriteColorIntentHandler(AbstractRequestHandler):
    """Handler for SetFavoriteColorIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SetFavoriteColorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots
        print("---- Printing Slots ----")
        # print(slots)
        logging.debug(slots)
        fav_color = slots['color_name'].value

        attr = handler_input.attributes_manager

        # STORE IN SESSION ATTRIBUTES
        attr.session_attributes.update({"fav_color": fav_color})

        # STORE IN PERSISTENT ATTRIBUTES, TO SAVE TO DYNAMO DB
        attr.persistent_attributes.update({"fav_color": fav_color})
        attr.save_persistent_attributes()

        speak_output = f"You said your favorite color is {fav_color}. I will now remember this."

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class GetFavoriteColorIntentHandler(AbstractRequestHandler):
    """Handler for GetFavoriteColorIntent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GetFavoriteColorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        attr = handler_input.attributes_manager

        # READ FROM SESSION ATTRIBUTES
        # fav_color = attr.session_attributes["fav_color"]

        # READ FROM PERISISTENT ATTRIBUTES TO RETRIEVE FROM DYNAMO DB
        fav_color = attr.persistent_attributes["fav_color"]
        speak_output = f"Your favorite color is {fav_color}"

        return (
            handler_input.response_builder
            .speak(f"{speak_output}. You can tell me your favorite color again, if you like")
            .ask("You can tell me your favorite color again, if you like")
            .response
        )

class KnowsHowToSquatHandler(AbstractRequestHandler):
    """User knows how to do the squats"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        attr = handler_input.attributes_manager

        return attr.persistent_attributes["situation"] == "pending_squat_knowledge" and ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # speak_output = HELP_MSG
        attr = handler_input.attributes_manager
        attr.persistent_attributes["squat_knowledge"] = "can_squat"
        attr.persistent_attributes["situation"] = "squat_mode"
        attr.save_persistent_attributes()

        next_squat_target = attr.persistent_attributes["next_squat_target"]

        speak_output = f"OK, drop it like it’s hot for {next_squat_target} squats. Let me know when you are done. {play_waiting_music()}"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class NeedsHelpToSquatHandler(AbstractRequestHandler):
    """User does not know how to do the squats"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        attr = handler_input.attributes_manager

        return attr.persistent_attributes["situation"] == "pending_squat_knowledge" and ask_utils.is_intent_name("AMAZON.NoIntent")(handler_input)

        # knows_how_to_squat = "squat_knowledge" in attr.persistent_attributes and attr.persistent_attributes["squat_knowledge"] == "Yes" # returns true or false

        # return knows_how_to_squat and ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # speak_output = HELP_MSG
        attr = handler_input.attributes_manager
        attr.persistent_attributes["squat_knowledge"] = "needs_help"
        speak_output = f"No worries! Stand with your feet hip width apart. Squat down like you want to sit in a chair, making sure your knees don’t bend over your toes. Try one and let me know when you’re done.{play_waiting_music()}"

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class DoneIntentHandler(AbstractRequestHandler):
    """User completed the squats"""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        attr = handler_input.attributes_manager

        # the situation is set to "squat_mode" AND the intent was either DoneIntent, or "AMAZON.YesIntent"
        return attr.persistent_attributes["situation"] == "squat_mode" and (ask_utils.is_intent_name("DoneIntent")(handler_input) or ask_utils.is_intent_name("AMAZON.YesIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        attr = handler_input.attributes_manager

        if "total_squat_count" in attr.persistent_attributes:
            # the user has done some squats in the past
            last_squat_target = attr.persistent_attributes["last_squat_target"]
            next_squat_target = attr.persistent_attributes["next_squat_target"]

            total_squat_count = attr.persistent_attributes["total_squat_count"] + last_squat_target
        else:
            # the user has NOT done any squats in the past
            last_squat_target = 2
            next_squat_target = 3
            total_squat_count = last_squat_target

        situation = "squat_done"
        # squat_level = 1

        attr.persistent_attributes["total_squat_count"] = 1
        attr.persistent_attributes.update({"total_squat_count": total_squat_count, "situation":situation,"last_squat_target":last_squat_target,"next_squat_target":next_squat_target })

        # STORE IN PERSISTENT ATTRIBUTES, TO SAVE TO DYNAMO DB
        attr.save_persistent_attributes()

        speak_output = f"Great! You have now done a total of {total_squat_count} squats. In no time you’ll have to rename yourself to buns of steel. Your next target is {next_squat_target} squats. Come back tomorrow and we’ll get down to business! See ya!"

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask(speak_output)
            .response
        )
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = HELP_MSG

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = GOODBYE_MSG

        return (
            handler_input.response_builder
            .speak(speak_output)
            .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = REFLECTOR_MSG.format(intent_name)

        return (
            handler_input.response_builder
            .speak(speak_output)
            # .ask("add a reprompt if you want to keep the session open for the user to respond")
            .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        speak_output = ERROR

        return (
            handler_input.response_builder
            .speak(speak_output)
            .ask(speak_output)
            .response
        )

class GenericRequestInterceptor(AbstractRequestInterceptor):
    """
    Log the Request
    """

    def process(self, handler_input):
        print("---- BEGIN HANDLER INPUT ----")
        print("Alexa Request: {}\n".format(handler_input.request_envelope.request))
        print("---- END HANDLER INPUT ----")

# Request and Response Loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Envelope: {}".format(
            handler_input.request_envelope))

        attr = handler_input.attributes_manager
        logger.info("Attempting to save all persistent attributes as session attributes")
        attr.session_attributes.update(attr.persistent_attributes)
        logger.info("Attempting to call the Airtable API, and saving data as session attributes")

        WELCOME_MESSAGE = getResponseFromAirtable(handler_input)

        return WELCOME_MESSAGE

class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("Response: {}".format(response))

# HELPER FUNCTIONS FOR GET DOWN SKILL
def play_waiting_music():
    return'<audio src="https://alexa-github.s3.amazonaws.com/waiting_music_2.mp3"/> Are you done?'

def getResponseFromAirtable(handler_input):
    attr = handler_input.attributes_manager
    if "skill_use_count" in attr.persistent_attributes:
        # skill_use_count = attr.persistent_attributes["skill_use_count"]
        filter_query = "filterByFormula=AND(Situation%3D%22Return%22,IsDisabled%3DFALSE())"
    else:
        filter_query = "filterByFormula=AND(Situation%3D%221st+time%22,IsDisabled%3DFALSE())"
        last_squat_target = 2
        attr.persistent_attributes.update({"last_squat_target":last_squat_target})

    final_url = f"https://api.airtable.com/v0/{base}/Welcomes?api_key={api_key}&{filter_query}"

    res = requests.get(final_url)
    json_res = res.json()
    records_found = len(json_res["records"])
    i = random.randint(0,records_found-1)

    WELCOME_MESSAGE = f'{json_res["records"][i]["fields"]["Utterance"]}'.replace("[last_squat_target]",str(attr.persistent_attributes["last_squat_target"])).replace("[next_squat_target]",str(attr.persistent_attributes["last_squat_target"]))

    attr.session_attributes.update({"responses":json_res})

    return WELCOME_MESSAGE

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.

# Skill Builder object
sb = StandardSkillBuilder(table_name=DYNAMO_DB_TABLE_NAME, auto_create_table=True)

# Add all request handlers to the skill
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(SetFavoriteColorIntentHandler())
sb.add_request_handler(GetFavoriteColorIntentHandler())
sb.add_request_handler(KnowsHowToSquatHandler())
sb.add_request_handler(NeedsHelpToSquatHandler())
sb.add_request_handler(DoneIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_request_handler(IntentReflectorHandler())

# Add response interceptor to the skill.
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Add exception handler to the skill.
sb.add_exception_handler(CatchAllExceptionHandler())

handler = sb.lambda_handler()

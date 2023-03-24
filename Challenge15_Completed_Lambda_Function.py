### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


def validate_data(age, investment_amount, risk_level, intent_request):
    # Validate age input
    if age is not None:
        age = parse_int(age)
        if age <= 0 or age >= 65:
            return build_validation_result(
                False,
                "age",
                "Your age should be greater than zero and less than 65. "
                "Please provide a valid age.",
            )

    # Validate investment amount input
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The minimum investment amount is $5000. "
                "Please provide a valid investment amount.",
            )

    # Validate risk level input
    if risk_level is not None:
        risk_levels = ["none", "low", "medium", "high"]
        if risk_level.lower() not in risk_levels:
            return build_validation_result(
                False,
                "riskLevel",
                "Your risk level should be one of the following options: none, low, medium, high. "
                "Please provide a valid risk level.",
            )

    return build_validation_result(True, None, None)

def get_rec(risk_level):
    # Determine recommended portfolio
    if risk_level.lower() == "none":
        portfolio_recommendation = "100% bonds (AGG), 0% equities (SPY)"
    elif risk_level.lower() == "low":
        portfolio_recommendation = "60% bonds (AGG), 40% equities (SPY)"
    elif risk_level.lower() == "medium":
        portfolio_recommendation = "40% bonds (AGG), 60% equities (SPY)"
    elif risk_level.lower() == "high":
        portfolio_recommendation = "20% bonds (AGG), 80% equities (SPY)"
    else:
        portfolio_recommendation = "Invalid Risk Level"
    return portfolio_recommendation



### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    # Get slot values
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    # Validate user input
    if source == "DialogCodeHook":
        slots = get_slots(intent_request)

        # Validate age
        validation_result = validate_data(age, investment_amount, risk_level, intent_request)
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Clear invalid slot
            
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        
        output_session_attributes = intent_request["sessionAttributes"]
        
        return delegate(output_session_attributes, get_slots(intent_request))
        
    portfolio_recommendation = get_rec(risk_level)
    
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you, {}, you should allocate your funds like so: {}"""
            .format(first_name, portfolio_recommendation),
        },
    )

### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")



### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)
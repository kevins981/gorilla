from copy import deepcopy
#from travel_booking import TravelAPI
from pprint import pprint
from bfcl.eval_checker.multi_turn_eval.func_source_code.travel_booking import TravelAPI


initial_state = {
    "credit_card_list": {
        "card_0064": {
            "card_number": "8293-1765-9823-0064",
            "cardholder_name": "Michael Thompson",
            "expiry_date": "12/25",
            "cvv": 123,
            "balance": 4500.0
        }
    },
    "booking_record": {
        "LA12345": {
            "flight_date": "2024-12-15",
            "destination": "Los Angeles",
            "class": "Business",
            "price": 1500.0
        }
    },
    "access_token": "abc123xyz456",
    "token_type": "Bearer",
    "token_expires_in": 3600,
    "token_scope": "read write",
    "user_first_name": "Michael",
    "user_last_name": "Thompson",
    "budget_limit": 20000.0
}
api = TravelAPI()
api._load_scenario(deepcopy(initial_state))


### set budget test

api.set_budget_limit(access_token='abc123xyz456', budget_limit=2857.14)
api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-12-15', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=660.0)
print("== after book flight")
pprint(api.get_all_states())
api.cancel_booking(access_token='abc123xyz456', booking_id='3426812')
print("== after cancel booking")
pprint(api.get_all_states())


api.revert_cancel_booking(booking_id='3426812')
print("== after revert cancel booking")
pprint(api.get_all_states())

api.revert_book_flight()
print("== after revert book flight ")
pprint(api.get_all_states())

api.revert_set_budget_limit()
print("== after revert set budget ")
pprint(api.get_all_states())

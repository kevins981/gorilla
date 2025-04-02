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
#out = api.set_budget_limit(access_token='abc123xyz456', budget_limit=2857.14)
#print(out)
#out = api.set_budget_limit(access_token='abc123xyz456', budget_limit=5000)
#print(out)
#out = api.revert_set_budget_limit()
#print(out)
#out = api.revert_set_budget_limit()
#print(out)

#### book flight test
#out = api.set_budget_limit(access_token='abc123xyz456', budget_limit=2857.14)
#out = api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-12-15', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=660.0)
#print("book 1 ", out)
#out = api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-11-10', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=1200.0)
#print("book 2 ", out)
#
#out = api.revert_book_flight()
#print("after reverting 1 ", out)
#out = api.revert_book_flight()
#print("after reverting 2 ", out)

### Register credit card
#out = api.register_credit_card(access_token='abc123xyz456', card_number="1111-2222-3333-4444", cardholder_name="Kevin S", expiration_date="11/22", card_verification_number=886)
#print(out)
#print("after registering 1")
#print(api.get_all_credit_cards())
#out = api.register_credit_card(access_token='abc123xyz456', card_number="9999-8888-7777-6666", cardholder_name="Sevin K", expiration_date="22/11", card_verification_number=661)
#print(out)
#print("after registering 2")
#print(api.get_all_credit_cards())
#
#out = api.revert_register_credit_card()
#print("after reverting 1 ", out)
#out = api.revert_register_credit_card()
#print("after reverting 2 ", out)


#### Purchase insurance
#out = api.set_budget_limit(access_token='abc123xyz456', budget_limit=2857.14)
#out = api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-12-15', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=660.0)
#print(out)
#booking_id = out['booking_id']
#print("before purchase")
#print(api.get_all_credit_cards())
#out = api.purchase_insurance(access_token='abc123xyz456', insurance_type='comprehensive', booking_id=booking_id, insurance_cost=500.0, card_id='card_0064')
#print(out)
#print("after purchase 1")
#print(api.get_all_credit_cards())
#out = api.purchase_insurance(access_token='abc123xyz456', insurance_type='comprehensive', booking_id=booking_id, insurance_cost=1500.0, card_id='card_0064')
#print(out)
#print("after purchase 2")
#print(api.get_all_credit_cards())
#
#
#out = api.revert_purchase_insurance(card_id='card_0064', insurance_cost=500.0)
#print("after revert 1")
#print(out)
#print(api.get_all_credit_cards())
#out = api.revert_purchase_insurance(card_id='card_0064', insurance_cost=1500.0)
#print("after revert 2")
#print(out)
#print(api.get_all_credit_cards())

#### Cancel booking
#out = api.set_budget_limit(access_token='abc123xyz456', budget_limit=2857.14)
#out = api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-12-15', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=660.0)
#book_id1 = out['booking_id']
#print("book 1 ", out)
#out = api.book_flight(access_token='abc123xyz456', card_id='card_0064', travel_date='2024-11-10', travel_from='RMS', travel_to='LAX', travel_class='business', travel_cost=1200.0)
#book_id2 = out['booking_id']
#print("book 2 ", out)
#pprint(api.get_all_bookings())
#
#out = api.cancel_booking(access_token='abc123xyz456', booking_id=book_id1)
#print(f"cancelled {book_id1} ", out)
#pprint(api.get_all_bookings())
#
#out = api.cancel_booking(access_token='abc123xyz456', booking_id=book_id2)
#print(f"cancelled {book_id2} ", out)
#pprint(api.get_all_bookings())
#
#out = api.revert_cancel_booking(booking_id=book_id1)
#print(f"reverted {book_id1} cancel ")
#pprint(api.get_all_bookings())
#
#out = api.revert_cancel_booking(booking_id=book_id2)
#print(f"reverted {book_id2} cancel ")
#pprint(api.get_all_bookings())


### Authentication
out = api.authenticate_travel(client_id='client_520', client_secret='rise_to_sky', refresh_token='token990125', grant_type='read_write', user_first_name='Kevin', user_last_name='Song')
print("authenticate 1 ", out)

out = api.authenticate_travel(client_id='client_520', client_secret='rise_to_sky', refresh_token='token990125', grant_type='read_write', user_first_name='Sevin', user_last_name='Kong')
print("authenticate 2 ", out)

out = api.revert_authenticate_travel()
print("reverse authenticate 1 ", out)

out = api.revert_authenticate_travel()
print("reverse authenticate 2 ", out)


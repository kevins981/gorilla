from copy import deepcopy
#from travel_booking import TravelAPI
from pprint import pprint
from bfcl.eval_checker.multi_turn_eval.func_source_code.ticket_api import TicketAPI

#close_ticket
#create_ticket
#edit_ticket
#logout
#resolve_ticket
#ticket_login


initial_state = {
        "ticket_queue": [
            {
                "id": "ticket1",
                "title": "Cancellation Issue",
                "description": "Error encountered during flight cancellation process",
                "status": "Open",
            }
        ],
        "ticket_counter": 2,
        "current_user": "Michael Thompson",
}
api = TicketAPI()
api._load_scenario(deepcopy(initial_state))

### logout
api.logout()
api.print_everything()

api.revert_logout()
print("== revert logout")
api.print_everything()

### ticket login
#api.ticket_login(username='mzhang', password='SecurePass123')
#api.print_everything()
#api.ticket_login(username='kevin', password='mypassword')
#api.print_everything()
#
#api.revert_ticket_login()
#print("== revert ticket login1")
#api.print_everything()
#api.revert_ticket_login()
#print("== revert ticket login2")
#api.print_everything()

### update ticket
#out = api.create_ticket(priority=4, title='Urgent Change in Travel Plans', description='An unexpected change has arisen, and I need to cancel my booking for the trip to the Maldives.')
#print("== Before close ticket ")
#api.print_everything()
#out = api.edit_ticket(ticket_id="ticket1", updates={'status':'Urgent edited', 'priority':5})
#print("== editd ticket1")
#out = api.edit_ticket(ticket_id=2, updates={'priority':2})
#print("== editd ticket2")
#api.print_everything()
#
#api.revert_edit_ticket()
#print("== revert edit ticket1")
#api.print_everything()
#api.revert_edit_ticket()
#print("== revert edit ticket2")
#api.print_everything()

#### resolve ticket
#out = api.create_ticket(priority=4, title='Urgent Change in Travel Plans', description='An unexpected change has arisen, and I need to cancel my booking for the trip to the Maldives.')
#print("== Before close ticket ")
#api.print_everything()
#out = api.resolve_ticket(ticket_id="ticket1", resolution="Manually fixed")
#print("== resolved ticket1")
#out = api.resolve_ticket(ticket_id=2, resolution="Gave up")
#print("== resolved ticket2")
#api.print_everything()
#
#api.revert_resolve_ticket()
#print("== revert resolved ticket1")
#api.print_everything()
#api.revert_resolve_ticket()
#print("== revert resolved ticket2")
#api.print_everything()

#### close ticket
#out = api.create_ticket(priority=4, title='Urgent Change in Travel Plans', description='An unexpected change has arisen, and I need to cancel my booking for the trip to the Maldives.')
#print("== Before close ticket ")
#api.print_everything()
#out = api.close_ticket(ticket_id="ticket1")
#print("== Closed ticket1")
#out = api.close_ticket(ticket_id=2)
#print("== Closed ticket2")
#api.print_everything()
#
#api.revert_close_ticket()
#print("== revert closed ticket1")
#api.print_everything()
#api.revert_close_ticket()
#print("== revert closed ticket2")
#api.print_everything()

### create ticket
#out = api.create_ticket(priority=4, title='Urgent Change in Travel Plans', description='An unexpected change has arisen, and I need to cancel my booking for the trip to the Maldives.')
#out = api.create_ticket(priority=2, title='Billing Concern', description='Detailed exchange with customer support regarding unexpected charge.')
#print("== After creating tickets")
#api.print_everything()
#
#out = api.revert_create_ticket()
#print("== After revert create ticket 1")
#api.print_everything()
#
#out = api.revert_create_ticket()
#print("== After revert create ticket 2")
#api.print_everything()
#
#

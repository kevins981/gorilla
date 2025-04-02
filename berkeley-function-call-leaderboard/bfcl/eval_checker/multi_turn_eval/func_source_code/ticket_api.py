from copy import deepcopy
from typing import Dict, List, Optional, Union
from pprint import pprint

DEFAULT_STATE = {
    "ticket_queue": [],
    "ticket_counter": 1,
    "current_user": None,
}


class TicketAPI:
    """
    A class representing the Ticket API for managing support tickets.

    This class provides methods for creating, retrieving, and managing
    support tickets within a ticketing system. It maintains a queue of
    tickets and handles ticket-related operations such as creation,
    status updates, and retrieval.

    Attributes:
        ticket_queue (List[Dict[str, Union[int, str]]]): A list of ticket dictionaries.
        ticket_counter (int): A counter for generating unique ticket IDs.
        current_user (Optional[str]): The currently authenticated user.
    """

    def __init__(self):
        """
        Initialize the TicketAPI instance.
        """
        self.ticket_queue: List[Dict[str, Union[int, str]]]
        self.ticket_counter: int
        self.current_user: Optional[str]
        self._api_description = "This tool belongs to the ticketing system that is part of a company, which allows users to create, view, and manage support business tickets."

        self._ticket_queue_history = []
        self._ticket_counter_history = []
        self._current_user_history = []

    def _save_history(self, obj, history) -> None:
        # Save obj into history list by creating a copy.
        # Assume history is a list that contains different versions of obj
        obj_cp = deepcopy(obj)
        history.append(obj_cp)

    def _revert(self, history) -> None:
        # Returns the reverted value
        # Remove current value
        history.pop()
        # Restore previous value
        return history[-1]

    def _load_scenario(self, scenario: dict, long_context=False) -> None:
        """
        Load a scenario into the ticket queue.

        Args:
            scenario (Dict): A dictionary containing ticket data.
        """
        DEFAULT_STATE_COPY = deepcopy(DEFAULT_STATE)
        self.ticket_queue = scenario.get("ticket_queue", DEFAULT_STATE_COPY["ticket_queue"])
        self.ticket_counter = scenario.get(
            "ticket_counter", DEFAULT_STATE_COPY["ticket_counter"]
        )
        self.current_user = scenario.get("current_user", DEFAULT_STATE_COPY["current_user"])

        self._save_history(self.ticket_queue, self._ticket_queue_history)
        self._save_history(self.ticket_counter, self._ticket_counter_history)
        self._save_history(self.current_user, self._current_user_history)

        #print(f"[DEBUG] loaded scenario. Ticker queue {self.ticket_queue}, cur user {self.current_user}")

    def create_ticket(
        self, title: str, description: str = "", priority: int = 1
    ) -> Dict[str, Union[int, str]]:
        """
        Create a ticket in the system and queue it.

        Args:
            title (str): Title of the ticket.
            description (str): Description of the ticket. Defaults to an empty string.
            priority (int): Priority of the ticket, from 1 to 5. Defaults to 1. 5 is the highest priority.

        Returns:
            id (int): Unique identifier of the ticket.
            title (str): Title of the ticket.
            description (str): Description of the ticket.
            status (str): Current status of the ticket.
            priority (int): Priority level of the ticket.
        """
        if not self.current_user:
            return {"error": "User not authenticated. Please log in to create a ticket."}
        if priority < 1 or priority > 5:
            return {"error": "Invalid priority. Priority must be between 1 and 5."}
        ticket = {
            "id": self.ticket_counter,
            "title": title,
            "description": description,
            "status": "Open",
            "priority": priority,
            "created_by": self.current_user,
        }
        self.ticket_queue.append(ticket)
        self.ticket_counter += 1

        self._save_history(self.ticket_queue, self._ticket_queue_history)
        self._save_history(self.ticket_counter, self._ticket_counter_history)

        return ticket

    def revert_create_ticket(self) -> None:
        self.ticket_queue = self._revert(self._ticket_queue_history)
        self.ticket_counter = self._revert(self._ticket_counter_history)

    def get_ticket(self, ticket_id: int) -> Dict[str, Union[int, str]]:
        """
        Get a specific ticket by its ID.

        Args:
            ticket_id (int): ID of the ticket to retrieve.

        Returns:
            id (int): Unique identifier of the ticket.
            title (str): Title of the ticket.
            description (str): Description of the ticket.
            status (str): Current status of the ticket.
            priority (int): Priority level of the ticket.
            created_by (str): Username of the ticket creator.
        """
        ticket = self._find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        return ticket

    def close_ticket(self, ticket_id: int) -> Dict[str, str]:
        """
        Close a ticket.

        Args:
            ticket_id (int): ID of the ticket to be closed.

        Returns:
            status (str): Status of the close operation.
        """
        ticket = self._find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        if ticket["status"] == "Closed":
            return {"error": f"Ticket with ID {ticket_id} is already closed."}
        ticket["status"] = "Closed"

        self._save_history(self.ticket_queue, self._ticket_queue_history)

        return {"status": f"Ticket {ticket_id} has been closed successfully."}

    def revert_close_ticket(self) -> None:
        self.ticket_queue = self._revert(self._ticket_queue_history)

    def resolve_ticket(self, ticket_id: int, resolution: str) -> Dict[str, str]:
        """
        Resolve a ticket with a resolution.

        Args:
            ticket_id (int): ID of the ticket to be resolved.
            resolution (str): Resolution details for the ticket.

        Returns:
            status (str): Status of the resolve operation.
        """
        ticket = self._find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}
        if ticket["status"] == "Resolved":
            return {"error": f"Ticket with ID {ticket_id} is already resolved."}
        ticket["status"] = "Resolved"
        ticket["resolution"] = resolution

        self._save_history(self.ticket_queue, self._ticket_queue_history)

        return {"status": f"Ticket {ticket_id} has been resolved successfully."}

    def revert_resolve_ticket(self) -> None:
        self.ticket_queue = self._revert(self._ticket_queue_history)

    def edit_ticket(
        self, ticket_id: int, updates: Dict[str, Optional[Union[str, int]]]
    ) -> Dict[str, str]:
        """
        Modify the details of an existing ticket.

        Args:
            ticket_id (int): ID of the ticket to be changed.
            updates (Dict): Dictionary containing the fields to be updated.
                - title (str) : [Optional] New title for the ticket.
                - description (str): [Optional] New description for the ticket.
                - status (str): [Optional] New status for the ticket.
                - priority (int): [Optional] New priority for the ticket.

        Returns:
            status (str): Status of the update operation.
        """
        ticket = self._find_ticket(ticket_id)
        if not ticket:
            return {"error": f"Ticket with ID {ticket_id} not found."}

        valid_fields = {"title", "description", "status", "priority"}
        invalid_fields = set(updates.keys()) - valid_fields
        if invalid_fields:
            return {"error": f"Invalid fields for update: {', '.join(invalid_fields)}"}

        for key, value in updates.items():
            if value is not None:
                ticket[key] = value

        self._save_history(self.ticket_queue, self._ticket_queue_history)

        return {"status": f"Ticket {ticket_id} has been updated successfully."}

    def revert_edit_ticket(self) -> None:
        self.ticket_queue = self._revert(self._ticket_queue_history)

    def _find_ticket(self, ticket_id: int) -> Optional[Dict[str, Union[int, str]]]:
        """
        Find a ticket by its ID.

        Args:
            ticket_id (int): ID of the ticket to find.

        Returns:
            id (int): Unique identifier of the ticket.
            title (str): Title of the ticket.
            description (str): Description of the ticket.
            status (str): Current status of the ticket.
            priority (int): Priority level of the ticket.
            created_by (str): Username of the ticket creator.
        """
        for ticket in self.ticket_queue:
            if ticket["id"] == ticket_id:
                return ticket
        return None

    def ticket_login(self, username: str, password: str) -> Dict[str, bool]:
        """
        Authenticate a user for ticket system.

        Args:
            username (str): Username of the user.
            password (str): Password of the user.

        Returns:
            success (bool): True if login was successful, False otherwise.
        """
        # In a real system, you would validate the credentials against a database
        if username and password:  # Simplified authentication
            self.current_user = username
            self._save_history(self.current_user, self._current_user_history)
            return {"success": True}

        self._save_history(self.current_user, self._current_user_history)
        return {"success": False}

    def revert_ticket_login(self) -> None:
        self.current_user = self._revert(self._current_user_history)

    def ticket_get_login_status(self) -> Dict[str, bool]:
        """
        Get the username of the currently authenticated user.

        Returns:
            username (bool): True if a user is logged in, False otherwise.

        """
        return {"username": bool(self.current_user)}

    def logout(self) -> Dict[str, bool]:
        """
        Log out the current user.

        Returns:
            success (bool): True if logout was successful, False otherwise.
        """
        if self.current_user:
            self.current_user = None
            self._save_history(self.current_user, self._current_user_history)
            return {"success": True}

        self._save_history(self.current_user, self._current_user_history)
        return {"success": False}

    def revert_logout(self) -> None:
        self.current_user = self._revert(self._current_user_history)

    def get_user_tickets(
        self, status: Optional[str] = None
    ) -> List[Dict[str, Union[int, str]]]:
        """
        Get all tickets created by the current user, optionally filtered by status.

        Args:
            status (str): [Optional] Status to filter tickets by. If None, return all tickets.

        Returns:
            id (int): Unique identifier of the ticket.
            title (str): Title of the ticket.
            description (str): Description of the ticket.
            status (str): Current status of the ticket.
            priority (int): Priority level of the ticket.
            created_by (str): Username of the ticket
        """
        if not self.current_user:
            return [{"error": "User not authenticated. Please log in to view tickets."}]

        user_tickets = [
            ticket
            for ticket in self.ticket_queue
            if ticket["created_by"] == self.current_user
        ]

        if status:
            user_tickets = [
                ticket
                for ticket in user_tickets
                if ticket["status"].lower() == status.lower()
            ]

        return user_tickets

    def print_everything(self):
        print("== Printing everything")
        print(f"ticket_queue: {self.ticket_queue}")
        print(f"ticket_counter: {self.ticket_counter}")
        print(f"current_user: {self.current_user}")

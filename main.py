import requests
import json
import prompts
import logging

# Configure logging to output to both a file and the terminal
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler for logging to a file
file_handler = logging.FileHandler('script_log.txt')
file_handler.setLevel(logging.INFO)

# Stream handler for logging to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# Log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.info("Script started.")

# Step 1: Fetch Open Tickets
# Update the domain and Auth token from UVDesk
tickets_url = "<your_domain>/api/v1/tickets"
headers = {
    'Authorization': 'Basic <Auth Token>',
    'Cookie': ''
}

# Fetch tickets
response = requests.get(tickets_url, headers=headers)

if response.status_code == 200:
    try:
        # Parse the ticket data
        data = response.json()
        tickets = data.get("tickets", [])  # Extract the 'tickets' list
        if not isinstance(tickets, list):
            logger.error("Unexpected data format: Tickets key is not a list.")
            exit()

        # Filter tickets with status "open"
        open_tickets = [
            ticket for ticket in tickets
            if ticket.get("status", {}).get("code") == "open"
        ]

        if open_tickets:
            logger.info(f"Found {len(open_tickets)} open ticket(s).")
        else:
            logger.info("No 'Open' tickets found.")
            exit()

    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw Response: {response.text}")
        exit()
else:
    logger.error(f"Failed to fetch tickets. Status Code: {response.status_code}, Response: {response.text}")
    exit()

system_message = prompts.system_message

# Step 2: Process Each Open Ticket
for ticket in open_tickets:
    ticket_id = ticket.get('id')  # Get the ticket ID
    ticket_subject = ticket.get('subject')  # Get the ticket subject
    logger.info(f"Processing Ticket ID: {ticket_id}, Subject: {ticket_subject}")

    # Step 2: Use the Subject from Open Ticket as Input for AI
    #Update the search endpoint, IndexName, and Search API key
    config = {
        "data_sources": [
            {
                "type": "azure_search",
                "parameters": {
                    "endpoint": "<Search-Endpoint>",
                    "index_name": "<IndexName>",
                    "semantic_configuration": "default",
                    "query_type": "semantic",
                    "fields_mapping": {},
                    "in_scope": True,
                    "role_information": system_message,
                    "filter": None,
                    "strictness": 3,
                    "top_n_documents": 5,
                    "authentication": {
                        "type": "api_key",
                        "key": "<Your_Search_API_KEY>"
                    }
                }
            }
        ],
        "messages": [
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": ticket_subject  # Use the subject of the open ticket
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800,
        "stop": None,
        "stream": False
    }

    # Azure OpenAI Endpoint and API Key
    openai_endpoint = "<Model_Endpoint>"
    api_key = "<API_KEY>"

    headers_ai = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    response_ai = requests.post(url=openai_endpoint, headers=headers_ai, json=config)

    if response_ai.status_code == 200:
        response_data = response_ai.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "No content found")
        logger.info(f"AI Response for Ticket ID {ticket_id}: {content}")
    else:
        logger.error(f"Error from AI for Ticket ID {ticket_id}: {response_ai.status_code} - {response_ai.text}")
        continue

    # Post AI Response to Ticket
    update_url = f"your_domain>/api/v1/ticket/{ticket_id}/thread"
    payload = json.dumps({
        "message": content,
        "actAsType": "agent",
        "actAsEmail": "admin@danish.com",
        "threadType": "reply"
    })
    headers_update = headers

    response_update = requests.post(update_url, headers=headers_update, data=payload)

    if response_update.status_code == 200:
        logger.info(f"Ticket {ticket_id} update successful.")
        update_status_url = f"your_domain>/api/v1/ticket/{ticket_id}"
        status_payload = json.dumps({"property": "status", "value": 2})
        status_response = requests.patch(update_status_url, headers=headers_update, data=status_payload)

        if status_response.status_code == 200:
            logger.info(f"Ticket {ticket_id} status updated to 'pending'.")
        else:
            logger.error(f"Error updating status for Ticket {ticket_id}: {status_response.status_code} - {status_response.text}")
    else:
        logger.error(f"Error updating Ticket {ticket_id}: {response_update.status_code} - {response_update.text}")

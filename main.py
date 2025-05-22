import base64
import mimetypes
import os
import email
import re
from email.message import EmailMessage
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from gmail_service import get_gmail_api_service


mcp = FastMCP("EmailBot")


LABEL_UNREAD = "UNREAD"
LABEL_INBOX = "INBOX"
LABEL_STARRED = "STARRED"
LABEL_SENT = "SENT"
LABEL_TRASH = "TRASH"
LABEL_SPAM = "SPAM"
LABEL_IMPORTANT = "IMPORTANT"


@mcp.tool()
def create_message(to_: str, from_: str, subject_: str, body_: str) -> Dict:
    """
    Create a base64 encoded email message without attachments.
    
    Constructs an RFC 2822 formatted email message and encodes it in base64 URL-safe format
    for the Gmail API. The message includes basic headers (To, From, Subject) and body content.
    
    Parameters:
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        
    Returns:
        Dict: A dictionary containing the base64 encoded message under the 'raw' key,
              or None if an error occurs
              
    Example:
        >>> message = create_message(
        ...     "recipient@example.com",
        ...     "me@example.com",
        ...     "Test Subject",
        ...     "This is a test email body"
        ... )
        >>> print(message['raw'])  # Base64 encoded message
    """
    try:
        message = EmailMessage()
        message.set_content(body_)
        message["To"] = to_
        message["From"] = from_
        message["Subject"] = subject_
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": encoded_message}
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def create_message_with_attachment(
    to_: str,
    from_: str,
    subject_: str,
    body_: str,
    file_paths: Union[str, List[str]]
) -> Dict:
    """
    Create a base64 encoded email message with one or multiple attachments.
    
    Constructs an RFC 2822 formatted email message with attachments, automatically detecting
    MIME types for each file. Supports both single file path (str) or multiple files (List[str]).
    
    Parameters:
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        file_paths (Union[str, List[str]]): Path(s) to attachment file(s)
        
    Returns:
        Dict: A dictionary containing the base64 encoded message under the 'raw' key,
              or None if an error occurs
              
    Example:
        >>> # Single attachment
        >>> message = create_message_with_attachment(
        ...     "recipient@example.com",
        ...     "me@example.com",
        ...     "Report",
        ...     "Please find attached report",
        ...     "/path/to/report.pdf"
        ... )
        
        >>> # Multiple attachments
        >>> message = create_message_with_attachment(
        ...     "team@example.com",
        ...     "me@example.com",
        ...     "Project Files",
        ...     "Attached are the project documents",
        ...     ["doc1.pdf", "data.xlsx", "image.jpg"]
        ... )
    """
    try:
        message = EmailMessage()
        message.set_content(body_)
        message["To"] = to_
        message["From"] = from_
        message["Subject"] = subject_

        if isinstance(file_paths, str):
            file_paths = [file_paths]

        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue

            type_subtype, _ = mimetypes.guess_type(file_path)
            if type_subtype is None:
                type_subtype = 'application/octet-stream'
            main_type, sub_type = type_subtype.split("/", 1)

            with open(file_path, "rb") as fp:
                data = fp.read()
                filename = os.path.basename(file_path)
                message.add_attachment(
                    data,
                    maintype=main_type,
                    subtype=sub_type,
                    filename=filename
                )

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": encoded_message}
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def send_message(
    user_id: str,
    to_: str,
    from_: str,
    subject_: str,
    body_: str
) -> Dict:
    """
    Send an email message without attachments using the Gmail API.
    
    Creates and immediately sends an email message through the authenticated Gmail service.
    The message is constructed and sent in a single API call.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        
    Returns:
        Dict: API response containing sent message details (id, threadId, etc.),
              or None if an error occurs
              
    Example:
        >>> response = send_message(
        ...     "me",
        ...     "client@example.com",
        ...     "my.email@example.com",
        ...     "Project Update",
        ...     "The project is on track for delivery next week."
        ... )
        >>> print(f"Message sent with ID: {response['id']}")
    """
    service = get_gmail_api_service()
    try:
        message_json = create_message(to_, from_, subject_, body_)
        if message_json:
            return (
                service.users()
                .messages()
                .send(userId=user_id, body=message_json)
                .execute()
            )
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def send_message_with_attachment(
    user_id: str,
    to_: str,
    from_: str,
    subject_: str,
    body_: str,
    file_paths: Union[str, List[str]]
) -> Dict:
    """
    Send an email message with attachments using the Gmail API.
    
    Creates and immediately sends an email message with one or more attachments through
    the authenticated Gmail service. Handles file reading, MIME type detection, and
    attachment encoding automatically.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        file_paths (Union[str, List[str]]): Path(s) to attachment file(s)
        
    Returns:
        Dict: API response containing sent message details (id, threadId, etc.),
              or None if an error occurs
              
    Example:
        >>> response = send_message_with_attachment(
        ...     "me",
        ...     "accounting@example.com",
        ...     "my.email@example.com",
        ...     "Monthly Report",
        ...     "Attached is the monthly financial report.",
        ...     ["report.pdf", "data.xlsx"]
        ... )
        >>> print(f"Message with attachments sent: {response['threadId']}")
    """
    service = get_gmail_api_service()
    try:
        message_json = create_message_with_attachment(
            to_, from_, subject_, body_, file_paths
        )
        if message_json:
            return (
                service.users()
                .messages()
                .send(userId=user_id, body=message_json)
                .execute()
            )
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def create_draft(
    user_id: str,
    to_: str,
    from_: str,
    subject_: str,
    body_: str
) -> Dict:
    """
    Create a draft email message without attachments in the user's mailbox.
    
    Creates an email draft that can be later sent or modified through the Gmail interface.
    The draft is saved in the user's drafts folder but not sent immediately.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        
    Returns:
        Dict: API response containing draft message details (id, message, etc.),
              or None if an error occurs
              
    Example:
        >>> draft = create_draft(
        ...     "me",
        ...     "team@example.com",
        ...     "manager@example.com",
        ...     "Meeting Notes",
        ...     "Here are the notes from yesterday's meeting..."
        ... )
        >>> print(f"Draft created with ID: {draft['id']}")
    """
    service = get_gmail_api_service()
    try:
        message_json = create_message(to_, from_, subject_, body_)
        if message_json:
            draft = {"message": message_json}
            return (
                service.users()
                .drafts()
                .create(userId=user_id, body=draft)
                .execute()
            )
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def create_draft_with_attachment(
    user_id: str,
    to_: str,
    from_: str,
    subject_: str,
    body_: str,
    file_paths: Union[str, List[str]]
) -> Dict:
    """
    Create a draft email message with attachments in the user's mailbox.
    
    Creates an email draft with one or more attachments that can be later sent or modified.
    The draft is saved in the user's drafts folder with all attachments included.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        to_ (str): Recipient email address
        from_ (str): Sender email address
        subject_ (str): Email subject line
        body_ (str): Plain text email body content
        file_paths (Union[str, List[str]]): Path(s) to attachment file(s)
        
    Returns:
        Dict: API response containing draft message details (id, message, etc.),
              or None if an error occurs
              
    Example:
        >>> draft = create_draft_with_attachment(
        ...     "me",
        ...     "client@example.com",
        ...     "consultant@example.com",
        ...     "Proposal Draft",
        ...     "Please review the attached proposal draft.",
        ...     "proposal_v3.docx"
        ... )
        >>> print(f"Draft with attachment created: {draft['id']}")
    """
    service = get_gmail_api_service()
    try:
        message_json = create_message_with_attachment(
            to_, from_, subject_, body_, file_paths
        )
        if message_json:
            draft = {"message": message_json}
            return (
                service.users()
                .drafts()
                .create(userId=user_id, body=draft)
                .execute()
            )
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def list_messages(
    user_id: str,
    query: str = None,
    max_results: int = 100
) -> List[Dict]:
    """
    Retrieve a list of messages matching specified search criteria.
    
    Fetches messages from the user's mailbox that match the Gmail search query syntax.
    Supports pagination and can return up to the specified maximum number of results.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        query (str, optional): Gmail search query string (e.g., "from:john label:inbox")
        max_results (int, optional): Maximum number of messages to return (default: 100)
        
    Returns:
        List[Dict]: List of message metadata dictionaries (containing id, threadId, etc.),
                   or empty list if no matches or error occurs
                   
    Example:
        >>> # Get unread messages from specific sender
        >>> messages = list_messages(
        ...     "me",
        ...     "from:important@example.com is:unread",
        ...     50
        ... )
        >>> print(f"Found {len(messages)} unread messages")
    """
    service = get_gmail_api_service()
    try:
        messages = []
        request = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=max_results
        )
        while request is not None:
            response = request.execute()
            messages.extend(response.get('messages', []))
            request = service.users().messages().list_next(request, response)
            if len(messages) >= max_results:
                break
        return messages[:max_results]
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def get_message(user_id: str, msg_id: str, format: str = 'full') -> Dict:
    """
    Retrieve a complete message with all headers and content.
    
    Fetches a specific message by its ID, with options to control the amount of detail
    returned. The 'full' format includes both message metadata and complete payload.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to retrieve
        format (str, optional): Format of message to return:
            - 'full': Returns full email message data with payload
            - 'metadata': Returns only email message metadata
            - 'minimal': Returns only email message ID and thread ID
            (default: 'full')
            
    Returns:
        Dict: Complete message resource dictionary, or None if error occurs
        
    Example:
        >>> message = get_message("me", "17c0f4a5f3e12cb1")
        >>> print(f"Subject: {message['payload']['headers'][0]['value']}")
    """
    service = get_gmail_api_service()
    try:
        return service.users().messages().get(
            userId=user_id,
            id=msg_id,
            format=format
        ).execute()
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def delete_message(user_id: str, msg_id: str) -> bool:
    """
    Permanently delete a message by ID.
    
    Immediately and permanently deletes the specified message. This action cannot be undone.
    The message is removed from the mailbox and cannot be recovered.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
        
    Example:
        >>> # Delete spam messages older than 1 year
        >>> old_spam = list_messages("me", "label:spam older_than:1y")
        >>> for msg in old_spam:
        ...     delete_message("me", msg['id'])
    """
    service = get_gmail_api_service()
    try:
        service.users().messages().delete(
            userId=user_id,
            id=msg_id
        ).execute()
        return True
    except Exception as error:
        print(f"An error occurred: {error}")
        return False


@mcp.tool()
def modify_message(
    user_id: str,
    msg_id: str,
    add_labels: List[str] = None,
    remove_labels: List[str] = None
) -> Dict:
    """
    Modify the labels applied to a message.
    
    Adds and/or removes labels from a message. This is commonly used to mark messages as
    read/unread, important, or apply custom labels for organization.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to modify
        add_labels (List[str], optional): List of label IDs to add to the message
        remove_labels (List[str], optional): List of label IDs to remove from the message
        
    Returns:
        Dict: Modified message resource, or None if error occurs
        
    Example:
        >>> # Mark message as read and add "FollowUp" label
        >>> modified = modify_message(
        ...     "me",
        ...     "17c0f4a5f3e12cb1",
        ...     add_labels=["Label_5"],  # FollowUp label ID
        ...     remove_labels=["UNREAD"]  # Mark as read
        ... )
    """
    service = get_gmail_api_service()
    try:
        body = {
            'addLabelIds': add_labels or [],
            'removeLabelIds': remove_labels or []
        }
        return service.users().messages().modify(
            userId=user_id,
            id=msg_id,
            body=body
        ).execute()
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def list_labels(user_id: str) -> List[Dict]:
    """
    List all labels in the user's mailbox.
    
    Retrieves the complete list of labels defined in the user's Gmail account, including
    system labels (like INBOX, SPAM) and user-created labels.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        
    Returns:
        List[Dict]: List of label resources (each containing id, name, type, etc.),
                   or empty list if error occurs
                   
    Example:
        >>> labels = list_labels("me")
        >>> for label in labels:
        ...     print(f"{label['name']}: {label['id']}")
    """
    service = get_gmail_api_service()
    try:
        return service.users().labels().list(userId=user_id).execute().get('labels', [])
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def create_label(user_id: str, label_name: str, label_color: Dict = None) -> Dict:
    """
    Create a new user-defined label in the mailbox.
    
    Creates a custom label with optional color settings. The label can then be applied to
    messages and threads for organization.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        label_name (str): Name for the new label
        label_color (Dict, optional): Color settings dictionary containing:
            - textColor: Hex color for text (e.g., "#000000")
            - backgroundColor: Hex color for background (e.g., "#ff0000")
            
    Returns:
        Dict: Created label resource, or None if error occurs
        
    Example:
        >>> new_label = create_label(
        ...     "me",
        ...     "Important Clients",
        ...     {"textColor": "#ffffff", "backgroundColor": "#4285f4"}
        ... )
        >>> print(f"Created label with ID: {new_label['id']}")
    """
    service = get_gmail_api_service()
    try:
        label_object = {
            'name': label_name,
            'messageListVisibility': 'show',
            'labelListVisibility': 'labelShow'
        }
        if label_color:
            label_object['color'] = label_color
        return service.users().labels().create(
            userId=user_id,
            body=label_object
        ).execute()
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def search_messages(
    user_id: str,
    query: str,
    max_results: int = 100
) -> List[Dict]:
    """
    Search for messages using Gmail's advanced search syntax.
    
    Wrapper around list_messages() that provides a more intuitive name for search
    functionality. Uses the same powerful Gmail search operators available in the web UI.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        query (str): Gmail search query string
        max_results (int, optional): Maximum number of messages to return (default: 100)
        
    Returns:
        List[Dict]: List of message metadata dictionaries matching the search criteria
        
    Example:
        >>> # Find large attachments received last week
        >>> messages = search_messages(
        ...     "me",
        ...     "larger:5M after:2023/01/01 before:2023/01/08 has:attachment",
        ...     50
        ... )
    """
    return list_messages(user_id, query, max_results)


@mcp.tool()
def get_message_attachments(
    user_id: str,
    msg_id: str,
    save_dir: str = "attachments"
) -> List[str]:
    """
    Download all attachments from a specific message to local files.
    
    Retrieves a message, extracts all attachments, and saves them to the specified directory.
    Creates the directory if it doesn't exist. Returns paths to the saved files.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): ID of the message containing attachments
        save_dir (str, optional): Directory path to save attachments (default: "attachments")
        
    Returns:
        List[str]: List of file paths where attachments were saved, or empty list if error
        
    Example:
        >>> # Save all attachments from an invoice message
        >>> saved_files = get_message_attachments(
        ...     "me",
        ...     "17c0f4a5f3e12cb1",
        ...     "/path/to/invoices"
        ... )
        >>> for file in saved_files:
        ...     print(f"Saved: {file}")
    """
    service = get_gmail_api_service()
    try:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        message = get_message(user_id, msg_id)
        if not message:
            return []

        saved_files = []
        parts = message.get('payload', {}).get('parts', [])
        
        for part in parts:
            if part.get('filename'):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    attachment = service.users().messages().attachments().get(
                        userId=user_id,
                        messageId=msg_id,
                        id=attachment_id
                    ).execute()
                    
                    file_data = base64.urlsafe_b64decode(
                        attachment.get('data', '').encode('UTF-8')
                    )
                    
                    filepath = os.path.join(save_dir, part['filename'])
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                    saved_files.append(filepath)
        
        return saved_files
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def get_message_body(user_id: str, msg_id: str, prefer_html: bool = False) -> Optional[str]:
    """
    Extract the message body text from a message by ID.
    
    Retrieves the complete message and extracts the body content, with options for
    HTML or plain text preference. Handles both simple and multipart messages.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to retrieve
        prefer_html (bool): If True, returns HTML body when available (default: False)
        
    Returns:
        Optional[str]: The message body content, or None if not found
        
    Example:
        >>> body = get_message_body("me", "17c0f4a5f3e12cb1")
        >>> html_body = get_message_body("me", "17c0f4a5f3e12cb1", prefer_html=True)
    """
    try:
        message = get_message(user_id, msg_id, format='full')
        if not message:
            return None

        payload = message.get('payload', {})
        parts = payload.get('parts', [])
        
        # Handle simple (non-multipart) messages
        if not parts:
            body_data = payload.get('body', {}).get('data')
            if body_data:
                return base64.urlsafe_b64decode(body_data.encode('UTF-8')).decode()
            return None

        # Handle multipart messages
        for part in parts:
            mime_type = part.get('mimeType', '')
            body_data = part.get('body', {}).get('data')
            
            if not body_data:
                continue
                
            decoded_body = base64.urlsafe_b64decode(body_data.encode('UTF-8')).decode()
            
            if prefer_html and 'text/html' in mime_type:
                return decoded_body
            if 'text/plain' in mime_type:
                return decoded_body
        
        # Fallback to any text part if preferred type not found
        for part in parts:
            if part.get('body', {}).get('data'):
                return base64.urlsafe_b64decode(
                    part['body']['data'].encode('UTF-8')
                ).decode()
                
        return None
    except Exception as error:
        print(f"An error occurred while getting message body: {error}")
        return None


@mcp.tool()
def get_recent_messages_from_sender(
    user_id: str,
    sender_email: str,
    max_results: int = 10,
    days_back: int = 30
) -> List[Dict]:
    """
    Retrieve recent messages from a specific sender within a time window.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        sender_email (str): Email address of the sender to filter by
        max_results (int): Maximum number of messages to return (default: 10)
        days_back (int): Number of days to look back for messages (default: 30)
        
    Returns:
        List[Dict]: List of message metadata dictionaries
        
    Example:
        >>> recent_emails = get_recent_messages_from_sender(
        ...     "me",
        ...     "important.client@example.com",
        ...     max_results=5,
        ...     days_back=7
        ... )
    """
    try:
        date_cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        query = f"from:{sender_email} after:{date_cutoff}"
        return list_messages(user_id, query, max_results)
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def mark_as_read(user_id: str, msg_id: str) -> bool:
    """
    Mark a message as read by removing the UNREAD label.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to mark as read
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> mark_as_read("me", "17c0f4a5f3e12cb1")
    """
    return modify_message(
        user_id,
        msg_id,
        remove_labels=[LABEL_UNREAD]
    ) is not None


@mcp.tool()
def mark_as_unread(user_id: str, msg_id: str) -> bool:
    """
    Mark a message as unread by adding the UNREAD label.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to mark as unread
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> mark_as_unread("me", "17c0f4a5f3e12cb1")
    """
    return modify_message(
        user_id,
        msg_id,
        add_labels=[LABEL_UNREAD]
    ) is not None


@mcp.tool()
def star_message(user_id: str, msg_id: str) -> bool:
    """
    Star/flag a message by adding the STARRED label.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to star
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> star_message("me", "17c0f4a5f3e12cb1")
    """
    return modify_message(
        user_id,
        msg_id,
        add_labels=[LABEL_STARRED]
    ) is not None


@mcp.tool()
def unstar_message(user_id: str, msg_id: str) -> bool:
    """
    Remove star/flag from a message by removing the STARRED label.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to unstar
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> unstar_message("me", "17c0f4a5f3e12cb1")
    """
    return modify_message(
        user_id,
        msg_id,
        remove_labels=[LABEL_STARRED]
    ) is not None


@mcp.tool()
def get_unread_messages(
    user_id: str,
    max_results: int = 100,
    label_ids: List[str] = None
) -> List[Dict]:
    """
    Retrieve all unread messages, optionally filtered by labels.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        max_results (int): Maximum number of messages to return (default: 100)
        label_ids (List[str]): Optional list of label IDs to filter by
        
    Returns:
        List[Dict]: List of unread message metadata dictionaries
        
    Example:
        >>> # Get unread messages in inbox
        >>> unread = get_unread_messages("me", label_ids=["INBOX"])
        >>> # Get all unread messages
        >>> all_unread = get_unread_messages("me", max_results=200)
    """
    try:
        query = "is:unread"
        if label_ids:
            label_query = " ".join(f"label:{label}" for label in label_ids)
            query += f" {label_query}"
            
        return list_messages(user_id, query, max_results)
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def process_unread_messages(
    user_id: str,
    processor_func: callable,
    mark_processed: bool = True,
    label_ids: List[str] = None
) -> int:
    """
    Process all unread messages with a custom function.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        processor_func (callable): Function to process each message (accepts message dict)
        mark_processed (bool): Whether to mark messages as read after processing
        label_ids (List[str]): Optional list of label IDs to filter by
        
    Returns:
        int: Number of messages processed
        
    Example:
        >>> def save_attachments(message):
        ...     # Custom processing logic
        ...     pass
        >>> processed = process_unread_messages(
        ...     "me",
        ...     save_attachments,
        ...     label_ids=["INBOX"]
        ... )
    """
    try:
        unread_messages = get_unread_messages(
            user_id, label_ids=label_ids)
        count = 0
        
        for msg in unread_messages:
            full_message = get_message(user_id, msg['id'])
            if full_message:
                processor_func(full_message)
                if mark_processed:
                    mark_as_read(user_id, msg['id'])
                count += 1
                
        return count
    except Exception as error:
        print(f"An error occurred: {error}")
        return 0


@mcp.tool()
def get_message_headers(
    user_id: str,
    msg_id: str,
    header_names: List[str] = None
) -> Dict[str, str]:
    """
    Extract specific headers from a message.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to examine
        header_names (List[str]): List of header names to retrieve (None for all)
        
    Returns:
        Dict[str, str]: Dictionary of header names and values
        
    Example:
        >>> headers = get_message_headers(
        ...     "me",
        ...     "17c0f4a5f3e12cb1",
        ...     ["From", "Subject", "Date"]
        ... )
    """
    try:
        message = get_message(user_id, msg_id)
        if not message:
            return {}

        headers = message.get('payload', {}).get('headers', [])
        result = {}
        
        for header in headers:
            name = header.get('name', '')
            if header_names is None or name in header_names:
                result[name] = header.get('value', '')
                
        return result
    except Exception as error:
        print(f"An error occurred: {error}")
        return {}


@mcp.tool()
def move_message_to_label(
    user_id: str,
    msg_id: str,
    label_id: str,
    remove_from_inbox: bool = False
) -> bool:
    """
    Move a message to a specific label/folder.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message to move
        label_id (str): The ID of the target label
        remove_from_inbox (bool): Whether to remove from INBOX (default: False)
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> # Move to custom label
        >>> move_message_to_label("me", "17c0f4a5f3e12cb1", "Label_1")
        >>> # Archive message (remove from inbox)
        >>> move_message_to_label("me", "17c0f4a5f3e12cb1", "Label_1", True)
    """
    try:
        add_labels = [label_id]
        remove_labels = [LABEL_INBOX] if remove_from_inbox else []
        
        return modify_message(
            user_id,
            msg_id,
            add_labels=add_labels,
            remove_labels=remove_labels
        ) is not None
    except Exception as error:
        print(f"An error occurred: {error}")
        return False


@mcp.tool()
def get_thread_messages(
    user_id: str,
    thread_id: str,
    format: str = 'full'
) -> List[Dict]:
    """
    Retrieve all messages in a thread.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        thread_id (str): The ID of the thread to retrieve
        format (str): Format of messages to return ('full', 'metadata', 'minimal')
        
    Returns:
        List[Dict]: List of message resources in the thread
        
    Example:
        >>> thread = get_thread_messages("me", "17c0f4a5f3e12cb1")
        >>> for msg in thread:
        ...     print(get_message_body("me", msg['id']))
    """
    service = get_gmail_api_service()
    try:
        thread = service.users().threads().get(
            userId=user_id,
            id=thread_id,
            format=format
        ).execute()
        return thread.get('messages', [])
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def get_message_snippet(user_id: str, msg_id: str) -> Optional[str]:
    """
    Get the snippet (preview text) of a message.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message
        
    Returns:
        Optional[str]: The message snippet text, or None if error occurs
        
    Example:
        >>> snippet = get_message_snippet("me", "17c0f4a5f3e12cb1")
    """
    try:
        message = get_message(user_id, msg_id, format='metadata')
        return message.get('snippet')
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def get_latest_messages(
    user_id: str,
    max_results: int = 10,
    label_ids: List[str] = None
) -> List[Dict]:
    """
    Get the most recent messages, optionally filtered by labels.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        max_results (int): Maximum number of messages to return (default: 10)
        label_ids (List[str]): Optional list of label IDs to filter by
        
    Returns:
        List[Dict]: List of message metadata dictionaries
        
    Example:
        >>> # Get latest 5 inbox messages
        >>> latest = get_latest_messages("me", 5, ["INBOX"])
        >>> # Get latest 10 messages overall
        >>> all_latest = get_latest_messages("me")
    """
    service = get_gmail_api_service()
    try:
        return service.users().messages().list(
            userId=user_id,
            maxResults=max_results,
            labelIds=label_ids
        ).execute().get('messages', [])
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def get_message_date(user_id: str, msg_id: str) -> Optional[datetime]:
    """
    Get the date/time a message was received.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message
        
    Returns:
        Optional[datetime]: The message date as datetime object, or None if error
        
    Example:
        >>> msg_date = get_message_date("me", "17c0f4a5f3e12cb1")
        >>> print(f"Received at: {msg_date.strftime('%Y-%m-%d %H:%M:%S')}")
    """
    try:
        headers = get_message_headers(user_id, msg_id, ["Date"])
        date_str = headers.get("Date", "")
        if not date_str:
            return None
            
        # Parse email date string to datetime
        return email.utils.parsedate_to_datetime(date_str)
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def find_messages_by_date_range(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    max_results: int = 100,
    label_ids: List[str] = None
) -> List[Dict]:
    """
    Find messages within a specific date range.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        start_date (datetime): Start of date range (inclusive)
        end_date (datetime): End of date range (inclusive)
        max_results (int): Maximum number of messages to return (default: 100)
        label_ids (List[str]): Optional list of label IDs to filter by
        
    Returns:
        List[Dict]: List of message metadata dictionaries
        
    Example:
        >>> start = datetime(2023, 1, 1)
        >>> end = datetime(2023, 1, 31)
        >>> jan_messages = find_messages_by_date_range(
        ...     "me",
        ...     start,
        ...     end,
        ...     label_ids=["INBOX"]
        ... )
    """
    try:
        start_str = start_date.strftime('%Y/%m/%d')
        end_str = end_date.strftime('%Y/%m/%d')
        query = f"after:{start_str} before:{end_str}"
        
        if label_ids:
            label_query = " ".join(f"label:{label}" for label in label_ids)
            query += f" {label_query}"
            
        return list_messages(user_id, query, max_results)
    except Exception as error:
        print(f"An error occurred: {error}")
        return []


@mcp.tool()
def extract_email_address(header_value: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract email address and name from a header value.
    
    Parameters:
        header_value (str): Header value string (e.g., "John Doe <john@example.com>")
        
    Returns:
        Tuple[Optional[str], Optional[str]]: (name, email) or (None, email) if no name
        
    Example:
        >>> name, email = extract_email_address("John Doe <john@example.com>")
        >>> # Returns ("John Doe", "john@example.com")
    """
    if not header_value:
        return None, None
        
    # Pattern to match "Name <email>" or just "email"
    pattern = r'(?:"?([^"]*)"?\s)?(?:<?(.+?@[^>,]+)>?)'
    match = re.match(pattern, header_value)
    if match:
        name = match.group(1) if match.group(1) else None
        email = match.group(2) if match.group(2) else None
        return name, email
    return None, None


@mcp.tool()
def get_message_sender_info(
    user_id: str,
    msg_id: str
) -> Dict[str, Optional[str]]:
    """
    Extract sender information (name, email) from a message.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message
        
    Returns:
        Dict[str, Optional[str]]: Dictionary with 'name' and 'email' keys
        
    Example:
        >>> sender = get_message_sender_info("me", "17c0f4a5f3e12cb1")
        >>> print(f"From: {sender['name']} ({sender['email']})")
    """
    headers = get_message_headers(user_id, msg_id, ["From"])
    from_header = headers.get("From", "")
    name, email = extract_email_address(from_header)
    return {"name": name, "email": email}


@mcp.tool()
def get_message_recipients_info(
    user_id: str,
    msg_id: str
) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract recipients information (To, Cc, Bcc) from a message.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_id (str): The ID of the message
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary with 'to', 'cc', 'bcc' keys,
        each containing a list of {'name', 'email'} dictionaries
        
    Example:
        >>> recipients = get_message_recipients_info("me", "17c0f4a5f3e12cb1")
        >>> for recipient in recipients['to']:
        ...     print(f"To: {recipient['name']} ({recipient['email']})")
    """
    headers = get_message_headers(user_id, msg_id, ["To", "Cc", "Bcc"])
    result = {
        "to": [],
        "cc": [],
        "bcc": []
    }

    for field in ["To", "Cc", "Bcc"]:
        if field in headers:
            addresses = headers[field].split(',')
            for addr in addresses:
                name, email = extract_email_address(addr.strip())
                if email:  # Only add if we found an email
                    result[field.lower()].append(
                        {"name": name, "email": email}
                    )
              
    return result


@mcp.tool()
def get_label_id_by_name(user_id: str, label_name: str) -> Optional[str]:
    """
    Find a label ID by its name.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        label_name (str): The name of the label to find
        
    Returns:
        Optional[str]: The label ID if found, None otherwise
        
    Example:
        >>> label_id = get_label_id_by_name("me", "Important")
    """
    labels = list_labels(user_id)
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']
    return None


@mcp.tool()
def batch_modify_messages(
    user_id: str,
    msg_ids: List[str],
    add_labels: List[str] = None,
    remove_labels: List[str] = None
) -> bool:
    """
    Apply label modifications to multiple messages in a single API call.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        msg_ids (List[str]): List of message IDs to modify
        add_labels (List[str]): Labels to add
        remove_labels (List[str]): Labels to remove
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> # Mark multiple messages as read
        >>> batch_modify_messages(
        ...     "me",
        ...     ["msg1", "msg2", "msg3"],
        ...     remove_labels=["UNREAD"]
        ... )
    """
    service = get_gmail_api_service()
    try:
        body = {
            'ids': msg_ids,
            'addLabelIds': add_labels or [],
            'removeLabelIds': remove_labels or []
        }
        service.users().messages().batchModify(
            userId=user_id,
            body=body
        ).execute()
        return True
    except Exception as error:
        print(f"An error occurred: {error}")
        return False


@mcp.tool()
def count_messages(
    user_id: str,
    query: str = None,
    label_ids: List[str] = None
) -> int:
    """
    Count messages matching specified criteria.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        query (str): Optional search query
        label_ids (List[str]): Optional list of label IDs to filter by
        
    Returns:
        int: Number of messages matching criteria
        
    Example:
        >>> # Count unread messages in inbox
        >>> unread_count = count_messages(
        ...     "me",
        ...     query="is:unread",
        ...     label_ids=["INBOX"]
        ... )
    """
    service = get_gmail_api_service()
    try:
        result = service.users().messages().list(
            userId=user_id,
            q=query,
            labelIds=label_ids,
            maxResults=1  # We only need the result size
        ).execute()
        return result.get('resultSizeEstimate', 0)
    except Exception as error:
        print(f"An error occurred: {error}")
        return 0


@mcp.tool()
def watch_for_new_emails(
    user_id: str,
    topic_name: str,
    label_ids: List[str] = None
) -> Dict:
    """
    Set up a push notification watch for new emails.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        topic_name (str): Cloud Pub/Sub topic name (projects/<project>/topics/<topic>)
        label_ids (List[str]): Optional list of label IDs to watch
        
    Returns:
        Dict: Watch response containing historyId and expiration
        
    Example:
        >>> response = watch_for_new_emails(
        ...     "me",
        ...     "projects/my-project/topics/new-emails"
        ... )
    """
    service = get_gmail_api_service()
    try:
        body = {
            'topicName': topic_name,
            'labelIds': label_ids or ["INBOX"]
        }
        return service.users().watch(
            userId=user_id,
            body=body
        ).execute()
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


@mcp.tool()
def stop_email_watch(user_id: str) -> bool:
    """
    Stop push notifications for email changes.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        >>> stop_email_watch("me")
    """
    service = get_gmail_api_service()
    try:
        service.users().stop(userId=user_id).execute()
        return True
    except Exception as error:
        print(f"An error occurred: {error}")
        return False


@mcp.tool()
def send_draft(user_id: str, draft_id: str) -> Dict:
    """
    Send an existing draft email message.
    
    Retrieves a draft by its ID and sends it as a regular email message. The draft will be
    removed from the drafts folder after being sent.
    
    Parameters:
        user_id (str): User ID (typically "me" for authenticated user)
        draft_id (str): The ID of the draft to send
        
    Returns:
        Dict: API response containing sent message details (id, threadId, etc.),
              or None if an error occurs
              
    Example:
        >>> # First create a draft
        >>> draft = create_draft(
        ...     "me",
        ...     "client@example.com",
        ...     "me@example.com",
        ...     "Project Update",
        ...     "Here's the latest project status..."
        ... )
        >>> # Later, send the draft
        >>> sent_message = send_draft("me", draft['id'])
        >>> print(f"Message sent with ID: {sent_message['id']}")
    """
    service = get_gmail_api_service()
    try:
        return service.users().drafts().send(
            userId=user_id,
            body={'id': draft_id}
        ).execute()
    except Exception as error:
        print(f"An error occurred while sending draft: {error}")
        return None


if __name__ == "__main__":
    mcp.run()

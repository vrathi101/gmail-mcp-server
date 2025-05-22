# Gmail MCP Server Setup

## Overview

This project creates a Model Context Protocol (MCP) server that allows Claude (or any MCP-compatible client) to interact with your Gmail account. It supports:
- Sending emails (with and without attachments)
- Creating drafts
- Listing, reading, deleting, and modifying Gmail messages
- Managing labels
- Extracting metadata such as headers, body, sender, recipients, etc.
- And more

## Tech Stack

- **Python**
- **Google Gmail API**
- **Google Auth / OAuth2**
- **MCP Protocol (via `fastmcp`)**
- **Claude Desktop Integration**
- **Virtual Environment (`.venv`) using `uv` or Python**

## Setup Instructions
### 1. Clone or navigate to your project directory

Example:
```bash
cd ~/Desktop/GmailMCPServer
```
### 2. Create and activate a virtual environment

Using `uv`:

```bash
uv venv --python $(which python3)
source .venv/bin/activate
```

Or using built-in `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```
### 3. Install required packages

```bash

pip install -r requirements.txt

```
### 4. Setup Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project
2. Enable the **Gmail API**
3. Create an **OAuth 2.0 Client ID** for a **Web application**
4. Download the `credentials.json` file
5. Place it at the root of your project directory (e.g.):
```
~/Desktop/GmailMCPServer/credentials.json
```
6. Add your email as a test user in GCP
7. Add corresponding Redirect URI in the project configuration

### 5. Claude Desktop MCP Configuration

Create or update this file:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```
```json
{
    "mcpServers": {
        "{{PROJECT_NAME}}": {
            "command": "{{PATH_TO_PROJECT}}/.venv/bin/python",
            "args": [
                "{{PATH_TO_PROJECT}}/main.py"
            ],
	}
    }
}
```

Replace `{{PATH_TO_PROJECT}}` by: `cd`ing into the folder containing your source code and copying the output of the `pwd` command. 

### 6. First-time OAuth2 token generation

Run the following command once to authenticate and generate `token.json`:
```bash

python main.py

```
A browser will open to authorize access. After success, a `token.json` file will be saved.

### 7. Claude Usage

Once the MCP server is running, you can issue natural language commands like:

```

Send an email draft from ***@gmail.com to ***@gmail.com saying subject "hello" and body "test"

```

Claude will use the appropriate tool depending on context.

## Notes

- You must keep `credentials.json` and the generated `token.json` secure.

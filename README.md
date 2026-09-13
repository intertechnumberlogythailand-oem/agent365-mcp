# Agent365 MCP - Dataverse Integration

AI Model Management System with Microsoft Dataverse and Stripe Integration for Intertech Numberology Thailand.

## Overview

Agent365 MCP provides a Model Context Protocol (MCP) server that integrates with Microsoft Dataverse to manage AI models and handle payment processing through Stripe.

## Features

✅ **Dataverse Integration**
- Fetch and parse EDMX metadata for cr_aimodels
- Extract properties, lookups, and entity schema
- Automatic publisher prefix detection (fuzzy matching)

✅ **Azure Authentication**
- MSAL token caching for efficient API calls
- Secure client credentials flow
- Automatic token refresh

✅ **MCP Tools**
- `health_check()` - Server health status
- `get_ai_model(model_id)` - Retrieve AI model configuration
- `fetch_metadata()` - Fetch Dataverse metadata
- `parse_cr_aimodels()` - Parse and schema extraction

✅ **Stripe Integration**
- Webhook listener for payment events
- Webhook signing for security
- Test event triggering

## Prerequisites

- Python 3.8+
- Node.js 14+ (for Stripe CLI)
- Azure AD Application Registration
- Dataverse environment
- Stripe account

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/intertechnumberlogythailand-oem/agent365-mcp.git
cd agent365-mcp
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
npm install -g @stripe/cli@latest
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `AZURE_TENANT_ID` - Your Azure AD tenant ID
- `AZURE_CLIENT_ID` - Your Azure AD client ID
- `AZURE_CLIENT_SECRET` - Your Azure AD client secret
- `DATAVERSE_ENV` - Your Dataverse environment URL
- `STRIPE_PUBLIC_KEY` - Your Stripe public key
- `STRIPE_SECRET_KEY` - Your Stripe secret key
- `STRIPE_WEBHOOK_SECRET` - Your Stripe webhook signing secret

## Usage

### Fetch Dataverse Metadata
```bash
python dataverse_metadata_v2.py
```

This will:
1. Authenticate with Azure AD
2. Fetch the EDMX metadata from Dataverse
3. Parse the cr_aimodels entity schema
4. Generate `cr_aimodels_schema.json`

### Output Example
```
╔══ cr_aimodels Schema ═══════════════════════════════════════╗
  EntityType  : cr_aimodels
  EntitySet   : cr_aimodelses   ← use in API calls
  Primary Key : cr_aimodelid
  Base Type   : crmbaseentity
╚═════════════════════════════════════════════════════════════╝

  Properties (42):
  logical_name                                    type                           nullable
  ────────────────────────────────────────────────────────────────────────────────
  cr_name                                         Edm.String                     yes
  cr_description                                  Edm.String                     yes
  cr_modeltype                                    Edm.String                     yes
  ...
```

### Start Stripe Webhook Listener
```bash
stripe listen
```

### Test Stripe Events
```bash
stripe trigger charge.succeeded
```

## Project Structure

```
agent365-mcp/
├── dataverse_metadata_v2.py      # Main metadata extraction script
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── README.md                     # This file
└── cr_aimodels_schema.json       # Generated schema (auto-created)
```

## API Endpoints

### Dataverse API
```
GET /api/data/v9.2/$metadata?annotations=true
GET /api/data/v9.2/cr_aimodelses?$select=cr_name,cr_description,...
POST /api/data/v9.2/cr_aimodelses
PATCH /api/data/v9.2/cr_aimodelses(ID)
DELETE /api/data/v9.2/cr_aimodelses(ID)
```

### Stripe API
```
POST /webhook  (Receive webhook events)
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_TENANT_ID` | Azure AD tenant ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_ID` | Azure AD app ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_CLIENT_SECRET` | Azure AD secret | `your_secret_here` |
| `DATAVERSE_ENV` | Dataverse URL | `https://intertechnumberlogythailand.crm5.dynamics.com` |
| `MCP_SERVER_NAME` | MCP server name | `intertechnumberlogythailand` |
| `MCP_SERVER_PORT` | MCP server port | `8000` |
| `STRIPE_PUBLIC_KEY` | Stripe public key | `pk_test_...` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |

## Troubleshooting

### Token Error: "Unauthorized_client"
- Verify Azure AD credentials in `.env`
- Check that the app has Dataverse API permissions

### Error: "cr_aimodels not found"
- Check if the table exists in your Dataverse environment
- The table might have a different publisher prefix (e.g., `cr8a2_aimodels`)
- Run with debug mode to see all custom entities

### Stripe Webhook Not Receiving Events
- Ensure `stripe listen` is running
- Check webhook endpoint URL is accessible
- Verify `STRIPE_WEBHOOK_SECRET` is correct

## Contributing

1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
2. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
3. Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- 📧 Email: intertechnumberlogythailand@zohomail.com
- 🐛 GitHub Issues: [Report an issue](https://github.com/intertechnumberlogythailand-oem/agent365-mcp/issues)

## Related Projects

- [FastMCP](https://github.com/pydantic/fastmcp) - Model Context Protocol implementation
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python) - Azure authentication
- [Stripe Python](https://github.com/stripe/stripe-python) - Stripe SDK

---

**Made with ❤️ by Intertech Numberology Thailand**

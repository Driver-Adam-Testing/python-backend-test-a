import json

import markdown

# JSON input (use your provided JSON object)
config_json = """
{
      "resource_name": "github-app",
      "resource_type": "GITHUB_APP",
      "resource": {
        "app_name": "eric-2m2-gh-app",
        "app_id": null,
        "client_id": null,
        "client_secret": null,
        "homepage_url": "https://eric-2m2-webapp.ngrok.io",
        "callback_url": "https://eric-2m2-api.ngrok.io/api/v1/git-provider/github/callback",
        "request_oauth_on_installation": true,
        "enable_device_flow": true,
        "setup_url": "https://github.com/app/eric-2m2-gh-app",
        "redirect_on_update": true,
        "webhook": {
          "webhook_url": "https://eric-2m2-api.ngrok.io/api/v1/git-provider/github/webhook",
          "webhook_secret": "power startle skewed scorebook undermine molehill careless sureness deftly viewing vocalist such driving durably corset afterglow",
          "ssl_verification_enabled": true
        },
        "permissions": {
          "repository_permissions": {
            "contents": "read-only",
            "pull_requests": "read-only",
            "metadata": "read-only",
            "webhooks": "read-only"
          },
          "organization_permissions": {
            "events": "read-only",
            "members": "read-only",
            "webhooks": "read-only"
          },
          "account_permissions": {
            "email_addresses": "read-only"
          }
        },
        "subscribed_events": [
          "push",
          "pull_request",
          "installation",
          "repository"
        ],
        "public_in_marketplace": false,
        "private_key_pem_path": null
      }
    }
"""

config = json.loads(config_json)["resource"]


def generate_markdown(config):
    md = f"""# 🔧 GitHub App Setup Guide

## 1. Create the GitHub App

- Go to [GitHub Apps](https://github.com/settings/apps).
- Click **New GitHub App**.
- Fill in the following:

| Field | Value |
|-------|-------|
| **App Name** | `{config['app_name']}` |
| **Homepage URL** | `{config['homepage_url']}` |
| **Setup URL** | `{config['setup_url']}` |
| **Callback URL** | `{config['callback_url']}` |

## 2. Webhook Configuration

| Field | Value |
|-------|-------|
| **Webhook URL** | `{config['webhook']['webhook_url']}` |
| **Webhook Secret** | `{config['webhook']['webhook_secret']}` |
| **SSL Verification** | `{config['webhook']['ssl_verification_enabled']}` |

## 3. Permissions and Events

### Repository Permissions
"""
    for perm, level in config["permissions"]["repository_permissions"].items():
        md += f"- `{perm}`: {level}\n"

    md += "\n### Organization Permissions\n"
    for perm, level in config["permissions"]["organization_permissions"].items():
        md += f"- `{perm}`: {level}\n"

    md += "\n### Account Permissions\n"
    for perm, level in config["permissions"]["account_permissions"].items():
        md += f"- `{perm}`: {level}\n"

    md += "\n### Subscribed Events\n"
    for event in config["subscribed_events"]:
        md += f"- `{event}`\n"

    oauth = "✅ Enabled" if config["request_oauth_on_installation"] else "❌ Disabled"
    device_flow = "✅ Enabled" if config["enable_device_flow"] else "❌ Disabled"

    md += f"""
## 4. OAuth & Device Flow

- **OAuth during installation:** {oauth}
- **Device Flow:** {device_flow}

## 5. Post-Setup Steps

After creating your app, GitHub will provide:

- `App ID`
- `Client ID`
- `Client Secret`
- Private key PEM file (store securely).

Update your configuration accordingly.

## 6. Installation

Visit: [Install {config['app_name']}](https://github.com/apps/{config['app_name']}/installations/new)

## 7. Test Integration

- Trigger events (`push`, `pull_request`).
- Verify webhook delivery at: `{config['webhook']['webhook_url']}`.

---

"""
    return md


# Output markdown guide
markdown_guide = generate_markdown(config)
print(markdown_guide)


# Assuming markdown_guide was generated from the previous Python script:
html_content = markdown.markdown(markdown_guide, extensions=["tables"])

html_page = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub App Setup Guide</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 40px auto;
            max-width: 800px;
            padding: 10px;
            color: #333;
        }}
        h1, h2, h3 {{
            color: #0366d6;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        table, th, td {{
            border: 1px solid #ddd;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
        }}
        code {{
            background-color: #f8f8f8;
            padding: 2px 4px;
            border-radius: 4px;
        }}
        pre {{
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
        }}
        a {{
            color: #0366d6;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Write the HTML to file
with open("./static/gh.html", "w", encoding="utf-8") as f:
    f.write(html_page)

print("Static HTML page generated as 'github_app_setup_guide.html'.")

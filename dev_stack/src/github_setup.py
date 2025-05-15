from models import GitHubAppResource


def generate_markdown(config: dict) -> str:
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


def generate_github_app_setup_guide(github_app_resource: GitHubAppResource) -> None:
    config = github_app_resource.model_dump(mode="json")
    markdown_guide = generate_markdown(config)
    with open("./state/out/github_app_setup_guide.md", "w", encoding="utf-8") as f:
        f.write(markdown_guide)

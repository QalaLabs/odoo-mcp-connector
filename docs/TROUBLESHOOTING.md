# Troubleshooting Guide

## Common Issues

### "spawn uvx ENOENT"

UV is not installed or not in PATH.

**Solution:**
1. Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Restart terminal
3. If on macOS, launch Claude from Terminal: `open -a "Claude"`

### "Access Denied" on all models

Your Odoo API key doesn't have permissions.

**Solution:**
1. Regenerate API key in Odoo
2. Ensure user has access to the models
3. For Odoo.sh, verify plan supports External API

### "Invalid Token" / "Authentication Required"

OAuth/token issue.

**Solution:**
Disconnect and reconnect MCP in your AI tool settings.

### SSL Certificate Error

Python can't verify SSL certificates.

**Solution:**
```json
{
  "env": {
    "ODOO_URL": "https://your-odoo.com",
    "ODOO_API_KEY": "your-key",
    "SSL_CERT_FILE": "/etc/ssl/cert.pem"
  }
}
```

### Database Not Found

Odoo restricts database listing.

**Solution:**
Set `ODOO_DB` explicitly:
```json
{
  "env": {
    "ODOO_DB": "your-database-name"
  }
}
```

## Debug Mode

Enable verbose logging:
```json
{
  "env": {
    "ODOO_MCP_LOG_LEVEL": "DEBUG"
  }
}
```

## Check Connection

Ask Claude:
> "Run server_info and tell me the connection status"

## Need Help?

- Check Odoo is accessible: `curl https://your-odoo.com/web/database/selector`
- Test API key: `curl -X POST https://your-odoo.com/api/account/2/token`

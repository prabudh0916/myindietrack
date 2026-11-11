# IndieTrack — Microsoft Azure Deployment Guide

**Target Cloud Platform:** Microsoft Azure  
**Architecture:** Azure App Service (Linux) + Azure SQL Database + Azure Blob Storage  
**Application:** IndieTrack — Music Release & Promotion Analytics Platform  

---

## 1. Prerequisites & Estimated Azure Costs

### 1.1 Prerequisites
- Active Microsoft Azure Subscription (Eligible for Azure Free Account / Student Credits).
- Azure CLI (`az`) installed locally.
- Git repository containing IndieTrack codebase.

### 1.2 Cost Management & Free Tier Guidance
> [!NOTE]
> Azure offers student and trial credits ($100–$200). Use the minimal tier configuration below to stay within budget:
- **Azure App Service:** `B1` Basic tier (~$13/month) or `F1` Free tier (limited outbound networking / CPU hours).
- **Azure SQL Database:** Serverless Compute tier (Auto-pause enabled after 1 hour of inactivity, ~0.5 vCore min, ~$5/month active).
- **Azure Blob Storage:** Standard LRS (Locally Redundant Storage, ~$0.02/GB/month).
- **Cleanup Warning:** Delete the resource group immediately after university viva evaluation to prevent recurring charges!

---

## 2. Step-by-Step Azure CLI Deployment

### Step 1: Login & Define Environment Variables
```bash
# Log in to Azure account
az login

# Set deployment variables (replace placeholders with unique names)
export RESOURCE_GROUP="rg-indietrack-prod"
export LOCATION="eastus"
export SQL_SERVER_NAME="sqlserver-indietrack-$RANDOM"
export SQL_DB_NAME="sqldb-indietrack"
export SQL_ADMIN_USER="indieadmin"
export SQL_ADMIN_PASSWORD="StrongPassword@2026!ReplaceMe"
export STORAGE_ACCOUNT_NAME="strgindietrack$RANDOM"
export APP_SERVICE_PLAN="asp-indietrack"
export APP_NAME="app-indietrack-$RANDOM"
```

### Step 2: Create Resource Group
```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 3: Provision Azure SQL Database
```bash
# 1. Create Azure SQL Server
az sql server create \
  --name $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $SQL_ADMIN_USER \
  --admin-password $SQL_ADMIN_PASSWORD

# 2. Allow Azure services (App Service) to access SQL Server
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER_NAME \
  --name "AllowAllWindowsAzureIps" \
  --start-ip-address "0.0.0.0" \
  --end-ip-address "0.0.0.0"

# 3. Create Serverless Database
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER_NAME \
  --name $SQL_DB_NAME \
  --edition GeneralPurpose \
  --family Gen5 \
  --compute-model Serverless \
  --auto-pause-delay 60 \
  --min-capacity 0.5 \
  --capacity 1
```

### Step 4: Apply Schema & Transact-SQL Artifacts
Using `sqlcmd` or Azure Portal Query Editor, execute the SQL scripts located in `sql/` in sequence:
1. `sql/01_schema_azure_sql.sql`
2. `sql/02_views.sql`
3. `sql/03_stored_procedures.sql`
4. `sql/04_indexes.sql`
5. `sql/05_seed_sample_data.sql`

### Step 5: Provision Azure Blob Storage
```bash
# 1. Create Storage Account
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --allow-blob-public-access false

# 2. Retrieve Connection String
export AZURE_STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query connectionString -o tsv)

# 3. Create Private Container
az storage container create \
  --name "indietrack-assets" \
  --account-name $STORAGE_ACCOUNT_NAME \
  --public-access off \
  --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
```

### Step 6: Deploy Azure App Service (Linux / Python)
```bash
# 1. Create App Service Plan (B1 Linux)
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --is-linux \
  --sku B1

# 2. Create Web App with Python 3.11/3.12 Runtime
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --runtime "PYTHON:3.11"

# 3. Configure App Settings (Environment Variables)
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    FLASK_ENV="production" \
    SECRET_KEY="$(openssl rand -hex 32)" \
    DATABASE_URL="mssql+pyodbc://${SQL_ADMIN_USER}:${SQL_ADMIN_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DB_NAME}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no" \
    AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
    AZURE_STORAGE_CONTAINER="indietrack-assets" \
    APP_BASE_URL="https://${APP_NAME}.azurewebsites.net"

# 4. Set Startup Command (Gunicorn WSGI Server)
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "gunicorn --bind=0.0.0.0:8000 --workers=4 app:app"

# 5. Enable Health Check Monitoring
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --generic-configurations '{"healthCheckPath": "/api/v1/health"}'

# 6. Deploy Code via Zip Deploy or Git
az webapp deployment source config-zip \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --src release.zip
```

---

## 3. Post-Deployment Verification Checklist

1. **Verify Health Endpoint:**  
   Navigate to `https://${APP_NAME}.azurewebsites.net/api/v1/health`. Ensure `database.connected == true` and `storage.connected == true`.
2. **Verify HTTPS Redirection:**  
   Confirm HTTP requests redirect to HTTPS and receive `Strict-Transport-Security` headers.
3. **Verify Seed Authentication:**  
   Login with initial admin credentials, immediately change the password via `/profile/change-password`.
4. **Test Blob Upload:**  
   Upload an audio demo and cover artwork; confirm file binary is saved in Azure Blob container `indietrack-assets`.

---

## 4. Teardown & Resource Deletion
To immediately terminate all running resources and avoid unintended subscription charges:
```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

# atd-citybase

Healthcheck url, must be on city network: https://citybase.austinmobility.io/

## Description

Flask based endpoint used to update Knack transaction records based on events delivered by Citybase.

## Integration with Knack

Citybase is the payment provider for the Over the Street and Lamppost Banner invoices.
Once a reservation is created and approved in the Knack app, an invoice is generated and marked as ready to pay. Custom [javascript](https://github.com/cityofaustin/atd-knack/blob/master/code/street-banner/street-banner.js#L417) creates a payload to send to the [Citybase endpoint](https://invoice-service.prod.cityba.se/invoices/austin_tx_transportation/street_banner). This request responds with a url to process the payment request. Note, the amount must be in pennies.

Once a user has completed the payment transaction, Citybase sends a postback and waits for us to confirm receipt. Citybase does not consider the payment complete until it receives a 200 response to the request.

The app inserts a record in the citybase_messages table in the Street Banners Knack app.
It then updates the transactions table, either by updating the status of the existing transaction or in the case of a refund, inserting a new record.

If the transaction is PAID, then the parent reservation is also updated in knack.

The response from the transaction update is then sent back to citybase.

Example citybase payload

```json
{
  "data": {
    "total_amount": 6000.0,
    "service_fee": 0.55,
    "amount": 6000.0,
    "voidable": true,
    "refundable": false,
    "id": 70022195,
    "payment_source_channel": "web",
    "status": "refunded",
    "request_id": "not used",
    "payment_type": "credit_card",
    "agency": "Austin Transportation",
    "credit_card": {
      "last_four": "1111",
      "card_type": "visa"
    },
    "bank_account": null,
    "created_at": "2022-10-13T17:58:00Z",
    "line_items": [
      {
        "id": "deea9dae-0121-49dc-be59-c3b40dccdb3d",
        "amount": 600000,
        "custom_attributes": {
          "invoice_number": "INV2022-100250",
          "knack_record_id": "638e5bd41370e500241c3e1f",
          "line_item_description": "Lamppost my big winter event",
          "line_item_sub_description": "INV2022-100250 - convention center"
        }
      }
    ],
    "associated_payments": [],
    "custom_attributes": [
      {
        "key": "invoice_number",
        "value": "INV2022-100250"
      },
      {
        "key": "knack_record_id",
        "value": "638e5bd41370e500241c3e1f"
      }
    ]
  }
}
```

## Development

The `docker-compose.yml` in this repository uses [profiles](https://docs.docker.com/compose/profiles/) to define separate application configurations for `development`, `staging`, `uat`, and `production`. You must specify which profile to use when starting the application.

In the root of the git repository, please:

- `docker compose --profile [development/staging/uat/production] build` will build the docker image for the services.
- Copy `env-template` to `.env` (which is git-ignored) and edit it to contain the desired environment variables. See 1PW entry "Citybase ENV"
- Use `docker compose up -d` with the `--profile` flag to start the application:
  - For **development**: `docker compose --profile development up -d`
  - For **staging**: `docker compose --profile staging up -d`
  - For **uat**: `docker compose --profile uat up -d`
  - For **production**: `docker compose --profile production up -d`
- Edit files in place outside of the docker instance as usual when developing

### Logging

Logs that are emitted are also sent to AWS Cloudwatch using [watchtower/](https://pypi.org/project/watchtower/), the log groups are named based on the environment variable used when spinning up the stack, `/dts/citybase/postback/{knack_env}`. Log streams are named based on the date in the YYYY/mm/dd format. Development logs have a 3 day retention rate, production and staging logs never expire.

## Deployment lifecycle

This project moves through four phases: development → staging → UAT → production. The `main` branch is the integration branch and should always be the most up to date (ahead of `uat` and `production`). Feature work happens on short‑lived branches and is merged into `main` via pull request.

### Development

- **Where it runs**: Locally on your computer, or in a personal checkout under your home directory on the bastion.
- **Branching**: Create a feature branch from `main` (for example, `developer-name/short-description`). Open a PR to merge into `main` when ready.
- **What moves forward**: Merging into `main` is the signal that work is ready to be exercised on staging.

### Staging

- **Host/Path**: Bastion at `/srv/atd-citybase-staging`
- **Branch**: `main`
- **URL**: [`https://citybase-staging.austinmobility.io`](https://citybase-staging.austinmobility.io)
- **Purpose**: Running the latest code in `main`. Used for internal verification before UAT.
- **How to update**: SSH to the bastion, then pull and restart the service.

```sh
cd /srv/atd-citybase-staging
git pull
docker compose --profile staging up -d
```

- **Automation today**: None. Manual `git pull` when you want to refresh staging.
- **Could be automated**: Add CI to auto-deploy on push to `main` (e.g., GitHub Action/Webhook that runs `git pull` and restarts the stack on the bastion).

### UAT (User Acceptance Testing)

- **Host/Path**: Bastion at `/srv/atd-citybase-uat`
- **Branch**: `uat`
- **URL**: [`https://citybase-uat.austinmobility.io`](https://citybase-uat.austinmobility.io)
- **Purpose**: Time-boxed snapshots of `main` for stakeholder testing. Sync is deliberate and controlled by the dev/project lead.
- **How to create/update a UAT snapshot**:
  - Ensure `uat` is brought up to the current `main`. Merge `main` → `uat` in GitHub or locally.
  - On the bastion, pull and restart:

```sh
# In your local clone or via GitHub PR
git checkout uat
git merge main
git push origin uat

# On the bastion host
cd /srv/atd-citybase-uat
git pull
docker compose --profile staging up -d
```

- **Automation today**: None (by design). Dev lead decides when to sync `main` into `uat` to align with upstream Citybase coordination.
- **Could be automated**: CI with a manual approval step to deploy `uat` on demand.

### Production

- **Host/Path**: Bastion at `/srv/atd-citybase-production`
- **Branch**: `production`
- **URL**: [`https://citybase.austinmobility.io`](https://citybase.austinmobility.io)
- **Purpose**: Live service.
- **Promotion**: After UAT sign‑off, merge the approved code into `production` (typically `main` → `production`, or `uat` → `production` if you used `uat` as the exact release snapshot).
- **How to deploy**:

```sh
# In your local clone or via GitHub PR
git checkout production
git merge main   # or: git merge uat
git push origin production

# On the bastion host
cd /srv/atd-citybase-production
git pull
docker compose --profile production up -d
```

- **Automation today**: None.
- **Could be automated**: CI/CD pipeline that deploys `production` on push, optionally gated by required reviews and manual approvals.

### Branching and promotion rules

- **`main` is the source of truth**: It should always be ahead of `uat` and `production` in commit history.
- **Environment branches are deployment targets**: Do not merge code into `uat` or `production` without first sending that code through `main`. These deployment targets may accumulate merge commits which creep ahead of `main` and this is fine, or you can merge them back into `main` if you'd prefer to manage not have the deployment targets have any commits that are not in the upstream integration branch.
- **Promotions are merges from left to right**: `main` → `uat` (when needed) → `production` (after approval). For hotfixes, merge the fix into `main`, then promote forward.
- **Service restarts**: After pulling on the bastion, restart the stack with the correct `docker compose --profile {environment} up -d` command for that environment.

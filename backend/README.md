## Prerequisites

The steps below will help you fill in the right details in the settings file. To begin with, copy the `settings.conf.example.json` to `settings.conf.json`

You will need a Linux or Mac OS environment to run this backend.

### EthVigil Beta Developer Account

[https://github.com/blockvigil/ethvigil-cli](https://github.com/blockvigil/ethvigil-cli)

Follow the instructions contained in the link above to install `ev-cli`, the CLI tool to interact with EthVigil APIs and also complete your signup for a developer account on EthVigil.

### EthVigil Python SDK

[https://github.com/blockvigil/ethvigil-python-sdk](https://github.com/blockvigil/ethvigil-python-sdk)

With the fresh EthVigil Beta signup and CLI installed, next up is installation of the EthVigil Python SDK. 

Run the following command
```bash
pip install git+https://github.com/blockvigil/ethvigil-python-sdk.git
```

### Amazon SES credentials

The backend code currently uses SES credentials to send out emails. Find the following section in the settings file and fill in the neccessary details:

```
"SES_CREDENTIALS": {  
    "from": "",  
    "region": "",  
    "accessKeyId": "",  
    "secretAccessKey": "",  
    "accountId": 0  
  },
  ```


### Stripe Identity Services Credentials

The automated KYC is supported thanks to [Stripe Identity Verification](https://stripe.com/docs/identity) and we have provided two separate configurations in case you wish to run the backend in a 'demo' or 'non-live' mode. Enter the relevant stripe API keys over here.

```
"STRIPE_KEY": {  
  "DEMO": "",  
  "LIVE": ""  
},
```

### Deploy the main contract

Use EthVigil to deploy the Solidity Smart Contract, `AdabdhaMain.sol`.

* [Deploy contract from Web UI](https://ethvigil.com/docs/web_onboarding/#deploy-a-solidity-smart-contract)
* [Deploy contract from CLI](https://ethvigil.com/docs/cli_onboarding/#deploy-a-solidity-smart-contract)

## Running the backend

### `server.py`

This is the REST interface of the backend which communicates with the frontend and allows operations on forms, passes, KYC verification as resources. The following starts a Flask server on the port `5000`.

Run it with 
```bash
./server.sh
```

### `webhook_listener.py`

Catches webhook updates from EthVigil corresponding to smart contract events emitted from `AdabdhaMain.sol`. Critical to correctly persisting a cache of smart contract activity and triggering automated parts of the workflow. 

It runs on port `5687` and should be available as a publicly reachable URL endpoint. 

>Tip: Open a SSH tunnel or use [ngrok](https://ngrok.io) to open up the server running at `5687` as a publicly reachable URL

Set up the public URL endpoint as a webhook integration for the deployed smart contract.

* [From Web UI](https://ethvigil.com/docs/web_onboarding/#adding-integrations)
* [From CLI](https://ethvigil.com/docs/cli_onboarding/#adding-integrations)

Run it with

```bash
./webhook.sh
```

### `stripe_listener.py`

Catches webhook updates from Stripe Identity services and persists information on smart contract in case of successful verification.

This listens on `0.0.0.0:8000/hooks`. Ensure this is also publicly reachable as explained above.

Run it with

```bash
./stripe_listener.sh
```


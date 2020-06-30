import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from redis_conn import provide_redis_conn
import json
import eth_utils
from ethvigil.EVCore import EVCore
from threading import Thread
from constants import *
from email_helper import send_ses_email
import requests

evc = EVCore(verbose=False)

with open('settings.conf.json', 'r') as f:
    settings = json.load(f)

main_contract_instance = evc.generate_contract_sdk(contract_address=settings['MAIN_CONTRACT'], app_name='AdabdhaMain')

app = Flask(__name__)
if settings['CORS_ENABLED']:
    CORS(app)

@provide_redis_conn
def get_verification_intent_mode(user_eth_address, redis_conn=None):
    # clear stored verification intent token
    vi_token = redis_conn.get(REDIS_ADABDHA_USER_VI_TOKEN.format(user_eth_address))
    if not vi_token:
        return None
    vi = vi_token.decode('utf-8')
    # get mode from redis
    m = redis_conn.get(REDIS_ADABDHA_VI_LIVE_MODE.format(vi))
    vi_mode = bool(int(m))
    return vi_mode

def get_approved_forms_eventlogs(track_address, evcore_obj: EVCore):
    api_key = evcore_obj._api_write_key
    contract_address = settings['MAIN_CONTRACT']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{evc._settings["REST_API_ENDPOINT"]}/cachedeventdata'
    method_args = {
        'contract': contract_address,
        'event_name': 'FormApproved',
        'indexed_param_name': 'ethAddress',
        'indexed_param_value': track_address
    }
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    print(r.text)
    r = r.json()
    data = r['data']
    form_uuidhashes = list()
    for cache_entry_with_ts in data:
        event_data = json.loads(cache_entry_with_ts[0])
        form_uuidhashes.append(event_data['uuidHash'])
    return form_uuidhashes

@provide_redis_conn
def get_base_id_data(user_eth_address, redis_conn=None):
    temp_pass_data = redis_conn.get(REDIS_ADABDHA_USER_VERIFIED_IDENTITY.format(user_eth_address))
    if not temp_pass_data:
        print(f'Could not find base identity data for user {user_eth_address}')
        return None
    else:
        base_pass_data = json.loads(temp_pass_data)
        return base_pass_data

@provide_redis_conn
def process_payload(request_json, redis_conn=None):
    event_name = request_json.get('event_name', None)
    event_data = request_json.get('event_data', None)
    contract_address = request_json.get('contract', None)
    if contract_address != settings['MAIN_CONTRACT']:
        return
    tx_hash = request_json.get('txHash', None)
    tx_hash_etherscan = 'https://goerli,etherscan.io/tx/' + tx_hash
    if event_name == 'NewForm' or event_name == 'FormApproved' or event_name == 'FormRejected':
        set_status = {
            'NewForm': 0,
            'FormApproved': 3,
            'FormRejected': 4
        }

        form_uuid_hash = event_data['uuidHash']
        user_eth_address = eth_utils.to_normalized_address(event_data['ethAddress'])
        u = redis_conn.hget(
            REDIS_ADABDHA_USERS,
            user_eth_address
        )
        if not u:
            print(f'Could not get user details for eth address {user_eth_address} connected to form')
            return
        user_details = json.loads(u)
        form_data_redis = redis_conn.hget(
            REDIS_ADABDHA_FORMS,
            form_uuid_hash
        )
        if form_data_redis:
            form_data_redis = json.loads(form_data_redis)
            form_data_redis['status'] = set_status[event_name]
            redis_conn.hset(
                REDIS_ADABDHA_FORMS,
                form_uuid_hash,
                json.dumps(form_data_redis, separators=(',', ':')).encode('utf-8')
            )
            if event_name == 'NewForm':
                redis_conn.zrem(
                    'adabdha:pendingUserForms:{}'.format(user_eth_address),
                    form_uuid_hash
                )
            if event_name == 'FormApproved':

                # send out email
                form_action_email_text = f'Form {form_data_redis["uuid"]} is approved.\n\n'
                if user_details['kycVerified'] != 'verified':
                    form_action_email_text += 'Please complete your KYC verification for a pass to be generated.'
                else:
                    form_action_email_text += 'Please wait for your pass to be generated and the next confirmation email.'
                if settings['EMAIL_SEND']:
                    t = send_ses_email(
                        email_addr=user_details['email'],
                        subject=f'Form {form_data_redis["uuid"]} is approved',
                        text=form_action_email_text
                    )
                    if t:
                        print('Sent out email for Form approval ' + form_data_redis['uuid'])
                    else:
                        print('Could not send email for Form approval ' + form_data_redis['uuid'])
                # auto generate a pass if KYC details are already verified
                if user_details['kycVerified'] == 'verified':
                    # pull pass data
                    p = redis_conn.get(REDIS_ADABDHA_USER_VERIFIED_IDENTITY.format(user_eth_address))
                    if not p:
                        print(f'Could not find pass data for user {user_eth_address}')
                        return
                    # pass_data_json = json.loads(p)
                    base_id_data = json.loads(p)
                    personal_details = base_id_data['person_details']
                    id_details = base_id_data['document_details']
                    mock_data_mode = not (get_verification_intent_mode(user_eth_address))
                    stored_pass_data = {
                        'first_name': personal_details['first_name'],
                        'last_name': personal_details['last_name'],
                        'identity_document_type': id_details['document_type'],
                        'city': form_data_redis['city'],
                        'state': form_data_redis['state'],
                        'purpose': form_data_redis['purpose'],
                        'movement': form_data_redis['movement'],
                        'api_prefix': evc._settings["REST_API_ENDPOINT"]+'/contract/'+settings['MAIN_CONTRACT'],
                        'mock_data': mock_data_mode
                    }
                    redis_conn.set(
                        REDIS_ADABDHA_USER_FORM_PASS_DATA.format(form_uuid_hash, user_eth_address),
                        json.dumps(stored_pass_data, separators=(',', ':')).encode('utf-8')
                    )
                    pass_data_hash = '0x' + eth_utils.keccak(text=json.dumps(stored_pass_data, separators=(',', ':'))).hex()
                    # send call to generate pass
                    tx = main_contract_instance.generatePass(
                        ethAddress=user_eth_address,
                        formUUIDHash=form_uuid_hash,
                        passHash=pass_data_hash
                    )
                    print('Generated pass on contract with tx ', tx[0]['txHash'])
            if event_name == 'FormRejected':
                if settings['EMAIL_SEND']:
                    t = send_ses_email(
                        email_addr=user_details['email'],
                        subject=f'Form {form_data_redis["uuid"]} is rejected',
                        text=f'Form {form_data_redis["uuid"]} is rejected.'
                    )
                    if t:
                        print(f'Sent out email for Form {form_uuid_hash} rejection')
                    else:
                        print(f'Could not send out email for form {form_uuid_hash} rejection')
    if event_name == 'UserStatusUpdated':
        user_states_flags_map = {
            0: 'unverified',  # useless. dummy.
            1: 'otpVerified',
            2: 'kycVerified'
        }
        user_eth_address = eth_utils.to_normalized_address(event_data['ethAddress'])
        user_updated_status = event_data['status']
        # get user details
        redis_user_details = redis_conn.hget(REDIS_ADABDHA_USERS, user_eth_address)
        if not redis_user_details:
            print(f"Could not find details in Redis for user {user_eth_address}")
            return
        user_details = json.loads(redis_user_details)
        if user_updated_status == 1:
            user_details['otpVerified'] = True
        elif user_updated_status == 2:
            user_details['kycVerified'] = 'verified'
            # check submitted forms for this user
            # check approved status of the forms
            # generate passes for the approved forms
            approved_forms = get_approved_forms_eventlogs(user_eth_address, main_contract_instance)
            pass_data_hash = None
            # send out KYC verification email
            kyc_verification_email_text = f'Your KYC  submission was verified.\n\n'
            if len(approved_forms):
                kyc_verification_email_text += 'Please wait for your pass to be generated and the next confirmation email.'
            else:
                kyc_verification_email_text += 'Please complete your application form to generate a pass.'
            if settings['EMAIL_SEND']:
                t = send_ses_email(
                    email_addr=user_details['email'],
                    subject=f'Your KYC verification is complete!',
                    text=kyc_verification_email_text
                )
                if t:
                    print('Sent out email for KYC verification for user '+user_eth_address)
                else:
                    print('Could not send email for KYC verification for user ' + user_eth_address)
            for form_uuid_hash in approved_forms:
                # get the form specific pass data
                f = redis_conn.hget(
                    REDIS_ADABDHA_FORMS,
                    form_uuid_hash
                )
                base_pass_data = get_base_id_data(user_eth_address)
                if f and base_pass_data:
                    personal_details = base_pass_data['person_details']
                    id_details = base_pass_data['document_details']
                    form_data_redis = json.loads(f)
                    mock_data_mode = not(get_verification_intent_mode(user_eth_address))
                    stored_pass_data = {
                        'first_name': personal_details['first_name'],
                        'last_name': personal_details['last_name'],
                        'identity_document_type': id_details['document_type'],
                        'city': form_data_redis['city'],
                        'state': form_data_redis['state'],
                        'purpose': form_data_redis['purpose'],
                        'movement': form_data_redis['movement'],
                        'api_prefix': evc._settings["REST_API_ENDPOINT"]+'/contract/'+settings['MAIN_CONTRACT'],
                        'mock_data': mock_data_mode
                    }
                    pass_data_hash = '0x' + eth_utils.keccak(text=json.dumps(stored_pass_data, separators=(',', ':'))).hex()
                    print(f'Prepared pass for form UUID hash {form_uuid_hash}: {stored_pass_data}')
                    try:
                        tx = main_contract_instance.generatePass(
                            ethAddress=user_eth_address,
                            formUUIDHash=form_uuid_hash,
                            passHash=pass_data_hash
                        )
                    except Exception as e:
                        print(
                            f'Exception sending out transaction for pass generation against form UUID hash {form_uuid_hash}')
                        print(e)
                    else:
                        print(
                            f'Sent out tx {tx[0]["txHash"]} for pass generation against form UUID hash {form_uuid_hash}')
                        redis_conn.set(
                            REDIS_ADABDHA_USER_FORM_PASS_DATA.format(form_uuid_hash, user_eth_address),
                            json.dumps(stored_pass_data, separators=(',', ':')).encode('utf-8')
                        )
                time.sleep(1)
        redis_conn.hset(
            REDIS_ADABDHA_USERS,
            user_eth_address,
            json.dumps(user_details, separators=(',', ':')).encode('utf-8')
        )
        print('Updated user data in Redis to: ', user_details)
        return

    if event_name == 'PassGenerated':
        user_eth_address = eth_utils.to_normalized_address(event_data['ethAddress'])
        form_uuid_hash = event_data['formUUIDHash']

        received_pass_data_hash = event_data['passDataHash']
        # get temporarily stored pass data
        p = redis_conn.get(REDIS_ADABDHA_USER_FORM_PASS_DATA.format(form_uuid_hash, user_eth_address))
        if not p:
            print(f'Could not find pass data for user {user_eth_address}')
            return
        pass_data_json = json.loads(p)
        print('Found pass data stored locally ', p)
        stored_pass_data_hash = '0x' + eth_utils.keccak(text=json.dumps(pass_data_json, separators=(',', ':'))).hex()
        if received_pass_data_hash != stored_pass_data_hash:
            print('Received pass data hash from event: ', received_pass_data_hash)
            print('Local cache of pass data hash: ', stored_pass_data_hash)
            print('Received and local cache of pass data do not match. Dying...')
            return
        redis_conn.set(
            REDIS_ADABDHA_USER_PASS_DATAHASH_CONFIRMED.format(user_eth_address),
            received_pass_data_hash
        )
        redis_conn.hset(
            REDIS_ADABDHA_ALL_PASSES,
            stored_pass_data_hash,
            p
        )
        redis_conn.set(
            REDIS_ADABDHA_PASS_STATUS.format(stored_pass_data_hash),
            str(int(True))
        )

        # get user details
        redis_user_details = redis_conn.hget(REDIS_ADABDHA_USERS, user_eth_address)
        if not redis_user_details:
            print(f"Could not find details in Redis for user {user_eth_address}")
            return
        user_details = json.loads(redis_user_details)
        # send pass generation confirmation
        if settings['EMAIL_SEND']:
            shortened_phash = received_pass_data_hash[:5]+'...'+received_pass_data_hash[-3:]
            t = send_ses_email(
                email_addr=user_details['email'],
                subject=f'Your pass ID {shortened_phash} has been generated!',
                text=f'Congratulations! Your pass ID {received_pass_data_hash} has been generated.'
                f'\n\nAccess the Passes section from your Dashboard to review it.'
            )
            if t:
                print('Sent out email for pass generation for user ' + user_eth_address)
            else:
                print('Could not send email for pass generation for user ' + user_eth_address)

    if event_name == 'PassRevoked':
        received_pass_data_hash = event_data['passDataHash']
        # check if pass data hash exists
        if (redis_conn.hexists(REDIS_ADABDHA_ALL_PASSES, received_pass_data_hash)):
            redis_conn.set(REDIS_ADABDHA_PASS_STATUS.format(received_pass_data_hash), str(int(False)))
            user_eth_address = eth_utils.to_normalized_address(event_data['ethAddress'])
            # get user details
            redis_user_details = redis_conn.hget(REDIS_ADABDHA_USERS, user_eth_address)
            if not redis_user_details:
                print(f"Could not find details in Redis for user {user_eth_address}")
                return
            user_details = json.loads(redis_user_details)
            # send pass generation confirmation
            if settings['EMAIL_SEND']:
                shortened_phash = received_pass_data_hash[:5] + '...' + received_pass_data_hash[-3:]
                t = send_ses_email(
                    email_addr=user_details['email'],
                    subject=f'Your pass ID {shortened_phash} has been revoked!',
                    text=f'Your pass ID {received_pass_data_hash} has been revoked'
                    f'\n\nAccess the Passes section from your Dashboard to review it.'
                )
                if t:
                    print('Sent out email for pass revocation for user ' + user_eth_address)
                else:
                    print('Could not send email for pass revocation for user ' + user_eth_address)


@app.route('/', methods=['POST'])
def main_listener():
    request_json = request.json
    print ("\n"*2+"Incoming webhook payload\n==========")
    print(request_json)
    print('=============='+'\n'*2)
    t = Thread(target=process_payload, args=(request_json, ))
    t.start()
    return jsonify({'success': True})

import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from redis_conn import provide_redis_conn
import json
import eth_utils
import requests
from ethvigil.EVCore import EVCore
from threading import Thread
from constants import *
from email_helper import send_ses_email

evc = EVCore(verbose=False)

with open('settings.conf.json', 'r') as f:
    settings = json.load(f)

main_contract_instance = evc.generate_contract_sdk(contract_address=settings['MAIN_CONTRACT'], app_name='AdabdhaMain')

app = Flask(__name__)
if settings['CORS_ENABLED']:
    CORS(app)


@provide_redis_conn
def process_payload(webhook_payload, redis_conn=None):
    payload_type = webhook_payload['type']

    if 'identity.verification_intent' in payload_type:
        user_eth_address = webhook_payload['data']['object']['metadata'].get('ethAddress')
        if user_eth_address:
            user_eth_address = eth_utils.to_normalized_address(user_eth_address)
            # check whether vi_ token set against this user
            try:
                stored_vi = redis_conn.get(REDIS_ADABDHA_USER_VI_TOKEN.format(user_eth_address)).decode('utf-8')
            except:
                # print('Did not find verification intent token against user ', user_eth_address)
                return
            payload_vi_token = webhook_payload['data']['object']['id']
            if stored_vi != payload_vi_token:
                # print(f'Stored VI token {stored_vi} does not match received token {payload_vi_token}')
                return
            user_details = redis_conn.hget(
                REDIS_ADABDHA_USERS,
                user_eth_address
            )
            user_details_json = json.loads(user_details)
            verification_status = None
            if payload_type == 'identity.verification_intent.succeeded':
                extracted_user_details = dict()
                extracted_user_details['document_details'] =  webhook_payload['data']['object']['verification_reports']['identity_document']['document_details']
                extracted_user_details['person_details'] = webhook_payload['data']['object']['verification_reports']['identity_document']['person_details']
                extracted_user_details.update({'stripe_verification_intent': webhook_payload['data']['object']['verification_reports']['identity_document']['verification_intent']})
                redis_conn.set(
                    REDIS_ADABDHA_VI_STATUS.format(payload_vi_token),
                    str(int(True))
                )
                redis_conn.set(
                    REDIS_ADABDHA_USER_VERIFIED_IDENTITY.format(user_eth_address),
                    json.dumps(extracted_user_details).encode('utf-8')
                )
                verification_status = 'verified'
            elif payload_type == 'identity.verification_intent.updated':
                try:
                    if webhook_payload['data']['object']['last_verification_error']['type'] == 'unverified':
                        verification_status = 'failed'
                        redis_conn.set(
                            REDIS_ADABDHA_VI_STATUS.format(payload_vi_token),
                            str(int(False))
                        )
                        # send verification failed email
                        kyc_verification_email_text = f'Your KYC verification failed. Visit the dashboard to review and resubmit your KYC application'
                        if settings['EMAIL_SEND']:
                            t = send_ses_email(
                                email_addr=user_details_json['email'],
                                subject=f'Your KYC verification failed',
                                text=kyc_verification_email_text
                            )
                            if t:
                                print('Sent out email for failed KYC verification for user ' + user_eth_address)
                            else:
                                print('Could not send email for failed KYC verification for user ' + user_eth_address)
                except:
                    pass
            elif payload_type == 'identity.verification_intent.processing':
                print('Processing update...')
                # check if VI status is failed or successful
                s = redis_conn.get(REDIS_ADABDHA_VI_STATUS.format(payload_vi_token))
                print(f'Got redis status for VI {payload_vi_token}: {s}')
                if s and (int(s) == 1 or int(s) == 0):
                    return  # do nothing
                # set status pending on KYC verification
                if not webhook_payload['data']['object']['last_verification_error']:
                    print('Found NO verification error on intent processing update')
                    verification_status = 'pending'
                else:
                    print('Found last verification error on intent processing update')
                    verification_status = 'failed'
                    redis_conn.set(
                        REDIS_ADABDHA_VI_STATUS.format(payload_vi_token),
                        str(int(False))
                    )
            if user_details:
                if verification_status:
                    if verification_status != 'verified':
                        # we set verified in redis only after receiving smart contract event confirmation
                        user_details_json['kycVerified'] = verification_status
                        redis_conn.hset(
                            REDIS_ADABDHA_USERS,
                            user_eth_address,
                            json.dumps(user_details_json).encode('utf-8')
                        )
                        print(f'Redis: Set {user_eth_address} kyc status to {verification_status}')

                    if verification_status == 'verified':
                        # write to contract
                        tx = main_contract_instance.submitUserKYCVerification(ethAddress=user_eth_address)
                        print('Verified user KYC status on contract with tx: ', tx)
                        return
                else:
                    return
            else:
                print('Did not find user entry for eth address ', user_eth_address)
                return
        else:
            print('Did not receive user eth address in payload')
            return

@app.route('/hooks', methods=['POST'])
def main_listener():
    webhook_payload = request.json
    print("Incoming webhook payload\n==========")
    print(webhook_payload)
    print('==============\n\n\n')
    t = Thread(target=process_payload, args=(webhook_payload, ))
    t.start()
    return jsonify({'success': True})

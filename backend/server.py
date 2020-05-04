from flask import Flask, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields, reqparse, inputs
from flask_login import LoginManager, current_user, login_required

import time
import requests
import random
from redis.sentinel import Sentinel
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial, wraps

import json
from email_helper import send_ses_email
import eth_utils
from eth_account.messages import defunct_hash_message
from eth_account.account import Account
import stripe

from ethvigil.EVCore import EVCore
from constants import *

evc = EVCore(verbose=False)

with open('settings.conf.json', 'r') as f:
    settings = json.load(f)

main_contract_instance = evc.generate_contract_sdk(contract_address=settings['MAIN_CONTRACT'], app_name='AdabdhaMain')

REDIS_CONF = {
    "SENTINEL": settings['REDIS']['SENTINEL']
}
REDIS_DB = settings['REDIS']['DB']
REDIS_PASSWORD = settings['REDIS']['PASSWORD']

sentinel = Sentinel(sentinels=REDIS_CONF['SENTINEL']['INSTANCES'], db=REDIS_DB, password=REDIS_PASSWORD,
                    socket_timeout=0.1)
redis_master = sentinel.master_for(REDIS_CONF['SENTINEL']['CLUSTER_NAME'])

app = Flask(__name__)
if settings['CORS_ENABLED']:
    CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)

def recover_address_from_sig():
    signed_timestamp_token = request.headers.get('X-Wallet-Signature')
    if signed_timestamp_token:
        # 'adabdha_'+timestamp+':'+walletSign('adabdha_'+timestamp)
        string_data, signed_data = signed_timestamp_token.split(':')
        string_data_hashed = defunct_hash_message(string_data.encode('utf-8'))
        recovered_eth_address = Account.recoverHash(message_hash=string_data_hashed, signature=signed_data)
        recovered_eth_address = eth_utils.to_normalized_address(recovered_eth_address)
        return recovered_eth_address
    else:
        return None

class AdabdhaUserPrototype():
    def __init__(self, json_details):
        self.user_details = json_details
        for each in json_details.keys():
            self.__setattr__(each, json_details[each])

    def __repr__(self):
        return json.dumps(self.user_details)

    def is_authenticated(self):
        return True

@login_manager.request_loader
def load_user_from_timestamp_token(request):
    signed_timestamp_token = request.headers.get('X-Wallet-Signature')
    ret = None
    if signed_timestamp_token:
        # 'adabdha_'+timestamp+':'+walletSign('adabdha_'+timestamp)
        recovered_eth_address = recover_address_from_sig()
        u = redis_master.hget(REDIS_ADABDHA_USERS, recovered_eth_address)
        if not u:
            ret = None
        else:
            try:
                user_details = json.loads(u)
            except json.JSONDecodeError:
                ret = None
            else:
                ret = AdabdhaUserPrototype(user_details)
    else:
        ret = None
    return ret


@login_manager.unauthorized_handler
def unauthorized():
    return {'success': False, 'error': 'Unauthorized'}, 401


def only_ethaddress_allowed(f):
    """
    check identified user from header X-Wallet-Signature.
    If API paylaod contains argument for ethAddress allow only if the identifying user is the same as ethAddress
    :param f:
    :return:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            supplied_eth_addr = api.payload['ethAddress']
        except:
            supplied_eth_addr = None
        if not supplied_eth_addr:
            return {'success': False, 'error': 'BadPayload'}, 400
        header_sig_eth_address = recover_address_from_sig()
        if not header_sig_eth_address:
            return {'success': False, 'error': 'Unauthorized'}, 401
        if header_sig_eth_address == eth_utils.to_normalized_address(api.payload['ethAddress']):
            return f(*args, **kwargs)
        else:
            return {'success': False, 'error': 'Unauthorized'}, 401
    return wrapper

def get_check_usermode_wrapper(god_mode=False):
    def deco(func):
        def mod_func(*args, **kwargs):
            try:
                is_admin = current_user.isAdmin
            except AttributeError:
                is_admin = False
            path_eth_addr = kwargs.get('ethAddress')
            if is_admin or (path_eth_addr and current_user.ethAddress == eth_utils.to_normalized_address(path_eth_addr)) or god_mode:
                return func(*args, **kwargs)
            else:
                return {'success': False, 'error': 'Unauthorized'}, 401
        return mod_func
    return deco

only_allowed_user_or_admin = get_check_usermode_wrapper()
only_form_approval_god_mode = get_check_usermode_wrapper(god_mode=settings['GOD_MODE_APPROVAL'])

api = Api(app, version='0.1', title='Adabdha Identity Oracle MVP API',
          description='A simple API for the Identity Oracle for Adabdha™️')

ns_toplevel_users = api.namespace('users', description='Adabdha user operations')

user_model = api.model('User', {
    'email': fields.String(required=True, description='User email'),
    'ethAddress': fields.String(required=True, description='User ethereum address'),
    'otpVerified': fields.Boolean(readonly=True, description='Is user OTP verified'),
    'kycVerified': fields.String(readonly=True, description='user KYC verification state'),
    'otp': fields.Integer(readonly=True, description='Assigned OTP')
})

form_data_model = api.model('FormData', {
    'ethAddress': fields.String(required=True, description='Ethereum address of user'),
    'uuid': fields.String(required=True, description='UUID of the application'),
    'formData': fields.Arbitrary(description='JSON data')
})

form_op_model = api.model('FormOperation', {
    'action': fields.String(required=True, description="Action on form: approve or reject")
})


user_put_parser = reqparse.RequestParser()
user_put_parser.add_argument('otp', help='Confirm the OTP', type=int, location='json')

updateops_return = api.model('UserUpdateOpsReturn', {
    'txHash': fields.String(required=True, description='transaction hash sent out'),
    'contractAddress': fields.String(required=True, description='contract address to which tx is sent'),
    'methodName': fields.String(required=True, description='method called in transaction'),
})

user_post_parser = reqparse.RequestParser()
user_post_parser.add_argument('action', help='initiateVerify | initiateMockVerify', location='json', default='initiateVerify | initiateMockVerify')
user_post_parser.add_argument(
    'return_url',
    help='URL to redirect to once verification process is complete',
    location='json'
)


pass_modify_parser = reqparse.RequestParser()
pass_modify_parser.add_argument('action', help='revoke | [....]', location='json')


user_post_return = api.model('UserPostReturn', {
    'id': fields.String(required=True, description='Stripe verification intent ID'),
    'redirect': fields.String(required=False, description='Redirect URL for ID verification')
})

user_passes_return = api.model('UserPassesReturn', {
    'passDataHash': fields.String(required=True, description='Hash of JSON serialized pass data committed on contract'),
    # 'passData': fields.Nested(required=True, description='JSON serialized pass data'),
    'formUUIDHash': fields.String(required=True, description='UUID Hash of JSON serialized form data against which '
                                                             'pass was generated'),
    'timestamp': fields.Integer(required=True, description='Timestamp of PassGenerated event')
})

user_get_return = api.model('UserGetReturn', {
    'email': fields.String,
    'ethAddress': fields.String,
    'otpVerified': fields.Boolean,
    'kycVerified': fields.String,
    'isAdmin': fields.Boolean
})

ns_indiv_user = api.namespace('user', description='User specific operations')
ns_forms = api.namespace('forms', description='user data form submission and retrieval')
ns_form_operations = api.namespace('form', description='user data form submission and retrieval')
ns_user_pass = api.namespace('pass', description='Passes generated for users')
ns_passes = api.namespace('passes', description='All passes')

@ns_toplevel_users.route('/')
class AdabdhaUsers(Resource):
    @only_ethaddress_allowed
    @ns_toplevel_users.doc('create_user')
    @ns_toplevel_users.expect(user_model)
    def post(self):
        """Initiate registration of a new user"""
        # add entry into redis, return OTP
        user_obj = api.payload
        eth_address = eth_utils.to_normalized_address(api.payload['ethAddress'])
        otp = random.choice(range(100000, 999999))
        if settings['EMAIL_SEND']:
            email_status = send_ses_email(
                email_addr=api.payload['email'],
                subject='Your Adabdha OTP',
                text='Confirm your OTP on Adabdha: ' + str(otp)
            )
            if not email_status:
                return user_obj, 500
        redis_master.set( eth_address + '_otp', otp, ex=900)
        user_obj = {
            'email': api.payload['email'],
            'ethAddress': eth_address,
            'otpVerified': False,
            'kycVerified': 'unverified'
        }
        redis_master.hset(
            REDIS_ADABDHA_USERS,
            eth_address,
            json.dumps(user_obj).encode('utf-8')
        )

        return user_obj, 201

    @login_required
    @only_allowed_user_or_admin
    @ns_toplevel_users.doc('list_users')
    @ns_toplevel_users.marshal_list_with(user_get_return)
    def get(self):
        """Returns all users"""
        u_l = list()
        try:
            users_mapping = redis_master.hgetall(REDIS_ADABDHA_USERS)
        except json.JSONDecodeError:
            return [], 404
        else:
            for k, v in users_mapping.items():
                v = json.loads(v)
                if 'isAdmin' not in v:
                    v['isAdmin'] = False
                _u_v = redis_master.get(REDIS_ADABDHA_USER_VI_TOKEN.format(k.decode('utf-8')))
                if not _u_v:
                    # no waiting verificaion intents found
                    pass
                else:
                    # check VI status
                    v_s = redis_master.get(REDIS_ADABDHA_VI_STATUS.format(_u_v.decode('utf-8')))
                    if v_s and int(v_s) == -1:
                        # set kyc verified status to requested
                        v['kycVerified'] = 'requested'
                u_l.append(v)
            return u_l


@ns_indiv_user.route('/<string:ethAddress>')
@ns_indiv_user.param('ethAddress', 'The Ethereum address of the user')
class IndividualAdabdhaUserByEthAddr(Resource):
    """Operations on individual Adabdha users"""
    @login_required
    @only_allowed_user_or_admin
    @ns_indiv_user.expect(user_put_parser)
    @ns_indiv_user.marshal_with(updateops_return, 201)
    def put(self, ethAddress):
        eth_address = eth_utils.to_normalized_address(ethAddress)
        if current_user.ethAddress != eth_address:
            return {'success': False, 'error': 'Unauthorized'}
        parsed_args = user_put_parser.parse_args()
        user_details = json.loads(redis_master.hget('adabdha:users', eth_address))
        if parsed_args.get('otp'):
            stored_otp = redis_master.get(eth_address + '_otp')
            if not stored_otp:
                return parsed_args, 404
            else:
                stored_otp = int(stored_otp.decode('utf-8'))
                if stored_otp != parsed_args['otp']:
                    return parsed_args, 400
                else:
                    # Set OTP verified on user details only after transaction is confirmed on contract
                    # user_details.update({'otpVerified': True})
                    #
                    # redis_master.hset(
                    #     'adabdha:users',
                    #     eth_address,
                    #     json.dumps(user_details).encode('utf-8')
                    # )
                    # Add to main contract
                    email_hash = eth_utils.keccak(text=user_details['email']).hex()
                    email_hash = eth_utils.add_0x_prefix(email_hash)
                    add_user_params = dict(ethAddress=eth_address, emailHash=email_hash)
                    try:
                        tx = main_contract_instance.addUserByEmail(**add_user_params)
                        print('Confirmed user on contract with tx: ', tx[0]['txHash'])
                    except Exception as e:
                        print('Exception trying to add user details on Contract ', add_user_params, e)
                        return user_details, 400
                    else:
                        return_struct = {
                            'txHash': tx[0]['txHash'],
                            'contractAddress': settings['MAIN_CONTRACT'],
                            'methodName': 'addUserByEmail'
                        }
                        return return_struct, 201

    @ns_indiv_user.expect(user_post_parser)
    @ns_indiv_user.marshal_with(user_post_return, 201)
    def post(self, ethAddress):
        parsed_args = user_post_parser.parse_args()
        eth_address = eth_utils.to_normalized_address(ethAddress)
        return_url = api.payload['return_url']
        user_details = json.loads(redis_master.hget('adabdha:users', eth_address))
        action = parsed_args.get('action')
        if action == 'initiateVerify' or action == 'initiateMockVerify' \
                and user_details.get('kycVerified') not in ['verified', 'pending']:
            # check if vi token already exists and has been initiated for processing
            existing_vi = redis_master.get(REDIS_ADABDHA_USER_VI_TOKEN.format(eth_address))
            if existing_vi \
                and int(redis_master.get(REDIS_ADABDHA_VI_STATUS.format(existing_vi.decode('utf-8')))) == -1:
                return {'success': False, 'error': 'VerificationInitiated'}, 400
            if action == 'initiateVerify':
                stripe.api_key = settings['STRIPE_KEY']['LIVE']
                vi_live_mode = True
            else:
                stripe.api_key = settings['STRIPE_KEY']['DEMO']
                vi_live_mode = False
            stripe.api_version = '2018-11-08; identity_beta=v3'
            r = stripe.stripe_object.StripeObject().request(
                'post',
                '/v1/identity/verification_intents',
                {
                    'requested_verifications': [
                        'identity_document',
                        'selfie'
                    ],
                    'metadata': {
                        'ethAddress': eth_address
                    },
                    'return_url': return_url
                }
            )
            verification_intent_id = r['id']
            print('Got stripe verification intent ID : ', verification_intent_id)
            # print(r)
            # associate intent ID with user
            redis_master.set(
                REDIS_ADABDHA_USER_VI_TOKEN.format(eth_address),
                verification_intent_id,
                ex=600
            )
            redis_master.set(
                REDIS_ADABDHA_VI_STATUS.format(verification_intent_id),
                str(-1)
            )

            redis_master.set(
                REDIS_ADABDHA_VI_LIVE_MODE.format(verification_intent_id),
                str(int(vi_live_mode))
            )
            return {'id': verification_intent_id, 'redirect': r['next_action']['redirect_to_url']}, 201

    @login_required
    @only_allowed_user_or_admin
    @ns_indiv_user.marshal_with(user_get_return, 200)
    def get(self, ethAddress):
        ethAddress = eth_utils.to_normalized_address(ethAddress)
        u = redis_master.hget(REDIS_ADABDHA_USERS, ethAddress)
        if not u:
            return {}, 404
        details = json.loads(u)
        if 'isAdmin' not in details:
            details['isAdmin'] = False
        _u_v = redis_master.get(REDIS_ADABDHA_USER_VI_TOKEN.format(ethAddress))
        if not _u_v:
            # no waiting verificaion intents found
            pass
        else:
            # check VI status
            v_s = redis_master.get(REDIS_ADABDHA_VI_STATUS.format(_u_v.decode('utf-8')))
            if v_s and int(v_s) == -1:
                # set kyc verified status to requested
                details['kycVerified'] = 'requested'
        return details, 200

def get_NewForm_eventlogs(event_param_name, event_param_value, evcore_obj: EVCore):
    """
    :return Return event logs for `NewForm` events indexed by `event_param_name` and `event_param_value`
    """
    api_key = evcore_obj._api_write_key
    contract_address = settings['MAIN_CONTRACT']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{evc._settings["REST_API_ENDPOINT"]}/cachedeventdata'
    method_args = {
        'contract': contract_address,
        'event_name': 'NewForm',
        'indexed_param_name': event_param_name,
        'indexed_param_value': event_param_value
    }
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    # print(r.text)
    r = r.json()
    data = r['data']
    form_uuidhashes = dict()
    for cache_entry_with_ts in data:
        event_data = json.loads(cache_entry_with_ts[0])
        form_uuidhashes[event_data['uuidHash']] = {
                'uuidHash': event_data['uuidHash'],
                'formDataHash': event_data['formdataHash'],
                'timestamp': cache_entry_with_ts[1]
        }
    return form_uuidhashes

@ns_indiv_user.route('/<string:ethAddress>/forms')
@ns_indiv_user.param('ethAddress', 'Ethereum address associated with user')
class IndividualAdabdhaUserFormByEthAddr(Resource):
    @login_required
    @only_allowed_user_or_admin
    def get(self, ethAddress):
        forms = list()
        ethAddress = eth_utils.to_normalized_address(ethAddress)
        # fetch from event logs cache on EthVigil
        submitted_form_uuidhashes = get_NewForm_eventlogs('ethAddress', ethAddress, evc)
        # merge with locally stored applications
        pending_form_uuidhashes = redis_master.zrange(
            'adabdha:pendingUserForms:{}'.format(eth_utils.to_normalized_address(ethAddress)),
            0,
            -1,
            withscores=True
        )
        for _ in pending_form_uuidhashes:
            form_uuid_hash = _[0].decode('utf-8')
            timestamp = int(_[1])
            if form_uuid_hash not in submitted_form_uuidhashes:
                redis_form_data = redis_master.hget(
                    'adabdha:forms',
                    form_uuid_hash
                )
                if redis_form_data:
                    redis_form_data = redis_form_data.decode('utf-8')
                    hashed_formdata = eth_utils.keccak(text=redis_form_data).hex()
                    hashed_formdata = eth_utils.add_0x_prefix(hashed_formdata)
                    submitted_form_uuidhashes.update({
                        form_uuid_hash: {
                            'uuidHash': form_uuid_hash,
                            'formDataHash': hashed_formdata,
                            'timestamp': timestamp
                        }
                    })
            else:
                # update time stamp to hold submitted time instead of event time
                submitted_form_uuidhashes[form_uuid_hash]['timestamp'] = timestamp
        for each in submitted_form_uuidhashes:
            form_info_map = {}
            form_dets = submitted_form_uuidhashes[each]
            # further fetch form data JSON information from redis
            # and status information of form from contract
            redis_form_data = redis_master.hget('adabdha:forms', form_dets['uuidHash'])
            if not redis_form_data:
                return [], 404
            redis_form_data = json.loads(redis_form_data)
            form_uuid = redis_form_data.pop('uuid', None)
            form_status = redis_form_data.pop('status', None)
            form_user_eth_address = redis_form_data.pop('userEthAddress', None)
            form_info_map['formData'] = redis_form_data
            form_info_map['formDataHash'] = form_dets['formDataHash']
            form_info_map['uuid'] = form_uuid
            form_info_map['uuidHash'] = form_dets['uuidHash']
            form_info_map['timestamp'] = form_dets['timestamp']
            # form_contract_info = main_contract_instance.submittedForms(each['uuidHash'])
            # form_status= form_contract_info['status']
            form_info_map['status'] = form_status
            forms.append(form_info_map)
        return forms

@ns_forms.route('/')
class FormsResource(Resource):
    @login_required
    @only_allowed_user_or_admin
    def get(self):
        """
        Get all forms
        """
        all_formdata = redis_master.hgetall('adabdha:forms')
        form_uuid_hashes = list(map(lambda x: x.decode('utf-8'), all_formdata.keys()))
        new_forms_events = dict()

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_rpcresult = {
                executor.submit(
                    get_NewForm_eventlogs,
                    event_param_name='uuidHash',
                    event_param_value=form_uuid_hash,
                    evcore_obj=main_contract_instance
                ): form_uuid_hash
                for form_uuid_hash in form_uuid_hashes
            }
            for future in as_completed(future_to_rpcresult):
                # collect form uuid hashes
                form_uuid_hash = future_to_rpcresult[future]
                try:
                    form_logs = future.result()
                except Exception as exc:
                    # do something in future
                    print("Error fetching NewForm event logs for form UUID hash{}: {}".format(form_uuid_hash, exc))
                    continue
                else:
                    for x in form_logs.keys():
                        new_forms_events[x] = form_logs[x]

        print(all_formdata)
        transformed_all_formdata = list()
        for k, v in all_formdata.items():
            k_decoded = k.decode('utf-8')
            form_data = json.loads(v)
            form_uuid = form_data.pop('uuid', None)
            form_status = form_data.pop('status', None)
            form_user_eth_addr = form_data.pop('userEthAddress', None)
            return_mapping = {
                'formData': form_data,
                'uuid': form_uuid,
                'uuidHash': k_decoded,
                'status': form_status
            }
            return_mapping.update({'uuidHash': k_decoded})
            if form_user_eth_addr:
                print(f'Looking for form uuid hash {k_decoded} in {new_forms_events}')
                if k_decoded in new_forms_events:
                    return_mapping.update({'timestamp': new_forms_events[k_decoded]['timestamp'], 'ethAddress': form_user_eth_addr})
            transformed_all_formdata.append(return_mapping)
        del all_formdata
        return transformed_all_formdata, 201

    @login_required
    @ns_forms.expect(form_data_model)
    @ns_forms.marshal_with(updateops_return, 201)
    def post(self):
        """
        Creates a new form application
        """
        eth_address = api.payload['ethAddress']
        eth_address = eth_utils.to_normalized_address(eth_address)
        if not eth_address:
            return {}, 400
        try:
            user_details = json.loads(redis_master.hget('adabdha:users', eth_address))
        except json.JSONDecodeError:
            return {}, 404
        if not user_details:
            return user_details, 404
        if not api.payload['formData']:
            return {}, 400
        _form_data = json.loads(api.payload['formData'])
        serialized_form_data = json.dumps(_form_data, separators=(',', ':'))
        _form_data.update({'uuid': api.payload['uuid']})  # because we want to store the UUID information in local cache
        _form_data.update({'status': -1})  # because we want to store the UUID information in local cache
        _form_data.update({'userEthAddress': eth_address})
        hashed_formdata = eth_utils.keccak(text=serialized_form_data).hex()
        hashed_formdata = eth_utils.add_0x_prefix(hashed_formdata)
        hashed_uuid = eth_utils.add_0x_prefix(eth_utils.keccak(text=api.payload['uuid']).hex())

        redis_master.hset(
            'adabdha:forms',
            hashed_uuid,
            json.dumps(_form_data, separators=(',', ':')).encode('utf-8')
        )
        # Add to main contract
        update_formdata_params = dict(
            uuidHash=hashed_uuid,
            ethAddress=eth_address,
            formdataHash=hashed_formdata
        )
        try:
            tx = main_contract_instance.submitFormData(**update_formdata_params)
            print('Updated user form data on contract with tx: ', tx[0]['txHash'])
        except Exception as e:
            print('Exception trying to update user form data on Contract ', update_formdata_params, e)
            return {}, 400
        else:
            redis_master.zadd(
                f'adabdha:pendingUserForms:{eth_address}',
                {hashed_uuid: int(time.time())}
            )
            return_struct = {
                'txHash': tx[0]['txHash'],
                'contractAddress': settings['MAIN_CONTRACT'],
                'methodName': 'submitFormData'
            }
            return return_struct, 201


@ns_form_operations.route('/<string:uuid>')
class IndividualFormResource(Resource):
    @login_required
    @only_form_approval_god_mode
    @ns_form_operations.expect(form_op_model)
    @ns_form_operations.marshal_with(updateops_return, 201)
    def post(self, uuid):
        if not (api.payload['action'] == 'approve' or api.payload['action'] == 'reject'):
            return {}, 400
        action = api.payload['action']
        hashed_uuid = eth_utils.add_0x_prefix(eth_utils.keccak(text=uuid).hex())
        form_action_params = dict(uuidHash=hashed_uuid)
        _fd = redis_master.hget(
            REDIS_ADABDHA_FORMS,
            hashed_uuid
        )
        if not _fd:
            return {}, 404
        redis_form_data = json.loads(_fd)
        try:
            if action == 'approve':
                # set form status to pending approval
                tx = main_contract_instance.approveForm(**form_action_params)
                redis_form_data.update({'status': 'pendingApproval'})
            else:
                tx = main_contract_instance.rejectForm(**form_action_params)
                redis_form_data.update({'status': 'pendingRejection'})
            redis_master.hset(
                REDIS_ADABDHA_FORMS,
                hashed_uuid,
                json.dumps(redis_form_data).encode('utf-8')
            )
            print('Updated form data on contract with tx: ', tx[0]['txHash'])
        except Exception as e:
            print('Exception trying to update form status on Contract ', form_action_params, e)
            return {}, 400
        else:
            return_struct = {
                'txHash': tx[0]['txHash'],
                'contractAddress': settings['MAIN_CONTRACT'],
                'methodName': 'approveForm' if api.payload['action'] == 'approve' else 'rejectForm'
            }
            return return_struct, 201


@ns_form_operations.route('/<string:uuid>/pass')
class FormToPassResource(Resource):
    @login_required
    def get(self, uuid):
        passes = list()
        hashed_uuid = eth_utils.add_0x_prefix(eth_utils.keccak(text=uuid).hex())
        generated_passes = get_generated_passes_eventlogs_by_form(hashed_uuid, main_contract_instance)
        p_hashes = list(map(lambda x: x[0]['passDataHash'], generated_passes))
        status_map = dict()
        # asynchronously also fetch pass information
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_rpcresult = dict()
            for p_data_hash in p_hashes:
                curried_fn = partial(main_contract_instance.passInformation, p_data_hash)
                fut = executor.submit(curried_fn)
                future_to_rpcresult[fut] = p_data_hash
            for future in as_completed(future_to_rpcresult):
                p_data_hash = future_to_rpcresult[future]
                try:
                    pass_data_contract = future.result()
                except Exception as exc:
                    # do something in future
                    print("Error fetching pass Hash {}: {}".format(p_data_hash, exc))
                    status_map[p_data_hash] = False
                else:
                    status_map[p_data_hash] = pass_data_contract['status']
        for e in generated_passes:
            each_map = dict()
            pass_hash = e[0]['passDataHash']
            form_uuid_hash = e[0]['formUUIDHash']
            ethAddress = e[0]['ethAddress']
            # pull pass data
            _pass_data = redis_master.get(REDIS_ADABDHA_USER_FORM_PASS_DATA.format(form_uuid_hash, ethAddress))
            if not _pass_data:
                print(f'Could not find pass data in local cache for form UUID hash {form_uuid_hash}')
                continue
            redis_pass_data = json.loads(_pass_data)
            each_map['passDataHash'] = pass_hash
            each_map['passData'] = redis_pass_data
            each_map['formUUIDHash'] = form_uuid_hash
            each_map['timestamp'] = e[1]
            each_map['status'] = status_map[pass_hash]
            passes.append(each_map)
        return passes, 200

def get_generated_passes_eventlogs_by_ethAddress(track_address, evcore_obj: EVCore):
    api_key = evcore_obj._api_write_key
    contract_address = settings['MAIN_CONTRACT']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{evc._settings["REST_API_ENDPOINT"]}/cachedeventdata'
    method_args = {
        'contract': contract_address,
        'event_name': 'PassGenerated',
        'indexed_param_name': 'ethAddress',
        'indexed_param_value': track_address
    }
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    print(r.text)
    r = r.json()
    data = r['data']
    passes = list()
    for cache_entry_with_ts in data:
        event_data = json.loads(cache_entry_with_ts[0])
        passes.append((event_data, int(cache_entry_with_ts[1])))
    return passes


def get_generated_passes_eventlogs_by_form(track_formUUIDHash, evcore_obj: EVCore):
    api_key = evcore_obj._api_write_key
    contract_address = settings['MAIN_CONTRACT']
    headers = {'accept': 'application/json', 'Content-Type': 'application/json', 'X-API-KEY': api_key}
    method_api_endpoint = f'{evc._settings["REST_API_ENDPOINT"]}/cachedeventdata'
    method_args = {
        'contract': contract_address,
        'event_name': 'PassGenerated',
        'indexed_param_name': 'formUUIDHash',
        'indexed_param_value': track_formUUIDHash
    }
    r = requests.post(url=method_api_endpoint, json=method_args, headers=headers)
    print(r.text)
    r = r.json()
    data = r['data']
    passes = list()
    for cache_entry_with_ts in data:
        event_data = json.loads(cache_entry_with_ts[0])
        passes.append((event_data, int(cache_entry_with_ts[1])))
    return passes

@ns_indiv_user.route('/<string:ethAddress>/passes')
class UserPassesResource(Resource):
    # @ns_indiv_user.marshal_list_with(user_passes_return, code=200)
    @login_required
    @only_allowed_user_or_admin
    def get(self, ethAddress):
        ethAddress = eth_utils.to_normalized_address(ethAddress)
        passes_event_data = get_generated_passes_eventlogs_by_ethAddress(ethAddress, main_contract_instance)
        return_list = list()
        p_hashes = list(map(lambda x: x[0]['passDataHash'], passes_event_data))
        status_map = dict()
        # asynchronously also fetch pass information
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_rpcresult = dict()
            for p_data_hash in p_hashes:
                curried_fn = partial(main_contract_instance.passInformation, p_data_hash)
                fut = executor.submit(curried_fn)
                future_to_rpcresult[fut] = p_data_hash
            for future in as_completed(future_to_rpcresult):
                p_data_hash = future_to_rpcresult[future]
                try:
                    pass_data_contract = future.result()
                except Exception as exc:
                    # do something in future
                    print("Error fetching pass Hash {}: {}".format(p_data_hash, exc))
                    status_map[p_data_hash] = False
                else:
                    status_map[p_data_hash] = pass_data_contract['status']
        for e in passes_event_data:
            each_map = dict()
            pass_hash = e[0]['passDataHash']
            form_uuid_hash = e[0]['formUUIDHash']
            # pull pass data
            _pass_data = redis_master.get(REDIS_ADABDHA_USER_FORM_PASS_DATA.format(form_uuid_hash, ethAddress))
            if not _pass_data:
                print(f'Could not find pass data in local cache for form UUID hash {form_uuid_hash}')
                continue
            redis_pass_data = json.loads(_pass_data)
            each_map['passDataHash'] = pass_hash
            each_map['passData'] = redis_pass_data
            each_map['formUUIDHash'] = form_uuid_hash
            each_map['timestamp'] = e[1]
            each_map['status'] = status_map[pass_hash]
            return_list.append(each_map)
        return return_list, 200


@ns_user_pass.route('/<string:passDataHash>')
class IndividualPassResource(Resource):
    @login_required
    @only_allowed_user_or_admin
    @ns_user_pass.expect(pass_modify_parser)
    @ns_user_pass.marshal_with(updateops_return, code=201)
    def post(self, passDataHash):
        parsed_args = pass_modify_parser.parse_args()
        if parsed_args['action'] == 'revoke':
            tx = main_contract_instance.revokePass(passDataHash=passDataHash)
            print(f'Sent out tx {tx[0]["txHash"]} to revoke pass {passDataHash}')
            return {
                'txHash': tx[0]["txHash"],
                'contractAddress': settings['MAIN_CONTRACT'],
                'methodName': 'revokePass'
            }, 201
        return {}, 400


@ns_passes.route('/')
class PassesResource(Resource):
    @login_required
    @only_allowed_user_or_admin
    def get(self):
        passes = list()
        p = redis_master.hgetall(REDIS_ADABDHA_ALL_PASSES)
        p_hashes = dict()
        for k, v in p.items():
            pass_data_hash = k.decode('utf-8')
            pass_data_json = json.loads(v)
            p_hashes[pass_data_hash] = pass_data_json

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_rpcresult = dict()
            for p_data_hash in p_hashes:
                curried_fn = partial(main_contract_instance.passInformation, p_data_hash)
                fut = executor.submit(curried_fn)
                future_to_rpcresult[fut] = p_data_hash
            for future in as_completed(future_to_rpcresult):
                p_data_hash = future_to_rpcresult[future]
                try:
                    pass_data_contract = future.result()
                except Exception as exc:
                    # do something in future
                    print("Error fetching pass Hash {}: {}".format(p_data_hash, exc))
                    continue
                else:
                    form_uuid_hash = pass_data_contract['formUUIDHash']
                    print(f'Extracted form UUID hash {form_uuid_hash} for pass hash {p_data_hash}')
                    single_map_obj = {
                        'passData': p_hashes[p_data_hash],
                        'passDataHash': p_data_hash,
                        'formUUIDHash': form_uuid_hash,
                        'timestamp': pass_data_contract['createdTimestamp'],
                        'status': pass_data_contract['status']
                    }
                    passes.append(single_map_obj)
        return passes, 200
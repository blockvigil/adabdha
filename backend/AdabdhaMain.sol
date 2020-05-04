pragma solidity >=0.5.1 <0.7.0;
pragma experimental ABIEncoderV2;

contract Ownable {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }
}

contract AdabdhaMain is Ownable {

    uint256 public lastApplicationId;

    struct UserInformationType {
        bytes32 emailHash;
        bytes32 phoneHash;
        bytes32 passDataHash;
        UserStates status;
    }

    struct FormDataType {
        address ethAddress;
        bytes32 formdataHash;
        FormStates status;
    }

    struct PassDataType {
        address ethAddress;
        bytes32 formUUIDHash;
        uint256 createdTimestamp;
        bool status;
    }

    enum FormStates {
        submitted,
        inReview,
        onHold,
        approved,
        rejected
    }

    enum UserStates {
        unverified,
        OTPverified,
        KYCverified
    }

    mapping(address => bool) public userExists;
    mapping(address=>UserInformationType) public userInformation;

    mapping(bytes32 => FormDataType) private submittedForms;

    address[] public userDataOracles;
    mapping(address => bool) UserDataOraclesStatus;
    mapping(bytes32 => PassDataType) public passInformation;

    event UserStatusUpdated(address ethAddress, UserStates status);
    event NewForm(bytes32 uuidHash, address indexed ethAddress, bytes32 formdataHash);

    event FormApproved(bytes32 uuidHash, address indexed ethAddress);
    event  FormRejected(bytes32 uuidHash, address indexed ethAddress);

    event PassGenerated(bytes32 passDataHash, address ethAddress, bytes32 formUUIDHash);
    event PassRevoked(bytes32 passDataHash, address ethAddress, bytes32 formUUIDHash);

    constructor() public {

    }

    modifier onlyUserDataOracleAllowed() {
        bool found = false;
        for (uint i=0; i<userDataOracles.length; i++) {
            if (userDataOracles[i] == msg.sender && UserDataOraclesStatus[msg.sender] == true) {
                found = true;
                break;
            }
        }
        if (!found && msg.sender != owner)
            revert();
        _;
    }

    modifier onlyNewUser(address ethAddress) {
        if (userExists[ethAddress] || userInformation[ethAddress].status != UserStates.unverified)
            revert();
        _;
    }

    modifier onlyExistingUser(address ethAddress) {
        if (userExists[ethAddress] && (userInformation[ethAddress].status != UserStates.OTPverified || userInformation[ethAddress].status != UserStates.KYCverified))
            revert();
        _;
    }

    function getFormStatus(bytes32 uuidHash) public view returns (int8 status) {
        FormDataType memory fd = submittedForms[uuidHash];
        if (fd.ethAddress == address(0))
            return -1;
        else
            return int8(fd.status);
    }

    function getPass(bytes32 passDataHash)
    public view
    returns (address ethAddress, bytes32 formUUIDHash, uint256 timestamp, bool status) {
        require(passInformation[passDataHash].ethAddress != address(0));  // should not refer to empty mapping
        status = passInformation[passDataHash].status;
        ethAddress = passInformation[passDataHash].ethAddress;
        formUUIDHash = passInformation[passDataHash].formUUIDHash;
        timestamp = passInformation[passDataHash].createdTimestamp;
    }


    function getFormStateIdentifierByCode(int8 statusCode)
    public pure returns(string memory statusIdentifier) {
        require(statusCode <= 4);
        if (statusCode < 0)
            return "notSubmittedOnContract";
        if (statusCode == int8(FormStates.submitted)) return "submitted";
        if (statusCode == int8(FormStates.inReview)) return "inReview";
        if (statusCode == int8(FormStates.onHold)) return "onHold";
        if (statusCode == int8(FormStates.approved)) return "approved";
        if (statusCode == int8(FormStates.rejected)) return "rejected";
    }

    function getFormStatusCodeByIdentifier(string memory statusIdentifier)
    public pure returns(int8 statusCode) {
        bytes32 identifierHash = keccak256(bytes(statusIdentifier));
        if (identifierHash == keccak256("notSubmittedOnContract")) return -1;
        if (identifierHash == keccak256("submitted")) return int8(FormStates.submitted);
        if (identifierHash == keccak256("inReview")) return int8(FormStates.inReview);
        if (identifierHash == keccak256("onHold")) return int8(FormStates.onHold);
        if (identifierHash == keccak256("approved")) return int8(FormStates.approved);
        if (identifierHash == keccak256("rejected")) return int8(FormStates.rejected);
    }

    function addUserRegistrationOracle(address oracle)
    public
    onlyOwner
    {
        userDataOracles.push(oracle);
        UserDataOraclesStatus[oracle] = true;
    }

    function addUserByEmail(address ethAddress, bytes32 emailHash)
    public
    onlyUserDataOracleAllowed
    onlyNewUser(ethAddress)
    {
        userInformation[ethAddress] = UserInformationType(emailHash, "\x00\x00", "\x00\x00", UserStates.OTPverified);
        emit UserStatusUpdated(ethAddress, UserStates.OTPverified);

    }

    function addUserByPhone(address ethAddress, bytes32 phoneHash)
    public
    onlyUserDataOracleAllowed
    onlyNewUser(ethAddress)
    {
        userInformation[ethAddress] = UserInformationType("\x00\x00", phoneHash, "\x00\x00", UserStates.OTPverified);
        emit UserStatusUpdated(ethAddress, UserStates.OTPverified);
    }

    function submitFormData(bytes32 uuidHash, address ethAddress, bytes32 formdataHash)
    public
    onlyUserDataOracleAllowed
    onlyExistingUser(ethAddress) {
        submittedForms[uuidHash] = FormDataType(ethAddress, formdataHash, FormStates.submitted);
        emit NewForm(uuidHash, ethAddress, formdataHash);
    }

    function submitUserKYCVerification(address ethAddress)
    public
    onlyUserDataOracleAllowed
    {
        require(userInformation[ethAddress].status != UserStates.KYCverified && userInformation[ethAddress].status == UserStates.OTPverified);
        userInformation[ethAddress].status = UserStates.KYCverified;
        emit UserStatusUpdated(ethAddress, UserStates.KYCverified);
    }

    function approveForm(bytes32 uuidHash)
    public
    onlyOwner {
        submittedForms[uuidHash].status = FormStates.approved;
        address u_addr = submittedForms[uuidHash].ethAddress;
        emit FormApproved(uuidHash, u_addr);
    }

    function generatePass(address ethAddress, bytes32 formUUIDHash, bytes32 passHash)
    public
    onlyOwner {
        /*
          commenting the followng out because of latency, concurrency issues that might cause
          user state to not be updated on contract yet, while the pass generation request has been sent out
        */
        // require(userInformation[ethAddress].status == UserStates.KYCverified && submittedForms[formUUIDHash].status == FormStates.approved);
        userInformation[ethAddress].passDataHash = passHash;
        passInformation[passHash] = PassDataType(ethAddress, formUUIDHash, block.timestamp, true);
        emit PassGenerated(passHash, ethAddress, formUUIDHash);
    }

    function rejectForm(bytes32 uuidHash)
    public
    onlyOwner {
        submittedForms[uuidHash].status = FormStates.rejected;
        address u_addr = submittedForms[uuidHash].ethAddress;
        emit FormRejected(uuidHash, u_addr);
    }

    function revokeUser(address ethAddress)
    public
    onlyUserDataOracleAllowed
    onlyExistingUser(ethAddress)
    {
        userExists[ethAddress] = false;
        emit UserStatusUpdated(ethAddress, UserStates.unverified);
    }

    function revokePass(bytes32 passDataHash)
    public
    onlyOwner {
        require(passInformation[passDataHash].ethAddress != address(0)); // should not refer to empty mapping
        passInformation[passDataHash].status = false;
        emit PassRevoked(passDataHash, passInformation[passDataHash].ethAddress, passInformation[passDataHash].formUUIDHash);
    }


}
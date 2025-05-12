import json
import hashlib
import logging
from django.conf import settings
from web3 import Web3
from hexbytes import HexBytes
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class BlockchainService:
    """Service for interacting with blockchain for report verification"""
    
    def __init__(self):
        self.w3 = self._initialize_web3()
        self.contract = self._initialize_contract()
        self.last_tx_hash = None
    
    def _initialize_web3(self):
        """Initialize Web3 connection"""
        if settings.BLOCKCHAIN_PROVIDER == 'ganache':
            return Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        elif settings.BLOCKCHAIN_PROVIDER == 'infura':
            return Web3(Web3.HTTPProvider(f"https://{settings.BLOCKCHAIN_NETWORK}.infura.io/v3/{settings.INFURA_PROJECT_ID}"))
        else:
            raise ValueError(f"Unsupported blockchain provider: {settings.BLOCKCHAIN_PROVIDER}")
    
    def _initialize_contract(self):
        """Initialize the smart contract instance"""
        with open(settings.BLOCKCHAIN_CONTRACT_ABI_PATH) as abi_file:
            contract_abi = json.load(abi_file)
        
        return self.w3.eth.contract(
            address=settings.BLOCKCHAIN_CONTRACT_ADDRESS,
            abi=contract_abi
        )
    
    def record_transaction(self, data: str, description: str = "") -> HexBytes:
        """
        Record data on the blockchain
        
        Args:
            data: The data to be stored on-chain
            description: Human-readable description of the transaction
            
        Returns:
            HexBytes: The transaction hash
        """
        try:
            # Generate hash of the data for efficient storage
            data_hash = hashlib.sha256(data.encode()).hexdigest()
            
            # Build transaction
            tx = self.contract.functions.recordData(
                data_hash,
                description
            ).build_transaction({
                'chainId': settings.BLOCKCHAIN_CHAIN_ID,
                'gas': 200000,
                'gasPrice': self.w3.to_wei('50', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(settings.BLOCKCHAIN_WALLET_ADDRESS),
            })
            
            # Sign transaction
            signed_tx = self.w3.eth.account.sign_transaction(
                tx,
                private_key=settings.BLOCKCHAIN_PRIVATE_KEY
            )
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.last_tx_hash = tx_hash.hex()
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Transaction successful with hash: {tx_hash.hex()}")
            return tx_hash
        
        except Exception as e:
            logger.error(f"Failed to record transaction: {str(e)}")
            raise
    
    def verify_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Verify a blockchain transaction
        
        Args:
            tx_hash: The transaction hash to verify
            
        Returns:
            Dict: Verification result containing status and data
        """
        try:
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if not receipt:
                return {
                    'status': 'error',
                    'message': 'Transaction not found'
                }
            
            # Check if transaction was successful
            if receipt.status != 1:
                return {
                    'status': 'error',
                    'message': 'Transaction failed'
                }
            
            # Get transaction details
            tx = self.w3.eth.get_transaction(tx_hash)
            
            # Get block details
            block = self.w3.eth.get_block(receipt.blockNumber)
            
            # Get event logs
            logs = self.contract.events.DataRecorded().process_receipt(receipt)
            
            return {
                'status': 'success',
                'transaction': {
                    'hash': tx_hash,
                    'block_number': receipt.blockNumber,
                    'block_hash': receipt.blockHash.hex(),
                    'timestamp': block.timestamp,
                    'from': tx['from'],
                    'to': tx['to'],
                    'gas_used': receipt.gasUsed,
                    'effective_gas_price': receipt.effectiveGasPrice
                },
                'data': logs[0].args if logs else None
            }
        
        except Exception as e:
            logger.error(f"Failed to verify transaction {tx_hash}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_data(self, data_hash: str) -> Optional[Dict]:
        """
        Retrieve data from the blockchain using its hash
        
        Args:
            data_hash: The SHA-256 hash of the original data
            
        Returns:
            Optional[Dict]: The stored data if found, None otherwise
        """
        try:
            result = self.contract.functions.getData(data_hash).call()
            return result if result else None
        except Exception as e:
            logger.error(f"Failed to get data for hash {data_hash}: {str(e)}")
            return None
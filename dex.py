from web3.middleware import geth_poa_middleware
from web3 import Web3
from time import time 
import logging


class DexTrade :

    def __init__(self,
        endpoint,
        account_keys,
        tokenA_address,
        tokenB_address, 
        factory_contract,
        router_contract,
        pair_abi,
        slippage= 0.01,
        gas_limit= 10165700,
        gsa_price= 120*10**9
        ):

        self.tokenA_address = Web3.toChecksumAddress(tokenA_address)
        self.tokenB_address = Web3.toChecksumAddress(tokenB_address)
        self.account_keys = account_keys
        self.slippage = slippage
        self.endpoint = endpoint
        self.gas_limit = gas_limit
        self.gas_price = gsa_price

        self._hexadem = '0x00fb7f630766e6a796048ea87d01acd3068e8ff67d078148a3fa3f4a84f69bd5' # used for create pair
        
        self.w3 = Web3(Web3.HTTPProvider(endpoint))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        self.pointer_to_factory_contract = self.w3.eth.contract(
            address= Web3.toChecksumAddress( factory_contract['address'] ),
            abi= factory_contract['abi']
        )

        self.pairAddress = self.pointer_to_factory_contract.functions.getPair(self.tokenA_address, self.tokenB_address).call()
        
        self.pointer_to_lp_contract = self.w3.eth.contract(
            address= self.pairAddress,
            abi= pair_abi
        )

        self.pointer_to_router_contract = self.w3.eth.contract(
            address= Web3.toChecksumAddress( router_contract['address'] ),
            abi= router_contract['abi']
        )

    def get_tokenA_price(self):
        
        # tokenA / tokenB

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()
        tokenA_price = tokenB_balance / tokenA_balance 

        return tokenA_price

    def get_tokenB_price(self):

        # tokenB / tokenA

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()
        tokenB_price = tokenA_balance / tokenB_balance 

        return tokenB_price

    def get_deadLine(self):

        return int(time()) + 10 * 60

    def _allowance(self, object_token):
        
        allowance_amount = object_token.functions.allowance(
            self.account_keys.public_key,
            self.pointer_to_router_contract.address
            ).call()

        return allowance_amount

    def _approve(self,object_token ,amount):
        
        logging.info('Approve token[{0}] ]'.format(object_token.address))

        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(Web3.toChecksumAddress(self.account_keys.public_key))
        
        data_field = object_token.functions.approve(self.pointer_to_router_contract.address, amount).buildTransaction({
        'from': self.account_keys.public_key,
        'gasPrice': gas_price,
        'nonce': nonce,
        })

        signed_txn = self.w3.eth.account.sign_transaction(data_field, private_key= self.account_keys.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logging.info('Tx approve hash [{0}]'.format(tx_hash.hex()))
        
        self.w3.eth.wait_for_transaction_receipt(tx_hash.hex())

        return tx_hash.hex()

    def check_approve(self, token_address, amount):

        object_token = self.w3.eth.contract(
            address= token_address,
            abi= self.pointer_to_lp_contract.abi
        )

        if self._allowance(object_token) < amount:
            max_amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
            self._approve(object_token, max_amount)


    def sell_tokenA(self, amount):


        tokenA_amount = Web3.toWei(amount, 'ether')

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()

        tokenB_amount = Web3.toWei(tokenB_balance / tokenA_balance * amount, 'ether')

        tokenB_amount = int((1 - self.slippage) * tokenB_amount) 

        logging.info('Sawp tokenA[{0:3.3f}] -> tokenB[{1:3.3f}]'.format(amount, tokenB_amount/10**18))

        self.check_approve(self.tokenA_address, tokenA_amount)

        return self._make_trade(
            fn_identifier='swapExactTokensForTokens',
            input_token_amount= tokenA_amount,
            output_token_amount= tokenB_amount,
            input_token_address= self.tokenA_address,
            output_token_address= self.tokenB_address
            )

    def sell_tokenB(self, amount):

        tokenB_amount = Web3.toWei(amount, 'ether')

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()
        tokenA_amount = Web3.toWei(tokenA_balance / tokenB_balance * amount, 'ether')
        tokenA_amount = int((1 - self.slippage) * tokenA_amount) 

        logging.info('Sawp tokenB[{0:3.3f}] -> tokenA[{1:3.3f}]'.format(amount, tokenA_amount/10**18) )

        self.check_approve(self.tokenB_address, tokenB_amount)

        return self._make_trade(
            fn_identifier='swapExactTokensForTokens',
            input_token_amount= tokenB_amount,
            output_token_amount= tokenA_amount,
            input_token_address= self.tokenB_address,
            output_token_address= self.tokenA_address
            )

    def buy_tokenA(self, amount):

        tokenA_amount = Web3.toWei(amount, 'ether')

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()
        tokenB_amount = Web3.toWei(tokenB_balance / tokenA_balance * amount, 'ether')

        tokenB_amount = int((1 + self.slippage) * tokenB_amount) 
        
        logging.info('Sawp tokenB[{0:3.3f}] -> tokenA[{1:3.3f}]'.format(tokenB_amount/10**18, amount) )

        self.check_approve(self.tokenB_address, tokenB_amount)

        return self._make_trade(
            fn_identifier='swapTokensForExactTokens',
            input_token_amount= tokenA_amount,
            output_token_amount= tokenB_amount,
            input_token_address= self.tokenB_address,
            output_token_address= self.tokenA_address
            )

    def buy_tokenB(self, amount):


        tokenB_amount = Web3.toWei(amount, 'ether')

        [tokenA_balance ,tokenB_balance ,_] = self.pointer_to_lp_contract.functions.getReserves().call()
        tokenA_amount = Web3.toWei(tokenA_balance / tokenB_balance * amount, 'ether')

        tokenA_amount = int((1 + self.slippage) * tokenA_amount) 

        logging.info('Sawp tokenA[{0:3.3f}] -> tokenB[{1:3.3f}]'.format(tokenA_amount/10**18 ,amount) )

        self.check_approve(self.tokenA_address, tokenA_amount)

        return self._make_trade(
            fn_identifier='swapTokensForExactTokens',
            input_token_amount= tokenB_amount,
            output_token_amount= tokenA_amount,
            input_token_address= self.tokenA_address,
            output_token_address= self.tokenB_address
            )

    def _make_trade(
        self,
        fn_identifier,
        input_token_amount,
        output_token_amount,
        input_token_address, 
        output_token_address
        ):
            
        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(Web3.toChecksumAddress(self.account_keys.public_key))
        
        data_field = getattr(self.pointer_to_router_contract.functions, fn_identifier)(
                input_token_amount,
                output_token_amount, 
                [input_token_address,output_token_address],
                Web3.toChecksumAddress(self.account_keys.public_key),
                self.get_deadLine()
            ).buildTransaction({
                'from': Web3.toChecksumAddress(self.account_keys.public_key),
                'gasPrice': gas_price,
                'nonce': nonce,
            })

        signed_txn = self.w3.eth.account.sign_transaction(data_field, private_key=self.account_keys.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        logging.info('Tx hash [{0}]'.format(tx_hash.hex()))

        return tx_hash.hex()




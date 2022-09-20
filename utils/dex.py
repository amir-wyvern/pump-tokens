from web3.middleware import geth_poa_middleware
from time import time 
import logging
from web3 import Web3

class DexTrade :

    def __init__(self,
        provider,
        account_keys,
        token0_address,
        token1_address, 
        factory_contract,
        router_contract,
        erc20_abi,
        slippage= 0.01,
        gas_limit= 10165700,
        ):


        self.account_keys = account_keys
        self.slippage = slippage
        self.gas_limit = gas_limit
        self._hexadem = '0x00fb7f630766e6a796048ea87d01acd3068e8ff67d078148a3fa3f4a84f69bd5' # used for create pair
        self.WBNB = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

        self.w3 = Web3(Web3.HTTPProvider(provider))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
        self.token0 = self.w3.eth.contract(
            address= Web3.toChecksumAddress(token0_address),
            abi= erc20_abi
        )
        self.token1 = self.w3.eth.contract(
            address= Web3.toChecksumAddress(token1_address),
            abi= erc20_abi
        )
        
        setattr(self.token0, "decimal", self.token0.functions.decimals().call())
        setattr(self.token1, "decimal", self.token1.functions.decimals().call())
        setattr(self.token0, "symbol", self.token0.functions.symbol().call())
        setattr(self.token1, "symbol", self.token1.functions.symbol().call())

        self.pointer_to_factory_contract = self.w3.eth.contract(
            address= Web3.toChecksumAddress( factory_contract['address'] ),
            abi= factory_contract['abi']
        )

        self.pointer_to_router_contract = self.w3.eth.contract(
            address= Web3.toChecksumAddress( router_contract['address'] ),
            abi= router_contract['abi']
        )

    def get_deadLine(self):

        return int(time()) + (10 * 60)

    def get_route(self, tokenA, tokenB):

        route = [tokenA, tokenB]
        if self.WBNB not in route:
            route = [tokenA, self.WBNB, tokenB]

        return route

    def _allowance(self, token):
        
        allowance_amount = token.functions.allowance(
            self.account_keys.public_key,
            self.pointer_to_router_contract.address
            ).call()

        return allowance_amount

    def _approve(self,token ,amount):
        
        logging.info('Approving...  token[{0}-{1}] ]'.format(token.symbol, token.address))

        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(Web3.toChecksumAddress(self.account_keys.public_key))
        
        data_field = token.functions.approve(self.pointer_to_router_contract.address, amount).buildTransaction({
            'from': self.account_keys.public_key,
            'gasPrice': gas_price,
            'nonce': nonce,
        })

        signed_txn = self.w3.eth.account.sign_transaction(data_field, private_key= self.account_keys.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        
        self.w3.eth.wait_for_transaction_receipt(tx_hash.hex())
        logging.info('Tx approve hash [{0}]'.format(tx_hash.hex()))

        return tx_hash.hex()

    def check_approve(self, token, amount):

        if self._allowance(token) < amount:
            max_amount = 115792089237316195423570985008687907853269984665640564039457584007913129639935
            self._approve(token, max_amount)

    def get_swap_type(self, token0, token1, swapType):

        if self.WBNB == token0:
            return swapType.format('ETH', 'Tokens')

        elif self.WBNB == token1:
            return swapType.format('Tokens', 'ETH')

        else :
            return swapType.format('Tokens', 'Tokens')

    def get_token0_price_for_buy(self):

        return self.pointer_to_router_contract.functions.getAmountsIn(
            10**self.token1.decimal,
            self.get_route(self.token1.address ,self.token0.address)
        ).call()[0] / 10**self.token0.decimal

    def get_token0_price_for_sell(self):

        return self.pointer_to_router_contract.functions.getAmountsOut(
            10**self.token1.decimal,
            self.get_route(self.token0.address ,self.token1.address)
        ).call()[-1] / 10**self.token0.decimal

    def get_token1_price_for_buy(self):

        return self.pointer_to_router_contract.functions.getAmountsIn(
            10**self.token0.decimal,
            self.get_route(self.token0.address ,self.token1.address)
        ).call()[0] / 10**self.token1.decimal

    def get_token1_price_for_sell(self):

        return self.pointer_to_router_contract.functions.getAmountsOut(
            10**self.token1.decimal,
            self.get_route(self.token1.address ,self.token0.address)
        ).call()[-1] / 10**self.token0.decimal

    def buy_token0(self, amount):

        token1_amount = self.pointer_to_router_contract.functions.getAmountsIn(
            int(amount*10**self.token0.decimal),
            self.get_route(self.token1.address ,self.token0.address) ).call()[0]

        token1_amount = int((1 + self.slippage) * token1_amount) 

        swapType = 'swap{0}ForExact{1}'
        swapType = self.get_swap_type(self.token1.address, self.token0.address, swapType)
        
        self.check_approve(self.token1, token1_amount)

        logging.info('Sawping...  token1[{0}|{1}] -> token0[{2}|{3}]'.format(
            self.token1.symbol,
            round(float(token1_amount)/10**self.token1.decimal, 5),
            self.token0.symbol,
            round(float(amount),5),
            )
        )

        route= self.get_route(self.token1.address ,self.token0.address)
        dict_args = {}
        if swapType == 'swapETHForExactTokens':
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token0.decimal),
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )
            
            dict_args['value'] = token1_amount

        else:
            
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token0.decimal), 
                    token1_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )

        return self._make_trade(
            fn_identifier= obj,
            dict_args= dict_args
            )

    def buy_token1(self, amount):

        token0_amount = self.pointer_to_router_contract.functions.getAmountsIn(
            int(amount*10**self.token1.decimal),
            self.get_route(self.token0.address ,self.token1.address) ).call()[0]

        token0_amount = int((1 + self.slippage) * token0_amount) 

        swapType = 'swap{0}ForExact{1}'
        swapType = self.get_swap_type(self.token0.address, self.token1.address, swapType)
        
        self.check_approve(self.token0, token0_amount)

        logging.info('Sawping...  token0[{0}|{1}] -> token1[{2}|{3}]'.format(
            self.token0.symbol,
            round(float(token0_amount)/10**self.token0.decimal, 5),
            self.token1.symbol,
            round(float(amount),5),
            )
        )

        route= self.get_route(self.token0.address ,self.token1.address)
        dict_args = {}
        if swapType == 'swapETHForExactTokens':
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token1.decimal),
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )
            
            dict_args['value'] = token0_amount

        else:
            
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token1.decimal), 
                    token0_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )

        return self._make_trade(
            fn_identifier= obj,
            dict_args= dict_args
            )

    def sell_token0(self, amount):

        token1_amount = self.pointer_to_router_contract.functions.getAmountsOut(
            int(amount*10**self.token0.decimal),
            self.get_route(self.token0.address ,self.token1.address) ).call()[-1]

        token1_amount = int((1 - self.slippage) * token1_amount) 

        swapType = 'swapExact{0}For{1}'
        swapType = self.get_swap_type(self.token0.address, self.token1.address, swapType)
        
        self.check_approve(self.token0, int(amount*10**self.token0.decimal))

        logging.info('Sawping...  token0[{0}|{1}] -> token1[{2}|{3}]'.format(
            self.token0.symbol,
            round(float(amount),5),
            self.token1.symbol,
            round(float(token1_amount)/10**self.token1.decimal, 5),
            )
        )

        route = self.get_route(self.token0.address ,self.token1.address)
        dict_args = {}

        if swapType == 'swapExactETHForTokens':
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    token1_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )
            
            dict_args['value'] = int(amount * 10 ** self.token0.decimal)

        else:
            
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token0.decimal), 
                    token1_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )

        return self._make_trade(
            fn_identifier= obj,
            dict_args= dict_args
            )

    def sell_token1(self, amount):

        token0_amount = self.pointer_to_router_contract.functions.getAmountsOut(
            int(amount*10**self.token1.decimal),
            self.get_route(self.token1.address, self.token0.address) ).call()[-1]

        token0_amount = int((1 - self.slippage) * token0_amount) 

        swapType = 'swapExact{0}For{1}'
        swapType = self.get_swap_type(self.token1.address, self.token0.address, swapType)
        
        self.check_approve(self.token1, int(amount*10**self.token1.decimal))

        logging.info('Sawping...  token1[{0}|{1}] -> token0[{2}|{3}]'.format(
            self.token1.symbol,
            round(float(amount),5),
            self.token0.symbol,
            round(float(token0_amount)/10**self.token0.decimal, 5),
            )
        )

        route = self.get_route(self.token1.address ,self.token0.address)

        dict_args = {}
        if swapType == 'swapExactETHForTokens':
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    token0_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )
            
            dict_args['value'] = int(amount * 10 ** self.token1.decimal)

        else:
            
            obj = getattr(self.pointer_to_router_contract.functions, swapType)(
                    int(amount * 10 ** self.token1.decimal), 
                    token0_amount,
                    route,
                    Web3.toChecksumAddress(self.account_keys.public_key),
                    self.get_deadLine()
                )

        return self._make_trade(
            fn_identifier= obj,
            dict_args= dict_args
            )

    def _make_trade(
        self,
        fn_identifier,
        dict_args
        ):
            
        dict_args["from"] = Web3.toChecksumAddress(self.account_keys.public_key)
        dict_args["gasPrice"] = self.w3.eth.gas_price
        dict_args["nonce"] = self.w3.eth.get_transaction_count(Web3.toChecksumAddress(self.account_keys.public_key))

        data_field = fn_identifier.buildTransaction(dict_args)

        signed_txn = self.w3.eth.account.sign_transaction(data_field, private_key=self.account_keys.private_key)

        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        logging.info('Tx hash [{0}]'.format(tx_hash.hex()))

        return tx_hash.hex()




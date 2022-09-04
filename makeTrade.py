
from utils.blockchainAccountBalance import BlockchainBalance
from utils.contracts import load_contracs
from utils.account import Account

from dotenv import load_dotenv

from dex import DexTrade

import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)-24s] [%(levelname)-8s] [%(lineno)-3d -%(name)-7s] | %(message)s',
    handlers=[
    logging.FileHandler("trade.log"),
    logging.StreamHandler()
    ]
)

if __name__ == '__main__':

    # tokenA_address  = '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82'  # name : cake
    # tokenA_address = '0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c' # name btcB
    # tokenA_address = '0x42F6f551ae042cBe50C739158b4f0CAC0Edb9096' # nrv
    tokenA_address = '0x4bd17003473389a42daf6a0a729f6fdb328bbbd7' # vai
    tokenB_address = '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56' # name : busd

    load_dotenv()
    password = os.getenv('PASSWORD').encode()
    
    account_keys = Account(password)

    list_contracts = load_contracs()

    blockchain_balance = BlockchainBalance(account_keys)

    dex = DexTrade(
        endpoint= 'https://bsc-dataseed.binance.org',
        account_keys= account_keys,
        tokenA_address= tokenA_address,
        tokenB_address= tokenB_address,
        factory_contract= list_contracts['pancake-factory'],
        router_contract= list_contracts['router'],
        pair_abi= list_contracts['pancake-pair']['abi']
        )
    
    print(dex.sell_tokenA(2))


# bot : 0x095ea7b300000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e000000000000000000000000000000000de0b6b3a763fffff21f494c589c0000
#  ex : 0x095ea7b300000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff


# bot : 0x095ea7b300000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff



0x095ea7b300000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024effffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
0x095ea7b3000000000000000000000000f45cd219aef8618a92baa7ad848364a158a24f33000000000000000000000000000000000de0b6b3a763fffff21f494c589c0000
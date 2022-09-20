
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

import uniswap
if __name__ == '__main__':

    token0_address = '' 
    token1_address = ''

    load_dotenv()
    password = os.getenv('PASSWORD').encode()
    
    account_keys = Account(password)

    list_contracts = load_contracs()

    dex = DexTrade(
        provider= 'https://bsc-dataseed.binance.org',
        account_keys= account_keys,
        token0_address= token0_address,
        token1_address= token1_address,
        factory_contract= list_contracts['pancake-factory'],
        router_contract= list_contracts['router'],
        erc20_abi= list_contracts['erc20']['abi'],
        slippage= 0.01)


    # print(dex.get_token0_price_for_buy() )
    # print(dex.get_token0_price_for_sell() )
    # print(dex.get_token1_price_for_buy() )
    # print(dex.get_token1_price_for_sell() )

    # print(dex.buy_token0(amount=1))
    # print(dex.buy_token1(amount=1))
    # print(dex.sell_token0(amount=1))
    # print(dex.sell_token1(amount=1))



from utils.contracts import load_contracs
from utils.account import Account
from utils.dex import DexTrade
from dotenv import load_dotenv
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)-24s] [%(levelname)-8s] [%(lineno)-3d -%(name)-7s] | %(message)s',
    handlers=[
    logging.FileHandler("dexTrade.log"),
    logging.StreamHandler()
    ]
)


if __name__ == '__main__':

    tokenB_address = '' # busd
    tokenA_address = '' # wbnb
    amount = 0

    load_dotenv()

    password = os.getenv('PASSWORD').encode()
    account_keys = Account(password)

    list_contracts = load_contracs()

    dex = DexTrade(
        endpoint= 'https://bsc-dataseed.binance.org',
        account_keys= account_keys,
        tokenA_address= tokenA_address,
        tokenB_address= tokenB_address,
        factory_contract= list_contracts['pancake-factory'],
        router_contract= list_contracts['router'],
        pair_abi= list_contracts['pancake-pair']['abi'],
        slippage=49
        )

    # dex.check_approve(token_address, amount)

    # dex.get_tokenA_price()
    # dex.get_tokenB_price()

    # dex.buy_tokenA(amount)
    # dex.buy_tokenB(amount)
    # dex.sell_tokenA(amount)
    # dex.sell_tokenB(amount)    

from concurrent.futures import ThreadPoolExecutor
from web3.middleware import geth_poa_middleware
from web3 import Web3

TOPICS = {
    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' # Transfer
}

FUNC_HASH = [
    '0x7ff36ab5',#swapExactETHForTokens
    '0x38ed1739',#swapExactTokensForTokens
    '0x8803dbee',#swapTokensForExactTokens
    '0x4a25d94a',#swapTokensForExactETH
    '0x18cbafe5',#swapExactTokensForETH
    '0xfb3bdb41',#swapETHForExactTokens
    '0x5c11d795',#swapExactTokensForTokensSupportingFeeOnTransferTokens
    '0xb6f9de95',#swapExactETHForTokensSupportingFeeOnTransferTokens
    '0x791ac947' #swapExactTokensForETHSupportingFeeOnTransferTokens
]

CONTRACT_CACHE = set()

w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org") )
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

class ScrapeNetwork :

    def __init__(self, firstBlock, lastBlock, worker):

        self.firstBlock = firstBlock
        self.lastBlock = lastBlock
        self.executor = ThreadPoolExecutor(max_workers= worker)

    def start(self):

        blockTxs = self.executor.map(self.getBlocks, range(self.firstBlock, self.lastBlock + 1))
        for blockTx in blockTxs:
            self.findCreateMethodInTx(blockTx['transactions'])

    def getBlocks(self ,blockNumber):
        
        blockTxs = w3.eth.get_block(blockNumber, full_transactions= True)
        return blockTxs

    def tokenizeArgs(self, data):

        data = data[10:]
        address_found = set()
        for arg_index in range(len(data)//64):
            arg = hex(int(data[arg_index*64:(arg_index+1)*64], 16))
            if len(arg) == 42:
                address_found.add(arg)
            
        return address_found
            
    def findCreateMethodInTx(self, txs):

        for tx in txs:

            if tx['input'].startswith('0xf305d719') and ( tokenAddress := hex(int(tx['input'][10:74], 16)) ) in CONTRACT_CACHE:

                print('>find a token : {0} | value : {1:.5}'.format(tokenAddress, tx['value']/10**18 ) )

            if tx['input'][:10] in FUNC_HASH and (address_list := self.tokenizeArgs(tx['input']) & CONTRACT_CACHE )  : 

                for _ in range(len(address_list)):
                    address = address_list.pop()
                
            if tx['input'].startswith('0x60806040')  :

                txData = w3.eth.get_transaction_receipt(tx['hash'].hex())
                topicLogs = set([log['topics'][0].hex() for log in txData['logs']])

                if topicLogs and not(TOPICS - topicLogs):

                    CONTRACT_CACHE.add(txData['contractAddress'].lower())


ScrapeNetwork(20987200, 20989210 ,15).start()




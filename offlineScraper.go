package main

import (
    "context"
    "fmt"
    "log"
    "math/big"
    "sync"
    "time"
    "bytes"
    "os"
	"encoding/json"
	"io/ioutil"
    "github.com/thedevsaddam/iter"
	"github.com/ethereum/go-ethereum/common"
    "github.com/ethereum/go-ethereum/ethclient"
    "github.com/ethereum/go-ethereum/core/types"
	"github.com/ethereum/go-ethereum/accounts/abi"

)

// var TOPICS [] 
var CACHE = map[common.Address]bool {}
var CLIENT, _ = ethclient.Dial("https://bsc-dataseed.binance.org")


var CREATE = map[[4]byte]interface{} {
    [4]byte{0x60, 0x80, 0x60, 0x40} : func (_ *big.Int, _ map[string]interface{})(*big.Int,string){return big.NewInt(0), ""},
}
var ADD_LIQ = map[[4]byte]interface{} {
	[4]byte{0xf3, 0x05, 0xd7, 0x19} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, ""} ,
}
var SWAP = map[[4]byte]interface{} {
	[4]byte{0x7f, 0xf3, 0x6a, 0xb5} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, "buy"} ,
	[4]byte{0xfb, 0x3b, 0xdb, 0x41} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, "buy"} ,
	[4]byte{0xb6, 0xf9, 0xde, 0x95} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, "buy"} ,
	[4]byte{0x4a, 0x25, 0xd9, 0x4a} : func(_ *big.Int, inputABI map[string]interface{})(*big.Int,string){return inputABI["amountOut"].(*big.Int), "sell"},
	[4]byte{0x18, 0xcb, 0xaf, 0xe5} : func(_ *big.Int, inputABI map[string]interface{})(*big.Int,string){return inputABI["amountOutMin"].(*big.Int), "sell"} ,
	[4]byte{0x79, 0x1a, 0xc9, 0x47} : func(_ *big.Int, inputABI map[string]interface{})(*big.Int,string){return inputABI["amountOutMin"].(*big.Int), "sell"} ,
}
var REMOVE_LIQ = map[[4]byte]interface{} {
	[4]byte{0x02, 0x75, 0x1c, 0xec} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, ""} ,
	[4]byte{0xaf, 0x29, 0x79, 0xeb} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, ""} ,
	[4]byte{0xde, 0xd9, 0x38, 0x2a} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, ""} ,
	[4]byte{0x5b, 0x0d, 0x59, 0x84} : func(value *big.Int, _ map[string]interface{})(*big.Int,string){return value, ""} ,
}


var CONTRACT_ABI = GetContractABI()
func GetContractABI() *abi.ABI {

	jsonFile, err := os.Open("contract-router-pancake.json")

	if err != nil {
        fmt.Println(err)
    }
    defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	
	var RawABI map[string]interface{}
    json.Unmarshal([]byte(byteValue), &RawABI)

	byteABI ,_:= json.Marshal(RawABI["abi"])
	
	reader := bytes.NewReader(byteABI)
	buf := make([]byte, len(byteABI))
	_, err2 := reader.Read(buf)
	if err2 != nil {
	  log.Fatal(err2)
	}
	
	contractABI, err := abi.JSON(bytes.NewReader(buf))
	if err != nil {
		log.Fatal(err)
	}

	return &contractABI
}

func DecodeTransactionInputData(contractABI *abi.ABI, data []byte) map[string]interface{} {
	
    methodSigData := data[:4]
	inputsSigData := data[4:]
	method, err := contractABI.MethodById(methodSigData)
	if err != nil {
		log.Fatal(err)
	}
	inputsMap := make(map[string]interface{})
	if err := method.Inputs.UnpackIntoMap(inputsMap, inputsSigData); err != nil {
		log.Fatal(err)
	} 
	return inputsMap
}

func isContainCacheAddress(listAddress []common.Address) bool {
    for _, address := range listAddress {
        if CACHE[address] {
            return true
        }
    }
    return false
}

func analyzeTx(tx *types.Transaction) {

    key4Byte := [4]byte{tx.Data()[0], tx.Data()[1], tx.Data()[2], tx.Data()[3]} 

    if CREATE[key4Byte] != nil {

        inputABI := make(map[string]interface{})
        value, _ := CREATE[key4Byte].(func(*big.Int,map[string]interface{})(*big.Int,string))(tx.Value(), inputABI) 
        from, _ := types.Sender(types.NewEIP155Signer(tx.ChainId()), tx) 
        receipt, _ := CLIENT.TransactionReceipt(context.Background(), tx.Hash())
        CACHE[receipt.ContractAddress] = true

        fmt.Println("=CRAETE : " ,receipt.ContractAddress , tx.Hash().Hex(),from ,value)
        fmt.Println("=CRAETE : " ,receipt.Logs)
        fmt.Printf("=CRAETE : %T" ,receipt.Logs)
        // fmt.Printf("%T\n" , tx.From())

    } else if ADD_LIQ[key4Byte] != nil {
        
        inputABI := DecodeTransactionInputData(CONTRACT_ABI, tx.Data())
        if CACHE[inputABI["token"].(common.Address)] {
            value, _ := ADD_LIQ[key4Byte].(func(*big.Int,map[string]interface{})(*big.Int,string))(tx.Value(), inputABI) 
            fmt.Println("ADD_LIQ : " , inputABI ,value)
            fmt.Printf("ADD %T" ,inputABI["token"] )
        }
    } else if SWAP[key4Byte] != nil {

        inputABI := DecodeTransactionInputData(CONTRACT_ABI, tx.Data()) 
        if isContainCacheAddress(inputABI["path"].([]common.Address) ) {
            SWAP[key4Byte].(func(*big.Int,map[string]interface{})(*big.Int,string))(tx.Value(), inputABI) 
        }

    } else if REMOVE_LIQ[key4Byte] != nil {
        
        inputABI := DecodeTransactionInputData(CONTRACT_ABI, tx.Data())
        if CACHE[inputABI["token"].(common.Address)] {
            value, _ := REMOVE_LIQ[key4Byte].(func(*big.Int,map[string]interface{})(*big.Int,string))(tx.Value(), inputABI) 
            fmt.Println("REMOVE_LIQ : " , value)
        }
    }

}

func getBlockNumber(number int) {

    fmt.Printf("> %d \n", number)

    blockNumber := big.NewInt(int64(number))
    block, err := CLIENT.BlockByNumber(context.Background(), blockNumber)

    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf( "<%d \n" ,block.Number().Uint64())

    for _, tx := range block.Transactions() {
        if (len(tx.Data()) >= 4) {
            analyzeTx(tx)
        }
    }
}

func spinupWorker(count int, pipeline <-chan int, wg *sync.WaitGroup) {

    for i := 0; i < count; i++ {
        wg.Add(1)
        go func (workerId int) {
            for blockNumber := range pipeline {
                getBlockNumber(blockNumber)
            }
            wg.Done()
        }(i)
    }
}


func main() {

    start := time.Now()
    
    wg := &sync.WaitGroup{}
    pipeline := make(chan int)

    spinupWorker(1, pipeline, wg)
    
    for i := range iter.N(21061418,21071407) {
        pipeline <- i
    }

    close(pipeline)
    wg.Wait()
    elapsed := time.Since(start)
    fmt.Printf("Binomial took %s", elapsed)

}
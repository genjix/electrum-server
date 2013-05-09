from processor import Processor

class BlockchainProcessor(Processor):

    def __init__(self, config, shared):
        Processor.__init__(self)

    def process(self, request):
        self.push_response({
            "id": request["id"],
            "result": 110
        })
        self.push_response({
            "method": "blockchain.numblocks.subscribe",
            "id": None,
            "params": [111]
        })


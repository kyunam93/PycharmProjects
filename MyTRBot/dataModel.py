class DataModel:
    def __init__(self):
        self.itemList = []
        self.stockBalanceList = []
        self.outstandingBalanceList = []

    class ItemInfo:
        def __init__(self, itemCode, itemName):
            self.itemCode = itemCode
            self.itemName = itemName

    class StockBalance:
        def __init__(self, itemCode, itemName, amount, buyingPrice, currentPrice, estmateProfit, profitRate):
            self.itemCode = itemCode
            self.itemName = itemName
            self.amount = amount
            self.buyingPrice = buyingPrice
            self.currentPrice = currentPrice
            self.estmateProfit = estmateProfit
            self.profitRate = profitRate

    class OutstandingBalance:
        def __init__(self, itemCode, itemName, orderNumber, orderVolume, orderPrice, outStandingVolume, tradeGubun,
                     orderTime, currentPrice):
            self.itemCode = itemCode
            self.itemName = itemName
            self.orderNumber = orderNumber
            self.orderVolume = orderVolume
            self.orderPrice = orderPrice
            self.outStandingVolume = outStandingVolume
            self.tradeGubun = tradeGubun
            self.orderTime = orderTime
            self.currentPrice = currentPrice

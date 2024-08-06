class DataModel:
    def __init__(self):
        self.itemList = []
        self.stockBalanceList = []
        self.outstandingBalanceList = []
        self.autoTradeConditionList = []
        self.conditionItemList = {}
        # self.conditionItemList["조건명"] = [종목정보]

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

    class AutoTradeConditionInfo:

        def __init__(self, startTime, endTime, code, name, autoTradeGubun):
            self.startTime = startTime
            self.endTime = endTime
            self.code = code
            self.name = name
            self.autoTradeGubun = autoTradeGubun

    class ConditionItemInfo:

        def __init__(self, itemCode, itemName, currentPrice, fluctuationRate, priceDiffYes, openPrice, highPrice, lowPrice, buyStatus, sellStatus, sRQName):
            # 전일가 대비 차이, sRQName : 화면이름- 가장 주요
            self.itemCode = itemCode
            self.itemName = itemName
            self.currentPrice = currentPrice
            self.fluctuationRate = fluctuationRate
            self.priceDiffYes = priceDiffYes
            self.openPrice = openPrice
            self.highPrice = highPrice
            self.lowPrice = lowPrice
            self.buyStatus = buyStatus
            self.sellStatus = sellStatus
            self.sRQName = sRQName

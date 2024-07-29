import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QAxContainer import *

import dataModel as dm


form_class = uic.loadUiType('main_window.ui')[0]




class MyBot1(QMainWindow, form_class):


    #생성자
    def __init__(self):
        super().__init__()
        self.setUI()
        self.myModel = dm.DataModel()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login()

        #kiwoom event
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trData)

        # Ui_Trigger
        self.searchItemButton.clicked.connect(self.searchItem)
        self.buyPushButton.clicked.connect(self.itemBuy)
        self.sellPushButton.clicked.connect(self.itemBuy)

    def setUI(self):
        # 반드시 pyqt 실행시 필요한 메소드
        self.setupUi(self)

        column_head = ["00 : 지정가", "03 : 시장가", "05 : 조건부지정가", "06 : 최유리지정가", "07: 최우선지정가",
                       "10 : 지정가IOC", "13 : 시장가IOC", "16 : 최유리IOC", "20 : 지정가FOK", " 23 : 시장가FOK",
                       "26 : 최유리FOK", "61 : 장전시간외종가", "62 : 시간외단일가매매", "81 : 장후시간외종가"]

        self.gubunComboBox.addItems(column_head)

        column_head = ["신규매수", "신규매도", "매수취소", "매도취소", "매수정정", "매도정정"]

        self.tradeGubunComboBox.addItems(column_head)



    def login(self):
        self.kiwoom.dynamicCall("CommConnect()")

    def event_connect(self, nErrCode):
        if nErrCode == 0 :
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
            self.get_login_info()
            self.getItemList()
            self.getMyAccount()


        elif nErrCode == -100:
            print("사용자 정보교환 실패")
        elif nErrCode == -101:
            print("서버 접속 실패")
        elif nErrCode == -102:
            print("버전처리 실패")


    def get_login_info(self):
        # 로그인 정보 ( 보유계좌, 사용자ID, 접속서버 구성 1. 모의투자, 나머지 : 실거래 )
        accCnt = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
        accList = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
        accList = accList.split(";")
        accList.pop()
        userId = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_ID")
        severGubun = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")



        if severGubun == "1":
            print("모의투자")
            self.statusbar.showMessage("모의투자")

        else:
            print("실서버")
            self.statusbar.showMessage("실서버")

        #message = "모의투자" if severGubun == "1" else "실서버" >> 리팩토링
        #print(message)
        #self.statusbar.showMessage(message)

        self.accComboBox.addItems(accList)

    def getItemList(self):
            # 종목 코드 리스트
            marketList = ["0", "10"]  # 0: 코스피, 10: 코스닥

            for market in marketList:
                codeList = self.kiwoom.dynamicCall("GetCodeListByMarket(QString)", market).split(";")
                for code in codeList:
                    name = self.kiwoom.dynamicCall("GetMasterCodeName(QString)", code)

                    item = dm.DataModel.ItemInfo(code, name)
                    self.myModel.itemList.append(item)


    def searchItem(self):
        print("조회 버튼 클릭")

        itemName = self.searchItemTextEdit.toPlainText()



        if itemName != "":
            for item in self.myModel.itemList:
                if item.itemName == itemName:
                    self.itemCodeTextEdit.setPlainText(item.itemCode)
                    self.getitemInfo(item.itemCode)


    def getitemInfo(self, code):
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)","주식기본정보요청", "opt10001", 0, "5000")


    def receive_trData(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage, sSplmMsg):
        if sTrCode == "opt10001":
            if sRQName == "주식기본정보요청":
                #현재가
                currentPrice = abs(int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "현재가")))
                print(currentPrice)
                self.priceSpinBox.setValue(currentPrice)

        elif sTrCode == "opw00018":
            if sRQName == "계좌잔고평가내역":
                column_header = ["종목번호", "종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]
                colCount = len(column_header)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                self.stocklistTableWidget.setColumnCount(colCount)
                self.stocklistTableWidget.setRowCount(rowCount)
                self.stocklistTableWidget.setHorizontalHeaderLabels(column_header)

                totalBuyingPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                               sRQName, 0, "총매입금액"))
                currentTotalPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, 0, "총평가금액"))
                balanceAsset = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                          sRQName, 0, "추정예탁자산"))
                totalEstimateProfit = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName, 0, "총평가손익금액"))


                self.totalBuyingPriceLabel.setText(str(totalBuyingPrice))
                self.currentTotalPriceLabel.setText(str(currentTotalPrice))
                self.balanceAssetLabel.setText(str(balanceAsset))
                self.totalEstimateProfitLabel.setText(str(totalEstimateProfit))



                for index in range(rowCount):
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "종목번호").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "종목명")
                    amount = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "보유수량"))
                    buyingPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "매입가"))
                    currentPrice = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "현재가"))
                    estmateProfit = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "평가손익"))
                    profitRate = float(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "수익률(%)"))



                    stockBalance = dm.DataModel.stockBalance(itemCode, itemName, amount, buyingPrice, currentPrice, estmateProfit, profitRate)
                    self.myModel.stockBalanceList.append(stockBalance)

                    self.stocklistTableWidget.setItem(index, 0, QTableWidgetItem(str(itemCode)))
                    self.stocklistTableWidget.setItem(index, 1, QTableWidgetItem(str(itemName)))
                    self.stocklistTableWidget.setItem(index, 2, QTableWidgetItem(str(amount)))
                    self.stocklistTableWidget.setItem(index, 3, QTableWidgetItem(str(buyingPrice)))
                    self.stocklistTableWidget.setItem(index, 4, QTableWidgetItem(str(currentPrice)))
                    self.stocklistTableWidget.setItem(index, 5, QTableWidgetItem(str(estmateProfit)))
                    self.stocklistTableWidget.setItem(index, 6, QTableWidgetItem(str(profitRate)))


        elif sTrCode == "opt10075":
            if sRQName == "미체결요청":
                column_header = ["종목번호", "종목명", "주문번호", "주문수량", "주문가격", "미체결수량", "주문구분", "시간", "현재가"]
                colCount = len(column_header)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                self.outstandingTableWidget.setColumnCount(colCount)
                self.outstandingTableWidget.setRowCount(rowCount)
                self.outstandingTableWidget.setHorizontalHeaderLabels(column_header)

                for index in range(rowCount):
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       index,
                                                       "종목번호").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "종목명").strip(" ")
                    orderNumber = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "주문번호").strip(" ")
                    orderVolume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "주문수량").strip(" ")
                    orderPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "주문가격").strip(" ")
                    outstandingVolume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "미체결수량").strip(" ")
                    tradeGubun = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                            "주문구분").strip(" ").strip("+").strip("-")
                    orderTime = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "시간").strip(" ")
                    currentPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "현재가").strip(" ")

                    outstandingBalance = dm.DataModel.outstandingBalance(itemCode, itemName, orderNumber, orderVolume, orderPrice,
                                                             outstandingVolume, tradeGubun, orderTime, currentPrice)
                    self.myModel.outstandingBalanceList.append(outstandingBalance)

                    self.outstandingTableWidget.setItem(index, 0, QTableWidgetItem(itemCode))
                    self.outstandingTableWidget.setItem(index, 1, QTableWidgetItem(itemName))
                    self.outstandingTableWidget.setItem(index, 2, QTableWidgetItem(orderNumber))
                    self.outstandingTableWidget.setItem(index, 3, QTableWidgetItem(orderVolume))
                    self.outstandingTableWidget.setItem(index, 4, QTableWidgetItem(orderPrice))
                    self.outstandingTableWidget.setItem(index, 5, QTableWidgetItem(outstandingVolume))
                    self.outstandingTableWidget.setItem(index, 6, QTableWidgetItem(tradeGubun))
                    self.outstandingTableWidget.setItem(index, 7, QTableWidgetItem(orderTime))
                    self.outstandingTableWidget.setItem(index, 8, QTableWidgetItem(currentPrice))







    def itemBuy(self):
        # 매수 함수
        print("매수 버튼")
        # TODO 계좌정보, 종목코드, 수량, 가격, 가격구분, 거래구분 데이터 가져오기
        acc = self.accComboBox.currentText()  # 계좌정보
        code = self.itemCodeTextEdit.toPlainText()  # 종목코드
        amount = int(self.volumeSpinBox.value())  # 수량
        price = int(self.priceSpinBox.value())  # 가격
        hogaGb = self.gubuncomboBox.currentText()[0:2]  # 호가구분
        if hogaGb == "03":  # 시장가 : 현재 거래되고 있는 가격
            price = 0
        tradeGubun = self.tradeGubuncomboBox.currentText()  # 거래구분

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6000", acc, 1, code, amount, price, hogaGb, ""])

        print(acc, code, amount, price, hogaGb, tradeGubun)

    def itemSell(self):
        # 매도 함수
        print("매도 버튼")

        acc = self.accComboBox.currentText() # 계좌정보
        code = self.itemCodeTextEdit.toPlainText() # 종목코드
        amount = int(self.volumeSpinBox.value()) # 수량
        price = int(self.priceSpinBox.value()) # 가격
        hogaGb = self.gubuncomboBox.currentText()[0:2] # 호가구분
        if hogaGb == "03": # 시장가 : 현재 거래되고 있는 가격
            price = 0
        tradeGubun = self.tradeGubuncomboBox.currentText() # 거래구분

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6500", acc, 2, code, amount, price, hogaGb, ""])


    def getMyAccount(self):
        account = self.accComboBox.currentText()
        #Tr - opw000018
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")

        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌잔고평가내역", "opw00018", 0, "5100")

        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", "str(code)")
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")

        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결요청", "opt10075", 0, "5200")









if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyBot1()
    myApp.show()
    app.exec()
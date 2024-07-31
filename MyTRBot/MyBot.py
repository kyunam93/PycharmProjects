import sys

from PyQt5.QtWidgets import *
# from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QAxContainer import *

# as : 가명을 만들어 주는 키워드
import dataModel as dm

form_class = uic.loadUiType('main_window.ui')[0]

"""
    메인클래스
    작업일자: 2024-07-22
    버전: 0.0.1v
    작업자: 임규남
    역할: 몰루?
    참고할 만한 사이트 : https://wikidocs.net/5755
"""


# 키움증권 관련 클래스 모음
class MyBot(QMainWindow, form_class):

    # 생성자 선언
    def __init__(self):
        super().__init__()
        self.myModel = dm.DataModel()
        self.setUI()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login()

        # kiwoom event
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trData)
        self.kiwoom.OnReceiveChejanData.connect(self.receive_chejanData)

        # Ui_Trigger
        # 조회 버튼 이벤트 처리
        self.searchItemButton.clicked.connect(self.searchItem)
        # 매수 버튼 이벤트 처리
        self.buyPushButton.clicked.connect(self.itemBuy)
        # 매도 버튼 이벤트 처리
        self.sellPushButton.clicked.connect(self.itemSell)
        # 미체결주문 테이블 클릭 이벤트 처리
        self.outstandingTableWidget.itemSelectionChanged.connect(self.selectOutstandingOrder)
        # 계좌잔고 테이블 클릭 이벤트 처리
        self.stockListTableWidget.itemSelectionChanged.connect(self.selectStockListOrder)
        # 정정 버튼 이벤트 처리
        self.changePushButton.clicked.connect(self.itemCorrect)
        # 취소 버튼 이벤트 처리
        self.cancelPushButton.clicked.connect(self.itemCancel)

    def setUI(self):
        # 반드시 PyQt 실행시 필요한 메소드
        self.setupUi(self)

        column_head = [
            "00: 지정가",
            "03: 시장가",
            "05: 조건부지정가",
            "06: 최유리지정가",
            "07: 최우선지정가",
            "10: 지정가IOC",
            "13: 시장가IOC",
            "16: 최유리IOC",
            "20: 지정가FOK",
            "23: 시장가FOK",
            "26: 최유리FOK",
            "61: 장전시간외종가",
            "62: 시간외단일가매매",
            "81: 장후시간외종가"]

        self.gubunComboBox.addItems(column_head)

        column_head = [
            "매수",
            "매도",
            "매수취소",
            "매도취소",
            "매수정정",
            "매도정정"]

        self.tradeGubunComboBox.addItems(column_head)

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()")  # 호출하면 해당 인스턴스의 값을 받아온다

    def event_connect(self, nErrcode):
        if nErrcode == 0:
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
            self.get_login_info()
            self.getItemList()
            self.getMyAccount()
        elif nErrcode == -100:
            print("사용자 정보교환 실패")
        elif nErrcode == -101:
            print("서버접속 실패")
        elif nErrcode == -102:
            print("비전처리 실패")

    def get_login_info(self):
        # 로그인 정보(보유계좌, 접속서버 구성 1. 모의투자, 나머지: 실거래)
        accCnt = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")
        accList = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCLIST")
        accList = accList.split(";")
        accList.pop()
        userId = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "USER_ID")
        serverGubun = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "GetServerGubun")

        if serverGubun == "1":
            msg = "모의투자"
        else:
            msg = "실서버"
        print(msg)
        self.statusbar.showMessage(msg)
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
        # 조회 버튼 클릭시 함수 호출
        print("조회 버튼 클릭")

        msg_box = QMessageBox()
        msg_box.setText("조회할거임?")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        ret = msg_box.exec()
        print(ret)

        itemName = self.searchItemTextEdit.toPlainText()

        if itemName != "":
            for item in self.myModel.itemList:
                if item.itemName == itemName:
                    self.itemCodeTextEdit.setPlainText(item.itemCode)
                    self.getItemInfo(item.itemCode)

    def getItemInfo(self, code):
        # 조회해서 나온 코드를 호출, 종목 정보, TR Data
        # 입력 데이터 설정
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        # TR을 서버로 전송
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", 0, "5000")

    def receive_trData(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage,
                       sSplmMsg):

        print("sRecordName", sRecordName)
        # 화면번호, 사용자 구분명, TR 이름, 레코드 이름, 연속조회 유무, 사용안함, 사용안함, 사용안함, 사용안함
        print(sTrCode)
        if sTrCode == "opt10001":
            print(sRQName)
            if sRQName == "주식기본정보요청":
                # 현재가
                # TR 이름, 레코드 이름, nIndex 번째, TR 에서 얻어오려는 출력항목 이름
                currentPrice = abs(
                    int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                                "현재가")))
                self.priceSpinBox.setValue(currentPrice)

                # price = currentPrice.split("+")
                # print(price[1])
                # self.priceSpinBox.setValue(int(price[1]))
        elif sTrCode == "opw00018":
            print(sRQName)
            if sRQName == "계좌평가잔고내역요청":
                column_head = ["종목번호", "종목명", "보유수량", "매입가", "현재가", "평가손익", "수익률(%)"]
                colCount = len(column_head)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                self.stockListTableWidget.setColumnCount(colCount)
                self.stockListTableWidget.setRowCount(rowCount)
                self.stockListTableWidget.setHorizontalHeaderLabels(column_head)
                self.stockListTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

                totalBuyingPrice = int(
                    self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                            "총매입금액"))
                balanceAsset = int(
                    self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                            "추정예탁자산"))
                currentTotalPrice = int(
                    self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                            "총평가금액"))
                totalEstimateProfit = int(
                    self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                            "총평가손익금액"))

                formatted_totalBuyingPrice = "{:,}".format(totalBuyingPrice)
                formatted_balanceAsset = "{:,}".format(balanceAsset)
                formatted_currentTotalPrice = "{:,}".format(currentTotalPrice)
                formatted_totalEstimateProfit = "{:,}".format(totalEstimateProfit)

                # print(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액"))
                # print(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "추정예탁자산"))
                # print(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가금액"))
                # print(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액"))
                print(totalBuyingPrice, balanceAsset, currentTotalPrice, totalEstimateProfit)

                self.totalBuyingPriceLabel.setText(formatted_totalBuyingPrice)
                self.balanceAssetLabel.setText(formatted_balanceAsset)
                self.currentTotalPriceLabel.setText(formatted_currentTotalPrice)
                self.totalEstimateProfitLabel.setText(formatted_totalEstimateProfit)

                # self.totalBuyingPriceLabel.setNum(totalBuyingPrice)
                # self.balanceAssetLabel.setNum(balanceAsset)
                # self.currentTotalPriceLabel.setNum(currentTotalPrice)
                # self.totalEstimateProfitLabel.setNum(totalEstimateProfit)

                for index in range(rowCount):
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       index, "종목번호").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       index, "종목명").strip(" ")
                    amount = int(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "보유수량"))
                    buyingPrice = int(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "매입가").strip(" ").strip("A"))
                    currentPrice = int(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "현재가").strip(" ").strip("A"))
                    estmateProfit = int(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "평가손익").strip(" ").strip("A"))
                    profitRate = float(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "수익률(%)").strip(" ").strip("A")) / 100

                    # 계좌 정보가 담긴 객체 생성하여 변수에 담기
                    stockBalance = dm.DataModel.StockBalance(itemCode, itemName, amount, buyingPrice, currentPrice,
                                                             estmateProfit, profitRate)
                    # 계좌 정보가 담긴 변수를 리스트에 담는다, 수동 매수, 매도를 위해서
                    self.myModel.stockBalanceList.append(stockBalance)

                    # 테이블 위젯에 아이템 셋팅
                    self.stockListTableWidget.setItem(index, 0, QTableWidgetItem(itemCode))
                    self.stockListTableWidget.setItem(index, 1, QTableWidgetItem(itemName))
                    self.stockListTableWidget.setItem(index, 2, QTableWidgetItem(str(amount)))
                    self.stockListTableWidget.setItem(index, 3, QTableWidgetItem(str(buyingPrice)))
                    self.stockListTableWidget.setItem(index, 4, QTableWidgetItem(str(currentPrice)))
                    self.stockListTableWidget.setItem(index, 5, QTableWidgetItem(str(estmateProfit)))
                    self.stockListTableWidget.setItem(index, 6, QTableWidgetItem(f"{profitRate:.2%}"))

        elif sTrCode == "opt10075":
            print(sRQName)
            if sRQName == "미체결요청":
                column_head = ["종목번호", "종목명", "주문번호", "주문수량", "주문가격", "미체결수량", "주문구분", "시간", "현재가"]
                colCount = len(column_head)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                print(rowCount)
                self.outstandingTableWidget.setColumnCount(colCount)
                self.outstandingTableWidget.setRowCount(rowCount)
                self.outstandingTableWidget.setHorizontalHeaderLabels(column_head)
                self.outstandingTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

                for index in range(rowCount):
                    itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       index, "종목코드").strip(" ").strip("A")
                    itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                       index, "종목명").strip(" ")
                    orderNumber = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                          sRQName, index, "주문번호").strip(" ")
                    orderVolume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                          sRQName, index, "주문수량").strip(" ")
                    orderPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, index, "주문가격").strip(" ")
                    outstandingVolume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                                sRQName, index, "미체결수량").strip(" ")
                    tradeGubun = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, index, "주문구분").strip(" ").strip("+").strip("-")
                    orderTime = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                        index, "시간").strip(" ")
                    currentPrice = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName, index, "현재가").strip(" ")

                    # 계좌 정보가 담긴 객체 생성하여 변수에 담기
                    outstanding = dm.DataModel.OutstandingBalance(itemCode, itemName, orderNumber, orderVolume,
                                                                  orderPrice, outstandingVolume, tradeGubun, orderTime,
                                                                  currentPrice)
                    # 계좌 정보가 담긴 변수를 리스트에 담는다, 수동 매수, 매도를 위해서
                    self.myModel.outstandingBalanceList.append(outstanding)

                    # 테이블 위젯에 아이템 셋팅
                    self.outstandingTableWidget.setItem(index, 0, QTableWidgetItem(itemCode))
                    self.outstandingTableWidget.setItem(index, 1, QTableWidgetItem(itemName))
                    self.outstandingTableWidget.setItem(index, 2, QTableWidgetItem(str(orderNumber)))
                    self.outstandingTableWidget.setItem(index, 3, QTableWidgetItem(str(orderVolume)))
                    self.outstandingTableWidget.setItem(index, 4, QTableWidgetItem(str(orderPrice)))
                    self.outstandingTableWidget.setItem(index, 5, QTableWidgetItem(str(outstandingVolume)))
                    self.outstandingTableWidget.setItem(index, 6, QTableWidgetItem(tradeGubun))
                    self.outstandingTableWidget.setItem(index, 7, QTableWidgetItem(orderTime))
                    self.outstandingTableWidget.setItem(index, 8, QTableWidgetItem(str(currentPrice)))

    def receive_chejanData(self, sGubun, nItemCnt, sFldList):
        print("receive chejan Data")

        if sGubun == "0":  # 접수 & 체결
            conClusionVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 911)  # 체결량
            print("conClusionVolume", conClusionVolume)
            if len(conClusionVolume) > 0:  # 체결이 있을 경우
                itemCode = self.kiwoom.dynamicCall("GetChejanData(int)", 9001).strip(" ").strip("A")  # 종목코드
                itemName = self.kiwoom.dynamicCall("GetChejanData(int)", 302).strip(" ")  # 종목명
                orderNumber = self.kiwoom.dynamicCall("GetChejanData(int)", 9203).strip(" ")  # 주문번호(신규체결시의 번호)
                orderPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 901).strip(" ")  # 주문번호
                orderVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 900).strip(" ")  # 주문수량
                outStandingVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 902).strip(" ")  # 미체결수량
                tradeGubun = self.kiwoom.dynamicCall("GetChejanData(int)", 905).strip(" ").strip("+").strip("-")  # 주문구분
                orderTime = self.kiwoom.dynamicCall("GetChejanData(int)", 908).strip(" ")  # 주문/체결시간
                currentPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 10).strip(" ")  # 현재가

                for itemIndex in range(len(self.myModel.outstandingBalanceList)):
                    # 확인 주문과 정정 주문의 번호가 일치한 경우
                    if self.myModel.outstandingBalanceList[itemIndex].orderNumber == orderNumber:
                        # 미체결량이 있을 경우
                        if outStandingVolume > 0:
                            for rowIndex in range(self.outstandingTableWidget.rowCount()):
                                # 화면에 들어간 주문 번호와 일치한 경우
                                if self.outstandingTableWidget.item(rowIndex, 2).text() == orderNumber:
                                    # 데이터 업데이트
                                    self.myModel.outstandingBalanceList[itemIndex].outStandingVolume = outStandingVolume
                                    self.myModel.outstandingBalanceList[itemIndex].currentPrice = currentPrice

                                    # 테이블 업데이트
                                    self.outstandingTableWidget.setItem(rowIndex, 0, QTableWidgetItem(str(itemCode)))
                                    self.outstandingTableWidget.setItem(rowIndex, 1, QTableWidgetItem(str(itemName)))
                                    self.outstandingTableWidget.setItem(rowIndex, 2, QTableWidgetItem(str(orderNumber)))
                                    self.outstandingTableWidget.setItem(rowIndex, 3, QTableWidgetItem(str(orderPrice)))
                                    self.outstandingTableWidget.setItem(rowIndex, 4, QTableWidgetItem(str(orderVolume)))
                                    self.outstandingTableWidget.setItem(rowIndex, 5,
                                                                        QTableWidgetItem(str(outStandingVolume)))
                                    self.outstandingTableWidget.setItem(rowIndex, 6, QTableWidgetItem(str(tradeGubun)))
                                    self.outstandingTableWidget.setItem(rowIndex, 7, QTableWidgetItem(str(orderTime)))
                                    self.outstandingTableWidget.setItem(rowIndex, 8,
                                                                        QTableWidgetItem(str(currentPrice)))
                                    break
                        else:  # 전량 체결된 경우
                            # 데이터 삭제
                            for itemIndex in range(len(self.myModel.outstandingBalanceList)):
                                # 확인 주문과 정정 주문의 번호가 일치한 경우
                                if self.myModel.outstandingBalanceList[itemIndex].orderNumber == orderNumber:
                                    del self.myModeloutstandingBalanceList[itemIndex]
                                    break
                            for rowIndex in range(self.outstandingTableWidget.rowCount()):
                                # 화면에 들어간 주문 번호와 일치한 경우
                                if self.outstandingTableWidget.item(rowIndex, 2).text() == orderNumber:
                                    self.outstandingTableWidget.removeRow(rowIndex)
                                    break
            else:  # 접수
                itemCode = self.kiwoom.dynamicCall("GetChejanData(int)", 9001).strip(" ").strip("A")  # 종목코드
                itemName = self.kiwoom.dynamicCall("GetChejanData(int)", 302).strip(" ")  # 종목명
                orderNumber = self.kiwoom.dynamicCall("GetChejanData(int)", 9203).strip(" ")  # 주문번호(신규체결시의 번호)
                orderPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 901).strip(" ")  # 주문금액
                orderVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 900).strip(" ")  # 주문수량
                outStandingVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 902).strip(" ")  # 미체결수량
                tradeGubun = self.kiwoom.dynamicCall("GetChejanData(int)", 905).strip(" ").strip("+").strip("-")  # 주문구분
                orderTime = self.kiwoom.dynamicCall("GetChejanData(int)", 908).strip(" ")  # 주문/체결시간
                currentPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 10).strip(" ")  # 현재가

                print("outStandingVolume", outStandingVolume)
                #
                for rowIndex in range(self.outstandingTableWidget.rowCount()):
                    if self.outstandingTableWidget.item(rowIndex, 2).text() == orderNumber \
                            and self.outstandingTableWidget.item(rowIndex, 3).text() == orderVolume \
                            and self.outstandingTableWidget.item(rowIndex, 4).text() == orderPrice:
                        if self.outstandingTableWidget.item(rowIndex, 5).text() == outStandingVolume:
                            # 정정확인주문
                            print("정정확인주문")
                            return
                        else:
                            # 원주문 삭제
                            self.outstandingTableWidget.removeRow(rowIndex)
                            for itemIndex in range(len(self.myModel.outstandingBalanceList)):
                                if self.myModel.outstandingBalanceList[itemIndex].orderNumber == orderNumber \
                                        and self.myModel.outstandingBalanceList[itemIndex].orderVolume == orderVolume \
                                        and self.myModel.outstandingBalanceList[itemIndex].orderPrice == orderPrice \
                                        and self.myModel.outstandingBalanceList[
                                    itemIndex].outStandingVolume == outStandingVolume:
                                    del self.myModel.outstandingBalanceList[itemIndex]
                                    break
                            break

                    for itemIndex in range(len(self.myModel.outstandingBalanceList)):
                        # 확인 주문과 정정 주문의 번호가 일치한 경우
                        if self.myModel.outstandingBalanceList[itemIndex].orderNumber == orderNumber:

                # 취소시 주문 삭제
                if outStandingVolume == 0: # 미체결 건 0 일때
                    print("너 왜 안돼?")
                    # 원주문 삭제
                    for itemIndex in range(len(self.myModel.outstandingBalanceList)):
                        if self.myModel.outstandingBalanceList[itemIndex].orderNumber == orderNumber:
                            del self.myModel.outstandingBalanceList[itemIndex]
                            break
                    # 테이블 삭제
                    for rowIndex in range(self.outstandingTableWidget.rowCount()):
                        # 화면에 들어간 주문 번호와 일치한 경우
                        if self.outstandingTableWidget.item(rowIndex, 2).text() == orderNumber:
                            self.outstandingTableWidget.removeRow(rowIndex)
                            break

                # 데이터 추가
                outStandingOrder = dm.DataModel.OutstandingBalance(itemCode, itemName, orderNumber, orderVolume,
                                                                   orderPrice, outStandingVolume, tradeGubun,
                                                                   orderTime, currentPrice)
                self.myModel.outstandingBalanceList.append(outStandingOrder)

                # 테이블 추가
                self.outstandingTableWidget.setRowCount(self.outstandingTableWidget.rowCount() + 1)
                index = self.outstandingTableWidget.rowCount() - 1

                # 테이블 업데이트
                self.outstandingTableWidget.setItem(index, 0, QTableWidgetItem(str(itemCode)))
                self.outstandingTableWidget.setItem(index, 1, QTableWidgetItem(str(itemName)))
                self.outstandingTableWidget.setItem(index, 2, QTableWidgetItem(str(orderNumber)))
                self.outstandingTableWidget.setItem(index, 3, QTableWidgetItem(str(orderVolume)))
                self.outstandingTableWidget.setItem(index, 4, QTableWidgetItem(str(orderPrice)))
                self.outstandingTableWidget.setItem(index, 5, QTableWidgetItem(str(outStandingVolume)))
                self.outstandingTableWidget.setItem(index, 6, QTableWidgetItem(str(tradeGubun)))
                self.outstandingTableWidget.setItem(index, 7, QTableWidgetItem(str(orderTime)))
                self.outstandingTableWidget.setItem(index, 8, QTableWidgetItem(str(currentPrice)))
        # 잔고 처리
        elif sGubun == 1:  # 국내주식 잔고변경
            pass
        elif sGubun == 4:  # 파생잔고변경
            pass

    def itemBuy(self):
        # 매수 함수
        print("매수 버튼(itemBuy)")

        acc = self.accComboBox.currentText()  # 계좌정보
        code = self.itemCodeTextEdit.toPlainText()  # 종목코드
        amount = int(self.volumeSpinBox.value())  # 수량
        price = int(self.priceSpinBox.value())  # 가격
        hogaGb = self.gubunComboBox.currentText()[0:2]  # 호가구분
        if hogaGb == "03":  # 시장가 : 현재 거래되고 있는 가격
            price = 0

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6000", acc, 1, code, amount, price, hogaGb, ""])

        print("계좌정보", acc, "종목코드", code, "수량", amount, "가격", price, "호가구분", hogaGb)

    def itemSell(self):
        # 매도 함수
        print("매도 버튼(itemSell)")

        acc = self.accComboBox.currentText()  # 계좌정보
        code = self.itemCodeTextEdit.toPlainText()  # 종목코드
        amount = int(self.volumeSpinBox.value())  # 수량
        price = int(self.priceSpinBox.value())  # 가격
        hogaGb = self.gubunComboBox.currentText()[0:2]  # 호가구분
        if hogaGb == "03":  # 시장가 : 현재 거래되고 있는 가격
            price = 0

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6500", acc, 2, code, amount, price, hogaGb, ""])

    def getMyAccount(self):
        print("getMyAccount")

        # 계좌 잔고 호출
        account = self.accComboBox.currentText()  # 계좌정보
        code = self.itemCodeTextEdit.toPlainText()

        print("account", account, "code", code)

        # Tr -
        # SetInputValue 입력 데이터 설정
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)  # 전문 조회할 보유계좌번호 10자리
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "")  # 사용안함, 공백
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")  # 공백불가
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")  # 1:합산, 2:개별

        # TR을 서버로 전송
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", 0,
                                "5100")  # 0은 반복횟수

        # Tr -
        # SetInputValue 입력 데이터 설정
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account)  # 전문 조회할 보유계좌번호 10자리
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "전체종목구분 ", "0")  # 전체종목구분 = 0:전체, 1:종목
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 매매구분 = 0:전체, 1:매도, 2:매수
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드",
                                "")  # 종목코드 = 전문 조회할 종목코드 (공백허용, 공백입력시 전체종목구분 "0" 입력하여 전체 종목 대상으로 조회)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")  # 체결구분 = 0:전체, 2:체결, 1:미체결

        # CommRqData TR을 서버로 전송
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "미체결요청", "opt10075", 0, "5200")  # 0은 반복횟수

    def selectOutstandingOrder(self):
        print("미체결 선택 함수")
        # 미체결 선택 함수
        check = 0
        for rowIndex in range(self.outstandingTableWidget.rowCount()):
            for colIndex in range(self.outstandingTableWidget.columnCount()):
                # 아이템이 있는 경우
                if self.outstandingTableWidget.item(rowIndex, colIndex) is not None:
                    # 아이템이 선택된 경우
                    if self.outstandingTableWidget.item(rowIndex, colIndex).isSelected():
                        check = 1
                        self.searchItemTextEdit.setText(self.outstandingTableWidget.item(rowIndex, 1).text())  # 종목명
                        self.itemCodeTextEdit.setText(self.outstandingTableWidget.item(rowIndex, 0).text())  # 종목코드
                        self.volumeSpinBox.setValue(int(self.outstandingTableWidget.item(rowIndex, 5).text()))  # 수량
                        self.priceSpinBox.setValue(int(self.outstandingTableWidget.item(rowIndex, 4).text()))  # 가격
                        self.ordernumberTextEdit.setText(self.outstandingTableWidget.item(rowIndex, 2).text())  # 원주문번호
                        index = self.tradeGubunComboBox.findText(self.outstandingTableWidget.item(rowIndex, 6).text())
                        self.tradeGubunComboBox.setCurrentIndex(index)  # 거래구분
            if check == 1:
                break

    def selectStockListOrder(self):
        # 계좌잔고 선택 함수
        print("계좌잔고 선택 함수")
        check = 0
        for rowIndex in range(self.stockListTableWidget.rowCount()):
            print(rowIndex)
            for colIndex in range(self.stockListTableWidget.columnCount()):
                print(colIndex)
                if self.stockListTableWidget.item(rowIndex, colIndex) is not None:
                    if self.stockListTableWidget.item(rowIndex, colIndex).isSelected():
                        check = 1
                        self.searchItemTextEdit.setText(self.stockListTableWidget.item(rowIndex, 1).text())  # 종목명
                        self.itemCodeTextEdit.setText(self.stockListTableWidget.item(rowIndex, 0).text())  # 종목코드
                        self.volumeSpinBox.setValue(int(self.stockListTableWidget.item(rowIndex, 2).text()))  # 수량
                        self.priceSpinBox.setValue(int(self.stockListTableWidget.item(rowIndex, 3).text()))  # 가격
                        self.ordernumberTextEdit.setText("")  # 원주문번호
                        index = self.tradeGubunComboBox.findText("")
                        self.tradeGubunComboBox.setCurrentIndex(index)  # 거래구분

            if check == 1:
                break

    def itemCorrect(self):
        # 정정
        print("item Correct")

        acc = self.accComboBox.currentText().strip(" ")  # 계좌번호
        code = self.itemCodeTextEdit.toPlainText().strip(" ")  # 종목코드
        amount = int(self.volumeSpinBox.value())  # 수량
        price = int(self.priceSpinBox.value())  # 가격
        hogaGb = self.gubunComboBox.currentText()[0:2]  # 호가구분
        orderType = self.tradeGubunComboBox.currentText().strip(" ")  # 거래구분
        if orderType == "매수" or orderType == "매수정정":
            orderType = 5  # SendOrder 함수 nOrderType - 5 : 매수 정정
        elif orderType == "매도" or orderType == "매도정정":
            orderType = 6  # SendOrder 함수 nOrderType - 6 : 매도 정정
        orderNo = self.ordernumberTextEdit.toPlainText().strip(" ")  # 원주문번호

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6700", acc, orderType, code, amount, price, hogaGb, orderNo])

    def itemCancel(self):
        # 취소
        print("item Cancel")

        acc = self.accComboBox.currentText().strip(" ")  # 계좌번호
        code = self.itemCodeTextEdit.toPlainText().strip(" ")  # 종목코드
        amount = int(self.volumeSpinBox.value())  # 수량
        price = int(self.priceSpinBox.value())  # 가격
        hogaGb = self.gubunComboBox.currentText()[0:2]  # 호가구분
        orderType = self.tradeGubunComboBox.currentText().strip(" ")  # 거래구분
        if orderType == "매수" or orderType == "매수취소" or orderType == "매수정정":
            orderType = 3  # SendOrder 함수 nOrderType - 3 : 매수취소
        elif orderType == "매도" or orderType == "매도취소" or orderType == "매도정정":
            orderType = 4  # SendOrder 함수 nOrderType - 4 : 매도취소
        orderNo = self.ordernumberTextEdit.toPlainText().strip(" ")  # 원주문번호

        print("acc", acc, "code", code, "amount", amount, "price", price, "hogaGb", hogaGb, "orderType", orderType, "orderNo", orderNo)

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString",
                                ["주식주문", "6800", acc, orderType, code, amount, price, hogaGb, orderNo])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyBot()
    myApp.show()
    app.exec()

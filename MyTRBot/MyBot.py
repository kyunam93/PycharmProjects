import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5.QAxContainer import *
from PyQt5.QtCore import Qt

import matplotlib.pyplot as plt
# 봉 차틑 만듬
# import mpl_finance as matfin
import mplfinance.original_flavor as matfin
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# 차트의 화면을 2개로 나눠 그리기 위한 그리드
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker

import datetime
from datetime import date

import time
# String 을 time 으로 포멧팅
from time import strftime

# as : 가명을 만들어 주는 키워드
import dataModel as dm

# ui 등록
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
        self.fig = None
        self.canvas = None
        self.myModel = dm.DataModel()
        self.setUI()
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.login()

        # kiwoom event
        self.kiwoom.OnEventConnect.connect(self.event_connect)
        self.kiwoom.OnReceiveTrData.connect(self.receive_trData)
        self.kiwoom.OnReceiveChejanData.connect(self.receive_chejanData)
        self.kiwoom.OnReceiveConditionVer.connect(self.receive_condition)
        self.kiwoom.OnReceiveTrCondition.connect(self.receive_trCondition)

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
        # 볼개수 조회 버튼 이벤트 처리
        self.chartPushButton.clicked.connect(self.chartShow)
        # 조건식 추가 버튼 이벤트 처리
        self.addAutoTradePushButton.clicked.connect(self.addAutoTradeCondition)
        # 조건식 삭제 버튼 이벤트 처리
        self.removeAutoTradePushButton.clicked.connect(self.removeAutoTradeCondition)
        # 조건검색시작 버튼 이벤트 처리
        self.conditionSearchPushBox.clicked.connect(self.conditionSearch)
        # 자동매매시작 버튼 이벤트 처리
        self.autoTradePushBox.clicked.connect(self.autoTrade)

        self.boolCondition = 0

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

        column_head = ["매수", "매도", "매수/매도"]
        self.autoTradeGubunComboBox.addItems(column_head)

        # 차트생성
        # 커스텀 가능한 피규어
        self.fig = plt.figure(figsize=(8, 5))  # inch 단위
        self.canvas = FigureCanvas(self.fig)
        self.chartLayout.addWidget(self.canvas)
        # plt.plot()

        src = "C:\\Users\\kosmo\\PycharmProjects\\PycharmProjects\\MyTRBot\\img.png"

        self.imgLabel.setPixmap(QPixmap(src).scaled(350, 130, Qt.IgnoreAspectRatio))

    def login(self):
        self.kiwoom.dynamicCall("CommConnect()")  # 호출하면 해당 인스턴스의 값을 받아온다

    def event_connect(self, nErrcode):
        if nErrcode == 0:
            print("로그인 성공")
            self.statusbar.showMessage("로그인 성공")
            self.get_login_info()
            self.getItemList()
            self.getMyAccount()
            self.getConditionList()
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
        print("서버 구분", msg)
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

        # msg_box = QMessageBox()
        # msg_box.setText("조회할거임?")
        # msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #
        # ret = msg_box.exec()
        # print(ret)

        itemName = self.searchItemTextEdit.toPlainText()

        if itemName != "":
            for item in self.myModel.itemList:
                if item.itemName == itemName:
                    self.itemCodeTextEdit.setPlainText(item.itemCode)
                    self.getItemInfo(item.itemCode)
                    self.drawDayChart(item.itemCode)

    def getItemInfo(self, code):
        # 조회해서 나온 코드를 호출, 종목 정보, TR Data
        # 입력 데이터 설정
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        # TR을 서버로 전송
        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식기본정보요청", "opt10001", 0, "5000")

    def receive_trData(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, nDataLength, sErrorCode, sMessage,
                       sSplmMsg):

        print("레코드 명", sRecordName)
        # 화면번호, 사용자 구분명, TR 이름, 레코드 이름, 연속조회 유무, 사용안함, 사용안함, 사용안함, 사용안함
        print("TR 코드", sTrCode)
        if sTrCode == "opt10001":
            print("리퀘스트 명", sRQName)
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
            print("리퀘스트 명", sRQName)
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
            print("리퀘스트 명", sRQName)
            if sRQName == "미체결요청":
                column_head = ["종목번호", "종목명", "주문번호", "주문수량", "주문가격", "미체결수량", "주문구분", "시간", "현재가"]
                colCount = len(column_head)
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
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
                    currentPrice = abs(
                        int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                    sRQName, index, "현재가").strip(" ")))

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
        elif sTrCode == "opt10081":
            print("리퀘스트 명", sRQName)
            if sRQName == "주식일봉차트조회요청":
                # 사용할 데이터 개수
                rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                print(rowCount)

                dateList = []  # 일자 모음
                openPrice = []  # 시가
                closePrice = []  # 공가
                highPrice = []  # 고가
                lowPrice = []  # 저가
                volume = []  # 일 체결량

                # candlenumber = ""

                # 봉차트는 기본 60개 가져온다
                # 신규 상장 기업은 있는 데이터만 가져온다
                if self.candlenumberTextEdit.toPlainText() is not None and self.candlenumberTextEdit.toPlainText() != "":
                    candlenumber = int(self.candlenumberTextEdit.toPlainText())
                else:
                    candlenumber = 60

                if candlenumber > rowCount:
                    candlenumber = rowCount

                # 캔들넘버만큼 숫자를 가져온다
                for index in range(candlenumber):
                    m_date = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                     index, "일자").strip(" ")
                    m_fDate = datetime.datetime(int(m_date[0:4]), int(m_date[4:6]), int(m_date[6:8]))
                    m_openPrice = abs(
                        int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                    index, "시가").strip(" ")))
                    m_closePrice = abs(
                        int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                    index, "현재가").strip(" ")))
                    m_highPrice = abs(
                        int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                    index, "고가").strip(" ")))
                    m_lowPrice = abs(
                        int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                    index, "저가").strip(" ")))
                    m_volume = int(
                        self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, index,
                                                "거래량").strip(" "))

                    print("일자", m_date, m_fDate, "시가", m_openPrice, "현재가", m_closePrice, "고가", m_highPrice, "저가",
                          m_lowPrice, "거래량", m_volume)

                    dateList.insert(0, m_fDate)
                    openPrice.insert(0, m_openPrice)
                    closePrice.insert(0, m_closePrice)
                    highPrice.insert(0, m_highPrice)
                    lowPrice.insert(0, m_lowPrice)
                    volume.insert(0, m_volume)

                    dayList = []
                    nameList = []

                    # enumrate() 내장 함수 사용
                    for i, day in enumerate(dateList):
                        if day.weekday() == 0:  # 요일 가져오기, 0: 월요일
                            dayList.append(i)
                            nameList.append(str(day.strftime("%Y-%m-%d")))

                    # 2행 1열 차트 생성, 각 행의 높이는 3 대 1 비율
                    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])
                    axes = [plt.subplot(gs[0]), plt.subplot(gs[1], sharex=axes[0])]
                    # axes = []
                    # axes.append(plt.subplot(gs[0]))
                    # axes.append(plt.subplot(gs[1], sharex=axes[0]))  # share X 각 차트들이 x 행의 데이터를 공유한다.

                    axes[0].get_xaxis().set_visible(False)  # 첫번째 행의 x 축 안보여줄거임, 데이터 공유만 할거임

                    axes[1].set_xticks(dayList)
                    # 기울기(rotation) 45도,
                    axes[1].set_xticklabels(nameList, rotation=45)

                    # 넓이(width) : 0.5, 상승봉(colorup) : 레드, 하강봉(colordown) : 블루
                    matfin.candlestick2_ochl(axes[0], openPrice, closePrice, highPrice, lowPrice, width=1,
                                             colorup='r', colordown='b')
                    # color : k = black, 넓이(width): 0.6, 정렬(align) : center
                    axes[1].bar(range(len(dateList)), volume, color='k', width=0.6, align='center')
                    plt.tight_layout()

                    self.canvas.draw()

        elif sTrCode == "OPTKWFID":
            print("화면번호", sScrNo)
            if sScrNo == "8000":
                # 테이블이 없을 때 실행하셈
                if self.conditionItemTableWidget.rowCount() is None or self.conditionItemTableWidget.rowCount() == 0:
                    # 데이터를 가져와서 conditionItemTableWidget 테이블에 추가
                    print(sRQName)
                    column_head = ["종목번호", "종목명", "현재가", "등락률", "전일대비", "거래량", "시가", "고가", "저가", "조건식명"]
                    colCount = len(column_head)
                    rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                    self.conditionItemTableWidget.setColumnCount(colCount)
                    self.conditionItemTableWidget.setRowCount(rowCount)
                    self.conditionItemTableWidget.setHorizontalHeaderLabels(column_head)
                    self.conditionItemTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

                    for index in range(rowCount):
                        itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName,
                                                           index, "종목코드").strip(" ").strip("A")
                        itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName,
                                                           index, "종목명").strip(" ")
                        currentPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "현재가").strip(" ")))
                        fluctuationRate = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                                  sTrCode,
                                                                  sRQName, index, "등락율").strip(" ")
                        priceDiffYes = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                               sRQName, index, "전일대비").strip(" ")
                        volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, index, "거래량").strip(" ")
                        openPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "시가").strip(" ")))
                        highPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "고가").strip(" ").strip("+").strip("-")))
                        lowPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                        index, "저가").strip(" ")))

                        conditionItem = dm.DataModel.ConditionItemInfo(itemCode, itemName, currentPrice,
                                                                       fluctuationRate,
                                                                       priceDiffYes,
                                                                       openPrice, highPrice, lowPrice, volume, sRQName)
                        # self.myModel.conditionItemList[sRQName] = conditionItem
                        self.myModel.conditionItemList[sRQName].append(conditionItem)

                        # 테이블 위젯에 아이템 셋팅
                        self.conditionItemTableWidget.setItem(index, 0, QTableWidgetItem(itemCode))
                        self.conditionItemTableWidget.setItem(index, 1, QTableWidgetItem(itemName))
                        self.conditionItemTableWidget.setItem(index, 2, QTableWidgetItem(str(currentPrice)))
                        self.conditionItemTableWidget.setItem(index, 3, QTableWidgetItem(fluctuationRate))
                        self.conditionItemTableWidget.setItem(index, 4, QTableWidgetItem(priceDiffYes))
                        self.conditionItemTableWidget.setItem(index, 5, QTableWidgetItem(volume))
                        self.conditionItemTableWidget.setItem(index, 6, QTableWidgetItem(str(openPrice)))
                        self.conditionItemTableWidget.setItem(index, 7, QTableWidgetItem(str(highPrice)))
                        self.conditionItemTableWidget.setItem(index, 8, QTableWidgetItem(str(lowPrice)))
                        self.conditionItemTableWidget.setItem(index, 9, QTableWidgetItem(sRQName))
                else:  # 1번 이상 조건검색시작을 눌렀을 시
                    rowCount = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
                    rowIndex = self.conditionItemTableWidget.rowCount()

                    self.conditionItemTableWidget.setRowCount(rowIndex + rowCount)

                    for index in range(rowCount):
                        itemCode = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName,
                                                           index, "종목코드").strip(" ").strip("A")
                        itemName = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                           sRQName,
                                                           index, "종목명").strip(" ")
                        currentPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "현재가").strip(" ")))
                        fluctuationRate = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                                  sTrCode,
                                                                  sRQName, index, "등락율").strip(" ")
                        priceDiffYes = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                               sRQName, index, "전일대비").strip(" ")
                        volume = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                         sRQName, index, "거래량").strip(" ")
                        openPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "시가").strip(" ")))
                        highPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode,
                                                        sRQName, index, "고가").strip(" ").strip("+").strip("-")))
                        lowPrice = abs(
                            int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName,
                                                        index, "저가").strip(" ")))

                        conditionItem = dm.DataModel.ConditionItemInfo(itemCode, itemName, currentPrice,
                                                                       fluctuationRate,
                                                                       priceDiffYes,
                                                                       openPrice, highPrice, lowPrice, volume, sRQName)
                        # self.myModel.conditionItemList[sRQName] = conditionItem
                        self.myModel.conditionItemList[sRQName].append(conditionItem)

                        nIndex = rowIndex + rowCount

                        # 테이블 위젯에 아이템 셋팅
                        self.conditionItemTableWidget.setItem(nIndex, 0, QTableWidgetItem(itemCode))
                        self.conditionItemTableWidget.setItem(nIndex, 1, QTableWidgetItem(itemName))
                        self.conditionItemTableWidget.setItem(nIndex, 2, QTableWidgetItem(str(currentPrice)))
                        self.conditionItemTableWidget.setItem(nIndex, 3, QTableWidgetItem(fluctuationRate))
                        self.conditionItemTableWidget.setItem(nIndex, 4, QTableWidgetItem(priceDiffYes))
                        self.conditionItemTableWidget.setItem(nIndex, 5, QTableWidgetItem(volume))
                        self.conditionItemTableWidget.setItem(nIndex, 6, QTableWidgetItem(str(openPrice)))
                        self.conditionItemTableWidget.setItem(nIndex, 7, QTableWidgetItem(str(highPrice)))
                        self.conditionItemTableWidget.setItem(nIndex, 8, QTableWidgetItem(str(lowPrice)))
                        self.conditionItemTableWidget.setItem(nIndex, 9, QTableWidgetItem(sRQName))

    def receive_chejanData(self, sGubun, nItemCnt, sFldList):
        print("receive chejan Data")

        if sGubun == "0":  # 접수 & 체결
            conClusionVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 911)  # 체결량
            print("체결량", conClusionVolume)
            if len(conClusionVolume) > 0:  # 체결이 있을 경우
                itemCode = self.kiwoom.dynamicCall("GetChejanData(int)", 9001).strip(" ").strip("A")  # 종목코드
                itemName = self.kiwoom.dynamicCall("GetChejanData(int)", 302).strip(" ")  # 종목명
                orderNumber = self.kiwoom.dynamicCall("GetChejanData(int)", 9203).strip(" ")  # 주문번호(신규체결시의 번호)
                orderPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 901).strip(" ")  # 주문번호
                orderVolume = self.kiwoom.dynamicCall("GetChejanData(int)", 900).strip(" ")  # 주문수량
                outStandingVolume = int(self.kiwoom.dynamicCall("GetChejanData(int)", 902).strip(" "))  # 미체결수량
                tradeGubun = self.kiwoom.dynamicCall("GetChejanData(int)", 905).strip(" ").strip("+").strip("-")  # 주문구분
                orderTime = self.kiwoom.dynamicCall("GetChejanData(int)", 908).strip(" ")  # 주문/체결시간
                currentPrice = abs(int(self.kiwoom.dynamicCall("GetChejanData(int)", 10).strip(" ")))  # 현재가

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
                                    del self.myModel.outstandingBalanceList[itemIndex]
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
                currentPrice = abs(int(self.kiwoom.dynamicCall("GetChejanData(int)", 10).strip(" ")))  # 현재가

                print("미체결수량", outStandingVolume)

                # 정정하는 부분
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

                # 취소시 주문 삭제
                if outStandingVolume == 0:  # 미체결 건 0 일때
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
                    return

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
        if sGubun == "1":  # 국내주식 잔고변경
            print("국내주식 잔고변경", sGubun)

            itemCode = self.kiwoom.dynamicCall("GetChejanData(int)", 9001).strip(" ").strip("A")  # 종목코드
            itemName = self.kiwoom.dynamicCall("GetChejanData(int)", 302).strip(" ")  # 종목명
            amount = self.kiwoom.dynamicCall("GetChejanData(int)", 930).strip(" ")  # 보유수량
            buyingPrice = self.kiwoom.dynamicCall("GetChejanData(int)", 931).strip(" ")  # 매입단가
            currentPrice = abs(int(self.kiwoom.dynamicCall("GetChejanData(int)", 10).strip(" ")))  # 현재가
            estimateProfit = (currentPrice - int(buyingPrice)) * int(amount)  # 손이익

            if buyingPrice != "0":
                profitRate = estimateProfit / (int(buyingPrice) * int(amount)) * 100
            else:
                profitRate = 0

            check = 0  # 잔고 유무 체크용
            for item in self.myModel.stockBalanceList:
                if item.itemName.strip(" ") == itemName.strip(" "):  # 이름이 일치하면
                    check = 1
                    if amount == "0":
                        for rowIndex in range(self.outstandingTableWidget.rowCount()):
                            if self.stockListTableWidget.item(rowIndex, 0).text() == itemCode:
                                self.stockListTableWidget.removeRow(rowIndex)
                                break
                        self.myModel.stockBalanceList.remove(item)
                        break

                    # 데이터 update
                    item.amount = amount
                    item.buyingPrice = buyingPrice
                    item.currentPrice = currentPrice
                    item.estimateProfit = estimateProfit
                    item.profitRate = profitRate

                    # 테이블 update
                    for rowIndex in range(len(self.myModel.stockBalanceList)):
                        if self.stockListTableWidget.item(rowIndex, 0).text().strip(" ") == itemCode:
                            self.stockListTableWidget.setItem(rowIndex, 0, QTableWidgetItem(str(itemCode)))
                            self.stockListTableWidget.setItem(rowIndex, 1, QTableWidgetItem(str(itemName)))
                            self.stockListTableWidget.setItem(rowIndex, 2, QTableWidgetItem(str(amount)))
                            self.stockListTableWidget.setItem(rowIndex, 3, QTableWidgetItem(str(buyingPrice)))
                            self.stockListTableWidget.setItem(rowIndex, 4, QTableWidgetItem(str(currentPrice)))
                            self.stockListTableWidget.setItem(rowIndex, 5, QTableWidgetItem(str(estimateProfit)))
                            self.stockListTableWidget.setItem(rowIndex, 6, QTableWidgetItem(f"{profitRate:.2%}"))
                            break

            if check == 0:  # 동일한 잔고가 없을 때
                print("동일한 잔고가 없을 때", check)
                if amount == "0":
                    for rowIndex in range(self.stockListTableWidget.rowCount()):
                        if self.stockListTableWidget.item(rowIndex, 0).text().strip(" ") == itemCode:
                            self.stockListTableWidget.removeRow(rowIndex)
                            break

                    for item in self.myModel.stockBalanceList:
                        if item.itemCode.strip(" ") == itemName.strip(" "):
                            self.myModel.stockBalanceList.remove(item)
                            break
                    return

            stockBalance = dm.DataModel.StockBalance(itemCode, itemName, amount, buyingPrice, currentPrice,
                                                     estimateProfit, profitRate)
            self.myModel.stockBalanceList.append(stockBalance)

            self.stockListTableWidget.setRowCount(self.stockListTableWidget.rowCount() + 1)
            index = self.stockListTableWidget.rowCount() - 1

            self.stockListTableWidget.setItem(index, 0, QTableWidgetItem(str(itemCode)))
            self.stockListTableWidget.setItem(index, 1, QTableWidgetItem(str(itemName)))
            self.stockListTableWidget.setItem(index, 2, QTableWidgetItem(str(amount)))
            self.stockListTableWidget.setItem(index, 3, QTableWidgetItem(str(buyingPrice)))
            self.stockListTableWidget.setItem(index, 4, QTableWidgetItem(str(currentPrice)))
            self.stockListTableWidget.setItem(index, 5, QTableWidgetItem(str(estimateProfit)))
            self.stockListTableWidget.setItem(index, 6, QTableWidgetItem(f"{profitRate:.2%}"))

        if sGubun == "4":  # 파생잔고변경
            print("파생잔고변경", sGubun)

    def receive_condition(self, lRet, sMsg):
        # lRet : 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
        # sMsg : 메시지
        print("조건목록 검색 이벤트 함수")

        if lRet != 0:  # 호출 성공
            conditionListTotal = self.kiwoom.dynamicCall("GetConditionNameList()").split(";")
            conditionListTotal.pop()
            print(conditionListTotal)

            # 딕셔너리 형태 리스트
            conditionList = {"code": [], "name": []}
            # 배열 형태
            #
            #
            # 데이터 입력
            for condition in conditionListTotal:
                temp = condition.split("^")
                conditionList["code"].append(temp[0])
                conditionList["name"].append(temp[1])

            column_head = ["조건코드", "조건명"]
            colCount = len(column_head)
            rowCount = len(conditionListTotal)
            self.conditionTableWidget.setColumnCount(colCount)  # 열
            self.conditionTableWidget.setRowCount(rowCount)  # 행
            self.conditionTableWidget.setHorizontalHeaderLabels(column_head)  # 헤더 삽입
            self.conditionTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 수정 방지

            for index in range(rowCount):
                self.conditionTableWidget.setItem(index, 0, QTableWidgetItem(str(conditionList["code"][index])))
                self.conditionTableWidget.setItem(index, 1, QTableWidgetItem(str(conditionList["name"][index])))

    def receive_trCondition(self, sScrNo, strCodeList, strConditionName, nIndex, nNext):
        # 화면번호, 종목코드 리스트, 조건식 이름, 조건 고유번호, 연속조회 여부

        codeList = strCodeList.split(";")
        codeList.pop()
        print(len(codeList))

        # CommKwRqData() 호출 : 한번에 100종목까지 조회할 수 있는 복수종목 조회함수
        self.kiwoom.dynamicCall("CommKwRqData(QString, bool, int, int, QString, QString)", strCodeList,
                                bool(nNext), len(codeList), 0, strConditionName, "8000")
        # 조회하려는 종목코드 리스트, 연속조회 여부, 종목코드 개수, 0: 주식종목 3: 선물옵션 종목,
        # 사용자 구분명(sRQName), 화면번호(sScreenNo)

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
        code = self.itemCodeTextEdit.toPlainText()  # 종목코드

        print("계좌번호", account, "종목코드", code)

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
                        self.drawDayChart(self.outstandingTableWidget.item(rowIndex, 0).text())
            if check == 1:
                break

    def selectStockListOrder(self):
        # 계좌잔고 선택 함수
        print("계좌잔고 선택 함수")
        check = 0
        for rowIndex in range(self.stockListTableWidget.rowCount()):
            for colIndex in range(self.stockListTableWidget.columnCount()):
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
                        self.drawDayChart(self.stockListTableWidget.item(rowIndex, 0).text())
                        break

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

        print("계좌번호", acc, "종목코드", code, "수량", amount, "가격", price, "호가구분", hogaGb, "거래구분", orderType,
              "원주문번호", orderNo)

        self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                ["주식주문", "6800", acc, orderType, code, amount, price, hogaGb, orderNo])

    def drawDayChart(self, itemCode):
        # 일차트 그리기

        now = datetime.datetime.now()  # 현재 날자 가져옴
        nowDate = now.strftime("%Y%m%d")  # YYYYMMDD 포멧

        # opt10081 데이터 요청
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", itemCode)
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "기준일자", nowDate)
        # 수정주가구분 = 0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락
        self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회요청", "opt10081", 0, "5300")

    def chartShow(self):
        if self.itemCodeTextEdit.toPlainText() is not None and self.itemCodeTextEdit.toPlainText != "":
            code = self.itemCodeTextEdit.toPlainText().strip(" ")
            self.drawDayChart(code)

    def getConditionList(self):
        print("조건검색")

        if self.kiwoom.dynamicCall("getConditionLoad()") == 1:
            print("조건식 목록 호출 성공")
            # 조건검색 목록을 모두 수신하면 OnReceiveConditionVer()이벤트가 발생
        else:
            print("조건식 목록 호출 실패")
            return

    def addAutoTradeCondition(self):
        print("조건식 추가 함수")

        check = 0
        for rowIndex in range(self.conditionTableWidget.rowCount()):
            for colIndex in range(self.conditionTableWidget.columnCount()):
                if self.conditionTableWidget.item(rowIndex, colIndex).isSelected():
                    check = 1
                    code = self.conditionTableWidget.item(rowIndex, 0).text()
                    name = self.conditionTableWidget.item(rowIndex, 1).text()
                    break

            if check == 1:
                break

        startTime = self.startTimeEdit.time()
        endTime = self.endTimeEdit.time()
        autoTradeGubun = self.autoTradeGubunComboBox.currentText()
        if check == 1:
            autoTradeCondition = dm.DataModel.AutoTradeConditionInfo(startTime, endTime, code, name, autoTradeGubun)
            self.myModel.autoTradeConditionList.append(autoTradeCondition)
            self.updateAutoTradeConditionTable()

    def removeAutoTradeCondition(self):
        print("조건식 제거 함수")
        check = 0
        for rowIndex in range(self.autoTradeConditionTableWidget.rowCount()):
            for colIndex in range(self.autoTradeConditionTableWidget.columnCount()):
                if self.autoTradeConditionTableWidget.item(rowIndex, colIndex).isSelected():
                    check = 1
                    del self.myModel.autoTradeConditionList[rowIndex]
                    break
                if check == 1:
                    break

        self.updateAutoTradeConditionTable()

        '''
                    code = self.autoTradeConditionTableWidget.item(rowIndex, 2).text()
                    # 데이터 삭제
                    for itemIndex in range(len(self.myModel.autoTradeConditionList)):
                        # 리스트와 선택한 화면의 코드번호가 일치한 경우
                        if self.myModel.autoTradeConditionList[itemIndex].code == code:
                            del self.myModel.autoTradeConditionList[itemIndex]
                            break
                    for rowIndex in range(self.autoTradeConditionTableWidget.rowCount()):
                        # 화면에 들어간 코드번호와 일치한 경우
                        if self.autoTradeConditionTableWidget.item(rowIndex, 2).text() == code:
                            self.autoTradeConditionTableWidget.removeRow(rowIndex)
                            break
                break
            if check == 1:
                break
        '''

    def updateAutoTradeConditionTable(self):
        column_head = ["시작시간", "종료시간", "조건식번호", "조건식이름", "자동매매상태"]
        colCount = len(column_head)
        rowCount = len(self.myModel.autoTradeConditionList)
        self.autoTradeConditionTableWidget.setColumnCount(colCount)  # 열
        self.autoTradeConditionTableWidget.setRowCount(rowCount)  # 행
        self.autoTradeConditionTableWidget.setHorizontalHeaderLabels(column_head)  # 헤더 삽입
        self.autoTradeConditionTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 수정 방지

        for index in range(rowCount):
            self.autoTradeConditionTableWidget.setItem(index, 0,
                                                       QTableWidgetItem(str(self.myModel.autoTradeConditionList[
                                                                                index].startTime.toString())))
            self.autoTradeConditionTableWidget.setItem(index, 1,
                                                       QTableWidgetItem(str(self.myModel.autoTradeConditionList[
                                                                                index].endTime.toString())))
            self.autoTradeConditionTableWidget.setItem(index, 2,
                                                       QTableWidgetItem(
                                                           str(self.myModel.autoTradeConditionList[index].code)))
            self.autoTradeConditionTableWidget.setItem(index, 3,
                                                       QTableWidgetItem(
                                                           str(self.myModel.autoTradeConditionList[index].name)))
            self.autoTradeConditionTableWidget.setItem(index, 4,
                                                       QTableWidgetItem(str(
                                                           self.myModel.autoTradeConditionList[index].autoTradeGubun)))

    def conditionSearch(self):
        print("조건검색시작 버튼 함수")

        # text = self.conditionSearchPushBox.text()
        # print(text)
        # if text == "조건검색시작":
        #     self.conditionSearchPushBox.setText("중      지")
        # elif text == "중      지":
        #     self.conditionSearchPushBox.setText("조건검색시작")

        if self.boolCondition == 0:
            self.conditionSearchPushBox.setText("조건검색종료")
            self.boolCondition = 1
        else:
            # 시작 상태 체크 후 (종료 -> 시작)
            self.conditionSearchPushBox.setText("조건검색시작")
            self.boolCondition = 0

        # 조건식 검색 테이블을 통해 조건번호, 조건이름 호출
        # row 마다 SendConditionStop() 호출
        for rowIndex in range(self.autoTradeConditionTableWidget.rowCount()):

            code = self.autoTradeConditionTableWidget.item(rowIndex, 2).text()
            name = self.autoTradeConditionTableWidget.item(rowIndex, 3).text()

            # 조건 검색 시작시
            # self.boolCondition 여부에 따라 처리 방안이 다름
            if self.boolCondition == 1:
                # row마다 lRet =  SendCondition() 함수 호출 -> OnReceiveTrCondition() 이벤트 발생
                # -> CommKwRqData() 함수를 통해 관심종목데이터(OPTKWFID)tr
                # BSTR  strScrNo : 화면번호, BSTR strConditionName : 조건식 이름 , int nIndex 조건식 고유번호,
                # int nSearch   // 실시간옵션. 0:조건검색만, 1:조건검색+실시간 조건검색
                strScrNo = 7000 + (rowIndex * 100)
                lRet = self.kiwoom.dynamicCall("SendCondition(QString, QString, int, int)", str(strScrNo), name, code,
                                               0)
                # 화면번호 기준으로 종목 (7000 + rowIndex * 100)
                if lRet == 1:
                    print("조건검색정보요청 성공 - ", name)
                    # 아래와 같이 딕셔너리 형태로 만드는 이유?
                    # 데이터가 많기 때문에 키 밸류 형태로 저장
                    self.myModel.conditionItemList[name] = []
                else:
                    print("조건검색정보요청 실패 - ", name)

            else:
                # BSTR  strScrNo : 화면번호, BSTR strConditionName : 조건식 이름 , int nIndex 조건식 고유번호

                strScrNo = 7000 + (rowIndex * 100)
                self.kiwoom.dynamicCall("SendConditionStop(QString, QString, int)", strScrNo, name, code)
                # 화면번호 기준으로 종목 (7000 + rowIndex * 100)
                # row 마다 SendConditionStop() 호출

            time.sleep(0.5)  # 1초에 5번 이상 호출되면 안되기 때문에 슬립을 준다.

    def autoTrade(self):
        print("자동매매시작 버튼 함수")

        # text = self.autoTradePushBox.text()
        # print(text)
        # if text == "자동매매시작":
        #     self.autoTradePushBox.setText("중      지")
        # elif text == "중      지":
        #     self.autoTradePushBox.setText("자동매매시작")

        if self.boolCondition == 0:
            self.autoTradePushBox.setText("자동매매종료")
            self.boolCondition = 1
        else:
            self.autoTradePushBox.setText("자동매매시작")
            self.boolCondition = 0


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyBot()
    myApp.show()
    app.exec()

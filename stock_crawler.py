import re
import json
import time
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta


class Stockfeeder_TW:
    def _get_market_info(self):
        headers = {"Referer": "https://mis.twse.com.tw/stock/twse_chart.html"}
        text = requests.get(
            "https://www.twse.com.tw/rsrc/data/zh/home/summary.json", headers=headers
        ).text
        market = json.loads(text)
        market_info = {}
        market_info["加權指數"] = market["TSE_I"]
        market_info["加權漲跌"] = market["TSE_D"]
        market_info["加權漲跌幅"] = market["TSE_P"]
        market_info["成交金額"] = market["TSE_V"]
        market_info["櫃買指數"] = market["OTC_I"]
        market_info["櫃買漲跌"] = market["OTC_D"]
        market_info["櫃買漲跌幅"] = market["OTC_P"]
        return market_info

    def _get_volume_top5_data(self):
        volume = requests.get(
            "https://www.twse.com.tw/exchangeReport/MI_INDEX20?response=json"
        ).text
        volume = json.loads(volume)
        stock_infos = []
        for stock in volume["data"][:5]:
            stock_info = {}
            stock_info["number"] = stock[1]
            stock_info["name"] = stock[2]
            stock_info["price"] = stock[8]
            stock_info["volume"] = str(int(stock[3].replace(",", "")) // 1000)
            stock_infos.append(stock_info)
        return stock_infos

    def _get_major_institutions(self):
        today = (datetime.now() + timedelta(days=0)).strftime("%Y%m%d")
        text = requests.get(
            f"https://www.twse.com.tw/fund/BFI82U?response=json&dayDate={today}"
        ).text
        institutions = json.loads(text)
        if institutions["stat"] == "OK":
            major_institutions = institutions["data"]
            got_date = True
            return major_institutions
        else:
            raise ValueError("ins_data haven't updated yet.")

    def _get_three_institutional_info(self):
        today = (datetime.now() + timedelta(days=0)).strftime("%Y%m%d")
        text = requests.get(
            f"https://www.twse.com.tw/fund/T86?response=json&date={today}&selectType=ALL"
        ).text
        data = json.loads(text)
        stock_infos = []
        for stocks in data["data"]:
            stock_info = {}
            stock_info["number"] = stocks[0]
            stock_info["name"] = stocks[1].strip()
            stock_info["foreign"] = int(stocks[4].replace(",", "")) // 1000
            stock_info["trust"] = int(stocks[10].replace(",", "")) // 1000
            stock_info["dealer"] = int(stocks[11].replace(",", "")) // 1000
            stock_infos.append(stock_info)
        three_ins_infos = {}
        for ins in ["foreign", "trust", "dealer"]:
            three_ins_info = []
            head3 = sorted(stock_infos, key=lambda x: x[ins], reverse=True)[:3]
            tail3 = sorted(stock_infos, key=lambda x: x[ins], reverse=False)[:3]
            three_ins_info.append(head3)
            three_ins_info.append(tail3)
            three_ins_infos[ins] = three_ins_info
        return three_ins_infos

    def _get_sectors(self):
        headers = {"referer": "https://histock.tw/globalchart.aspx?m=tw"}
        text = requests.get(
            "https://histock.tw/stock/module/StockData.aspx?m=class&g=6",
            headers=headers,
        ).text
        stock_info = json.loads(text)
        sectors = ast.literal_eval(stock_info["Class"])
        pattern = r"y:(-*\d.\d+)"
        risings = re.findall(pattern, stock_info["Ratio"])
        pattern = r"url:'/twclass/([A-Z].\d+)"
        url = re.findall(pattern, stock_info["Ratio"])
        top_five_sectors = []
        idx = 0
        while len(top_five_sectors) < 5:
            if "不含" in sectors[idx] or "其他" in sectors[idx]:
                pass
            else:
                single_sector = {}
                single_sector["sectors_name"] = sectors[idx]
                single_sector["rising"] = str(round(float(risings[idx]), 2)) + "%"
                single_sector["url"] = url[idx]
                top_five_sectors.append(single_sector)
            idx += 1
        return top_five_sectors

    def _get_sectors_top3(self, sectors_number):
        headers = {"referer": "https://histock.tw/tw"}
        text = requests.get(
            f"https://histock.tw/stock/module/StockData.aspx?m=classstock&cid={sectors_number}",
            headers=headers,
        ).text
        soup = BeautifulSoup(text, "html.parser")
        number = soup.select("div.fixW40")
        name = soup.select("div.fixW70")
        prices = soup.select("span")
        infos = []
        if number and name and prices:
            for idx in range(3):
                info = []
                info.append(number[idx].text)
                info.append(name[idx].text)
                info.append(prices[5 * idx].text)
                info.append(prices[5 * idx + 1].text)
                info.append(prices[5 * idx + 2].text)
                info.append(prices[5 * idx + 3].text)
                infos.append(info)
        else:
            infos.append([" "] * 6)
        return infos

    def three_ins_output_writer(self):
        major_ins = self._get_major_institutions()
        institutionals = self._get_three_institutional_info()
        sectors = self._get_sectors()
        output = self._three_ins_template_maker(major_ins, institutionals, sectors)
        return output

    def _deal_percent(self, buy, sell, total):
        buy = float(buy.replace(",", ""))
        sell = float(sell.replace(",", ""))
        total = total * 100000000
        return str(round((buy + sell) / total / 2 * 100, 2))

    def _three_ins_template_maker(self, major_ins, institutionals, sectors):
        ins_trans = {"foreign": "✈️ 外資", "trust": "🏦 投信", "dealer": "🏭 自營商"}
        output = f"⚙️ 三大法人買賣金額統計 (億元) ⚙️ \n"
        output += f"(單位名稱 / 買進金額 / 賣出金額 / 買賣差額) \n\n"
        for single_major in major_ins:
            output += f"{single_major[0]} / {self._trans_billion(single_major[1])} / {self._trans_billion(single_major[2])} / {self._add_plus(self._trans_billion(single_major[3]))}\n"
        market_number = self._get_market_info()["成交金額"]
        output += f"\n三大法人成交比重 : {self._deal_percent(major_ins[-1][1], major_ins[-1][2], market_number)} %\n\n\n"
        output += f"\n📢 三大法人買賣超 TOP 3 \n"
        for ins in institutionals:
            output += f"\n{ins_trans[ins]} (代號 / 股名 / 買賣超(張))\n買超 TOP 3 :\n"
            for data in institutionals[ins][0]:
                output += f'{data["number"]} / {data["name"]} / {data[ins]}\n'
            output += f"\n賣超 TOP 3 :\n"
            for data in institutionals[ins][1]:
                output += f'{data["number"]} / {data["name"]} / {data[ins]}\n'
        return output

    def market_output_writer(self):
        market_info = self._get_market_info()
        volume = self._get_volume_top5_data()
        sectors = self._get_sectors()
        output = self._market_template_maker(market_info, volume, sectors)
        return output

    def _market_template_maker(self, market_info, volume, sectors):
        output = f"⚙️ 大盤收盤統計 ⚙️ \n\n"
        output += f'📌 加權指數\n{market_info["加權指數"]} / {market_info["加權漲跌"]}({market_info["加權漲跌幅"]}%)\n'
        output += f'📌 櫃買指數\n{market_info["櫃買指數"]} / {market_info["櫃買漲跌"]}({market_info["櫃買漲跌幅"]}%)\n'
        output += f'📌 台股成交金額\n{market_info["成交金額"]} 億\n'
        output += "\n\n💰 交易量 TOP 5 \n(代號 / 股名 / 收盤價 / 交易量(張)) :\n"
        for stock in volume:
            output += f'{stock["number"]} / {stock["name"]} / {stock["price"]} / {stock["volume"]}\n'
        output += "\n\n🔥 今日熱門概念股 TOP 5\n"
        output += "(代號 / 名稱 / 成交價 / 漲跌 / 漲跌幅)\n"
        for sec in sectors:
            output += f'\n🎫{sec["sectors_name"]} / {sec["rising"]}\n'
            for stock_prices in self._get_sectors_top3(sec["url"]):
                output += f"{stock_prices[0]} / {stock_prices[1]} / {stock_prices[2]} / {stock_prices[3]} / {stock_prices[4]}\n"
        return output

    def _trans_billion(self, number):
        number = int(number.replace(",", ""))
        return round(number / 100000000, 2)

    def _add_plus(self, number):
        if "-" not in str(number):
            return "+" + str(number)
        return number


if __name__ == "__main__":
    stock = Stockfeeder_TW()
    market = stock.market_output_writer()
    investor = stock.three_ins_output_writer()
    print(market)
    print("*" * 100)
    print(investor)

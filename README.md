# TW_stock_info
爬取每日台股資訊(大盤資訊、三大法人資訊)的爬蟲程式。

![alt text](https://i.imgur.com/W4vDIf2.png)

## stock_crawler.py
* 無需輸入變數，在每日收盤時間後(大盤資訊約 15:00/三大法人資訊約 16:00)啟用即可爬取該日股市資訊。
* 回傳值為字串形式，如附圖。

## Requirements
python 3

## Usage

```
if __name__ == "__main__":
    stock = Stockfeeder_TW()
    market = stock.market_output_writer()
    investor = stock.three_ins_output_writer()
    print(market)
    print(investor)

```
## Installation
`pip install -r requriements.txt`。

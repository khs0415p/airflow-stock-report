from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from airflow.exceptions import AirflowException
from .urls import HKurl
import pandas as pd
import FinanceDataReader as fdr
import numpy as np
import pendulum
import logging
import MySQLdb
import os

HOST = os.environ.get("MYSQL_HOST")
USER = "root"
PORT = os.environ.get("MYSQL_PORT", 3306)
PASSWORD = os.environ.get("MYSQL_ROOT_PASSWORD", "root")
DATABASE = os.environ.get("MYSQL_DATABASE", 'crawling')


def crawling(**context):    
    
    logical_date = pendulum.parse(context['ds'])
    start_date = logical_date.strftime("%Y-%m-%d")
    end_date = (logical_date + timedelta(days=7)).strftime("%Y-%m-%d")
    
    # firefox 웹페이지 접속
    
    service = Service("/usr/bin/geckodriver")
    options = Options()
    options.binary_location = "/usr/bin/firefox"
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(HKurl(start_date, end_date)) # 오류출력 고치기

    #   CRAWLING
    Report_arr = None    # 결과담을 리스트
    page = 1
    while True:
        #   해당 페이지 모든 리포트
        allReportElement = driver.find_elements(By.CSS_SELECTOR, '#contents > div.table_style01 > table > tbody > tr')

        #   마지막 페이지 > 종료
        if (len(allReportElement)==0):
            driver.quit()
            break

        #   report text 가져오기
        body = driver.find_elements(By.CSS_SELECTOR, '#contents > div.table_style01 > table > tbody> tr > td')
        body_text = [b.text for b in body]
        body_arr = np.array(body_text).reshape((-1, 9))

        #   합치기
        if Report_arr is not None:
            Report_arr = np.concatenate([Report_arr, body_arr])
        else:
            Report_arr = body_arr.copy()
        
        # verbose
        logging.info(f'\rpage {page} {"■"*page}')
        
        # next page
        page +=1
        # url = HKurl(start_date, end_date, page=page, analyst_quoted=(analyst_quoted if analyst!="" else ""))    # 오류 출력되는 부분
        url = HKurl(start_date, end_date, page=page, analyst_quoted="")
        driver.get(url)
    
    # AirflowException
    if Report_arr is None:
        raise AirflowException("검색 결과가 없습니다.")
    
    #   PREPROCESSING
    df = pd.DataFrame(Report_arr)
    df.drop(columns=[6, 7, 8], inplace=True)
    logging.info(df.info())
    df.columns = ['reporting_date', 'title', 'target_price', 'opinion', 'analyst', 'provider']

    # 종목명, 종목코드 추가 및 타이틀 수정
    df[['name', 'ticker']] = df.title.str.extract('(.+)\((\s*\d{6}\s*)\)')
    df.loc[df.ticker.isnull(), ['name', 'ticker']] = df.title[df.ticker.isnull()].str.extract('([^\s\d]+)(\d{6})').values   # {종목명}({종목코드}) 의 형식일 경우

    # DROP
    logging.info('\n===================Non Ticker DROP=====================\n')
    logging.info(df[df.ticker.isnull()])
    df.drop(index=df[df.ticker.isnull()].index, inplace=True)
    
    logging.info('\n===================Non TargetPrice DROP=====================\n')
    logging.info(df[df.target_price=='0'])
    df.drop(index=df[df.target_price=='0'].index, inplace=True)
    
    # 당일 종가 추가
    get_close_price = lambda x: fdr.DataReader(*x[['ticker','reporting_date', 'reporting_date']])['Close'][0]
    df['close_price'] = df.apply(get_close_price, axis=1)
    
    # 데이터타입 변환
    df.reporting_date = pd.to_datetime(df.reporting_date)
    df.target_price = df.target_price.str.replace(',', '').astype(int)
    

    # 당일 종가 없는 것 체크
    logging.info('\n===================Non Close Price=====================\n')
    for x in df[['ticker', 'reporting_date', 'title']].values:
        if fdr.DataReader(*x[[0,1,1]]).shape[0]==0:
            logging.info(x)

    # SAVE
    df = df[['reporting_date', 'provider', 'analyst', 'name', 'ticker', 'close_price', 'target_price', 'opinion', 'title']]
    logging.info("Saving crawling data..")
    
    db_conn = MySQLdb.connect(host=HOST, port=PORT, user=USER,
                  password=PASSWORD, database=DATABASE)
    db_cursor = db_conn.cursor()
    
    for _, row in df.iterrows():
        exist_query = f"SELECT EXISTS ( \
                    SELECT 1 FROM tickers as t WHERE t.name='{row['name']}')"
        db_cursor.execute(exist_query)
        flag = db_cursor.fetchone()[0]
        if not flag:
            query = f"INSERT INTO tickers VALUES ('{row['name']}', '{row['ticker']}')"
            db_cursor.execute(query)
        
        exist_query = f"SELECT EXISTS ( \
                    SELECT * FROM stock as s WHERE s.reporting_date='{row['reporting_date']}' and s.analyst='{row['analyst']}' and s.name='{row['name']}')"
        db_cursor.execute(exist_query)
        flag = db_cursor.fetchone()[0]
        if not flag:
            query = f"INSERT INTO stock (reporting_date, provider, analyst, name, close_price, target_price, opinion, title) \
                VALUES ('{row['reporting_date']}', '{row['provider']}', '{row['analyst']}', '{row['name']}', '{row['close_price']}', '{row['target_price']}', \
                    '{row['opinion']}', '{row['title']}')"
            db_cursor.execute(query)
        
    db_conn.commit()
    db_conn.close()
    logging.info("Completed")
    
if __name__=="__main__":
    crawling()
from selenium import webdriver
from selenium.webdriver.common.by import By
import gspread as gs
import pandas as pd
import os
from time import sleep
import urllib

API_KEY = "";
SCRAPING_URL = "https://chiebukuro.yahoo.co.jp/"

class SpreadSheet:
	spreadsheet_key = "";
	myspreadsheet = None;
	def __init__(self, SPREADSHEET_KEY: str):
		gclient = gs.oauth();
		self.spreadsheet_key = SPREADSHEET_KEY;
		self.myspreadsheet = gclient.open_by_key(SPREADSHEET_KEY);

class WorkSheet:
	myworksheet = None;
	mydataframe = None;
	def __init__(self, id: int, spreadsheet: SpreadSheet):
		self.myworksheet = spreadsheet.myspreadsheet.get_worksheet(id);
		self.mydataframe = pd.DataFrame(self.myworksheet.get_all_records());

class Scraper:
	driver = webdriver.Chrome();
	search_text = "hoge";
	scraping_url = SCRAPING_URL;

	def __init__(self, text: str):
		self.search_text = text;
		self.driver.get(SCRAPING_URL);

	def scrape_execute(self, ws: WorkSheet, url_keys: set, userid_keys: set) -> None: #参照渡し
		records = [];
		# 検索
		search_box = self.driver.find_element(By.CLASS_NAME, 'SearchBox_searchBox__inputBoxInput__nf3fq');
		search_box.send_keys(self.search_text);
		sleep(3);
		self.driver.find_element(By.XPATH, '//*[@id="Top"]/div/div[1]/div[2]/nav/div[1]/div/div/button').click();
		"""
		search_button = self.driver.find_element(By.CLASS_NAME, 'cl-noclick-log SearchBox_searchBox__inputButton__2OXXW')
		search_button = search_button_container.find_element(By.CSS_SELECTOR, 'input')
		search_button.click()
		"""
		sleep(3)
		page = 0;
		while True:
			page+= 1;
			try:
				results = self.driver.find_element(By.ID, "sr").find_elements(By.TAG_NAME, "h3");
			except Exception as e:
				return;
			for element in results:
				a_elem = element.find_element(By.TAG_NAME, "a");
				href = a_elem.get_attribute("href");
				href = href.split("?")[0];

				if href in url_keys:
					continue;
				text_content = a_elem.text;

				self.driver.execute_script("window.open()");
				self.driver.switch_to.window(self.driver.window_handles[1]);
				self.driver.get(href);
				
				area_questioner = self.driver.find_element(By.CSS_SELECTOR, "a[class^=ClapLv1UserInfo_Chie-UserInfo]");
				question_date = area_questioner.find_element(By.CSS_SELECTOR, "p[class^=ClapLv1UserInfo_Chie-UserInfo__Date]").text;
				user_name = area_questioner.find_element(By.CSS_SELECTOR, "p[class^=ClapLv1UserInfo_Chie-UserInfo__UserName]").text[:-2];
				user_page_url = area_questioner.get_attribute("href");
				if user_page_url is None:
					continue;
				self.driver.get(user_page_url);
				profile = self.driver.find_element(By.ID, "my_prof");
				user_id = self.driver.find_element(By.CSS_SELECTOR, "p[class^=ClapLv2MyProfile_Chie-MyProfile__Uid]").text.split("：")[-1];
				record = [question_date, href, text_content, "", user_name, user_id];
				
				self.driver.execute_script("window.close()");
				self.driver.switch_to.window(self.driver.window_handles[0]);
				sleep(3);

				if user_id not in userid_keys:
					continue;
				else:
					print(*record);
					ws.myworksheet.append_row(record);
					url_keys.add(record[1]);
					userid_keys.add(record[-1]);

			
			new_page = "b={}".format(10*page+1);
			current_page = "b={}".format(10*(page-1)+1);
			currenturl = self.driver.current_url;
			if 1<page:
				self.driver.get(currenturl.replace(current_page, new_page));
			else:
				self.driver.get(currenturl+"&{}".format(new_page));


def main():
	SPREADSHEET_KEY = input("INPUT SPREADSHEET KEY");
	ss = SpreadSheet(SPREADSHEET_KEY);
	ws = WorkSheet(0, ss);
	url_keys = set(ws.myworksheet.col_values(2)[1:]); #URLをキーとする
	userid_keys = set(ws.myworksheet.col_values(6)[1:]);
	"""
	for key in keys:
		print(key);
	exit();
	"""
	while True:
		search_text = input("INPUT SEARCH WORDS");
		if search_text == "":
			break;
		Scraper(search_text).scrape_execute(ws, url_keys, userid_keys);



if __name__ == "__main__":
	main();
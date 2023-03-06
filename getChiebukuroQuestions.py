from selenium import webdriver
from selenium.webdriver.common.by import By
import gspread as gs
import pandas as pd
from time import sleep
import os

SCRAPING_URL = "https://chiebukuro.yahoo.co.jp/search"

GENRE_TXT = """
	ALL GENRE -> JUST PRESS ENTER KEY
	Hobbies and Entertainment -> 2078297513
		Gaming -> 2078297514
			Dragon Quest -> 2080401137
			Final Fantasy -> 2080401134
			Video Games -> 2078297516
			PlayStation 4 -> 2080306361
	Computer Technology -> 2078297616
		Programming -> 2078297622
			C: Programming Language -> 2078297650
	Personal Computer -> 2080401529
	Human Life -> 2079526977
		Love Affair -> 2078675272
		Life Style -> 2079526980
	Life Style Guidlines -> 2078297937
		Dish -> 2078297945
	Others -> 2078297354
		Adult -> 2078297371
	Careers -> 2078297897
		Job Hunt -> 2078297901
	School and Education -> 2078297878
		Higher Education -> 2078297882
	Sports, Outdoor activities and Cars -> 2078297753
		Sports -> 2078297757
		Cars -> 2078297760
	Health, Beauty, and Fashion -> 2078297854
		Fashion -> 2078297856
""" 

SORT_TXT = """
	related: JUST PRESS ENTER KEY
	ASC: 21
	DEC: 20
	least visited: 7
"""

class SpreadSheet:
	gclient = None;
	def __init__(self, SPREADSHEET_KEY: str):
		self.gclient = gs.oauth();
		#self.gclient = gs.service_account();

		self.spreadsheet_key = SPREADSHEET_KEY;
		self.myspreadsheet = self.gclient.open_by_key(SPREADSHEET_KEY);

class WorkSheet:
	def __init__(self, id: int, spreadsheet: SpreadSheet):
		self.myworksheet = spreadsheet.myspreadsheet.get_worksheet(id);
		##self.mydataframe = pd.DataFrame(self.myworksheet.get_all_records());

	def col_values(self, i: int) -> list:
		return self.myworksheet.col_values(i);

class URLBuilder:
	class Chiebukuro_Params(dict):
		def set_next_page(self):
			next_page = int(self["b"]) + 10;
			self["b"] = str(next_page);

	url = "";
	params = Chiebukuro_Params();
	def __init__(self, s: str, cp: Chiebukuro_Params):
		self.url = s;
		self.params = cp;
	def build(self) -> str:
		ret = self.url + "?";
		for it in self.params.items():
			ret += it[0] + "=" +  it[1] + "&";
		return ret[:-1];


class Scraper:
	class History(set):
		def __init__(self):
			os.makedirs("data", exist_ok=True);
			try:
				with open("data/checked.txt", mode='x') as f:
					pass;
			except FileExistsError:
				pass;
				
			with open("data/checked.txt", mode='r', encoding="utf-8") as f:
				super().__init__([s.strip() for s in f]);

	class Nomenclature(set):
		COLUMN_NO = 6;
		def __init__(self, ws: WorkSheet):
			column_no = self.COLUMN_NO;
			super().__init__(ws.col_values(column_no)[1:]);

	class URL_Set(set):
		COLUMN_NO = 2;
		def __init__(self, ws: WorkSheet):
			column_no = self.COLUMN_NO;
			super().__init__(ws.col_values(column_no)[1:]);

	driver = webdriver.Chrome();
	search_text = "hoge";
	scraping_url = SCRAPING_URL;

	def __init__(self, text: str):
		self.search_text = text;
		self.driver.get(SCRAPING_URL);

	def scrape_execute(self, params: dict, ws: WorkSheet, url_keys: set, userid_keys: set, checked: set, dbg=False) -> None: #参照渡し
		page = 0;
		
		## 検索結果がなくなるまで取得
		while page < 100:
			url = URLBuilder(SCRAPING_URL, params).build();
			print("URLBuild Success: {}".format(url));
			self.driver.get(url);
			page+= 1;
			try:
				results = self.driver.find_element(By.ID, "sr").find_elements(By.TAG_NAME, "h3");
			except Exception as e:
				if dbg: print(e);
				return;
			## 検索結果訪問
			for element in results:
				a_elem = element.find_element(By.TAG_NAME, "a");
				href = a_elem.get_attribute("href");
				href = href.split("?")[0];

				if href in url_keys:
					if dbg: print("href in url_keys!");
					continue;
				q = href.split('/')[-1];
				if q in checked:
					if dbg: print("already checked!");
					continue;
				else:
					checked.add(q);
					with open("data/checked.txt", mode='a', encoding="utf-8", newline="\n") as f:
						f.write(q+"\n");

				text_content = a_elem.text;

				self.driver.execute_script("window.open()");
				sleep(1);
				self.driver.switch_to.window(self.driver.window_handles[1]);
				self.driver.get(href);
				area_questioner = None;
				
				try:
					area_questioner = self.driver.find_element(By.CSS_SELECTOR, "a[class^=ClapLv1UserInfo_Chie-UserInfo]");
				except:
					#ID非公開 -> NoSuchElementException を回避
					self.driver.execute_script("window.close()");
					sleep(1);
					self.driver.switch_to.window(self.driver.window_handles[0]);
					continue;

				question_date = area_questioner.find_element(By.CSS_SELECTOR, "p[class^=ClapLv1UserInfo_Chie-UserInfo__Date]").text;
				user_name = area_questioner.find_element(By.CSS_SELECTOR, "p[class^=ClapLv1UserInfo_Chie-UserInfo__UserName]").text[:-2];

				user_page_url = area_questioner.get_attribute("href");

				self.driver.get(user_page_url);
				profile = self.driver.find_element(By.ID, "my_prof");
				user_id = self.driver.find_element(By.CSS_SELECTOR, "p[class^=ClapLv2MyProfile_Chie-MyProfile__Uid]").text.split("：")[-1];
				record = [question_date, href, text_content, "", user_name, user_id];
				
				self.driver.execute_script("window.close()");
				self.driver.switch_to.window(self.driver.window_handles[0]);
				sleep(1);

				## 確認済み質問者IDと一致するならば、表を更新する
				if user_id not in userid_keys:
					continue;
				else:
					print(*record);
					ws.myworksheet.append_row(record, value_input_option="USER_ENTERED");
					ws.myworksheet.format("A{}".format(len(ws.myworksheet.col_values(1))), {"numberFormat": {"type": "DATE"}})
					url_keys.add(record[1]);
					userid_keys.add(record[-1]);

			## ページング処理
			params.set_next_page();


def main():	
	visited = Scraper.History();
	spreadsheet_key = input("INPUT SPREADSHEET KEY");
	ss = SpreadSheet(spreadsheet_key);
	ws = WorkSheet(0, ss);
	url_keys = Scraper.URL_Set(ws);
	userid_keys = Scraper.Nomenclature(ws);
	while True:
		ws.myworksheet.sort((1, 'asc'), (2, 'asc'));
		search_text = input("INPUT SEARCH WORDS");
		search_genre = input("INPUT SEARCH GENRE\n" + GENRE_TXT);
		search_sort = input("INPUT IN WHAT WAY SORT\n" + SORT_TXT);
		params = URLBuilder.Chiebukuro_Params(p=search_text, dnum=search_genre, b="1", sort=search_sort);
		print("if you want to get out of the process, press [Ctrl+C].")
		Scraper(search_text).scrape_execute(params, ws, url_keys, userid_keys, visited);



if __name__ == "__main__":
	main();

# To run the script you need to:
# 1. Python>3.8
# 2. pip install selenium
# 3. Have Chromedriver in the same path in a version compatible
#    with your installed chrome browser:
#    https://sites.google.com/a/chromium.org/chromedriver/downloads
# 4. Set your username & password, don’t forget file_title
# 5. python <this-script>
import os
from datetime import date, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SpringAheadCrawler:
    company_login = os.environ["SPRINGAHEAD_COMPANY"]
    username = os.environ["SPRINGAHEAD_USERNAME"]
    password = os.environ["SPRINGAHEAD_PASSWORD"]
    file_title = os.environ["SPRINGAHEAD_FILETITLE"]
    no_of_weeks_backward = 4
    headless = True

    def __init__(self):
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--width=1080")
        options.add_argument("--height=1440")
        # options.add_argument("--window-size=1080,1920")

        # self.driver = webdriver.Chrome(
        #     executable_path=os.path.abspath("/home/maciej/Documents/chromedriver"), options=options
        # )
        self.driver = webdriver.Firefox(
            executable_path="/home/maciej/Documents/blackstone/geckodriver",
            options=options,
        )
        self.driver.implicitly_wait(10)

    def login(self):
        self.driver.get("https://my.springahead.com/")

        search_field = self.driver.find_element_by_id("CompanyLogin")
        search_field.clear()
        search_field.send_keys(self.company_login)

        search_field = self.driver.find_element_by_id("UserName")
        search_field.clear()
        search_field.send_keys(self.username)

        search_field = self.driver.find_element_by_id("Password")
        search_field.clear()
        search_field.send_keys(self.password)

        search_field.send_keys(Keys.ENTER)

    def daterange(self, date1, date2):
        for n in range(0, int((date2 - date1).days) + 1, 7):
            yield date1 + timedelta(days=n)

    def generate_weeks(self):
        end_dt = date.today()
        end_dt = end_dt - timedelta(days=end_dt.weekday())
        start_dt = end_dt - timedelta(weeks=self.no_of_weeks_backward)
        weeks = []
        for dt in self.daterange(start_dt, end_dt):
            weeks.append((dt, dt + timedelta(days=6)))
        return weeks

    def request_report(self, monday, sunday, include_unapproved=False):
        self.driver.find_element_by_link_text("Reports").click()
        self.driver.find_element_by_link_text("Time by Employee").click()
        search_field = self.driver.find_element_by_name("Rpt_Date_Start")
        search_field.clear()
        search_field.send_keys(monday.strftime("%m/%d/%Y"))
        search_field = self.driver.find_element_by_name("Rpt_Date_Stop")
        search_field.clear()
        search_field.send_keys(sunday.strftime("%m/%d/%Y"))
        if include_unapproved:
            search_field = self.driver.find_element_by_name(
                "Rpt_Include_Unapproved"
            ).click()
            unnapproved_tag = "_incl_unapproved"
        else:
            unnapproved_tag = ""
        search_field = self.driver.find_element_by_name("operation").click()

        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_all_elements_located((By.ID, "subjectbar_right"))
        )
        mstr = monday.strftime("%#d_%b_%Y").lower()
        sstr = sunday.strftime("%#d_%b_%Y").lower()
        filename = f"{self.file_title}_BX_report_{mstr}_{sstr}{unnapproved_tag}.png"
        self.driver.save_screenshot(filename)

        report_tables = self.driver.find_elements_by_class_name("report_table")
        sth = report_tables[-1].find_element_by_css_selector(
            "tbody tr:last-child td:last-child"
        )
        return int(sth.text.strip())

    def request_monthly_view(self):
        self.driver.find_element_by_link_text("Time").click()
        day = date.today()
        sstr = day.strftime("%b_%Y").lower()
        filename = f"{self.file_title}_BX_report_{sstr}_overview.png"
        self.driver.save_screenshot(filename)

        self.driver.find_element_by_id("PrevMonth").click()
        day = date.today() - timedelta(days=30)
        sstr = day.strftime("%b_%Y").lower()
        filename = f"{self.file_title}_BX_report_{sstr}_overview.png"
        self.driver.save_screenshot(filename)

    def get_screenshots(self):
        # Report for the whole prev. month
        day = date.today()
        total = self.request_report(day.replace(day=1), day, include_unapproved=True)
        print(f"{day}: {total}")

        prev_month = day.replace(day=1) - timedelta(days=1)
        total = self.request_report(prev_month.replace(day=1), prev_month)
        print(f"{prev_month}: {total}")

        # Get week by week
        self.request_monthly_view()
        for week in self.generate_weeks():
            (monday, sunday) = week
            print(monday, sunday)
            self.request_report(monday, sunday)

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    sac = SpringAheadCrawler()
    sac.login()
    sac.get_screenshots()
    sac.close()

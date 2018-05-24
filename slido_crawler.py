# -- coding: utf-8 -- –
import os, sys, getopt
import csv
import datetime, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote, urljoin
from lxml import etree
import re

def createBrowserFirefox():
    driver = webdriver.Firefox()
    driver.implicitly_wait(600)
    driver.set_page_load_timeout(600)
    return driver

def openUrlWithRetry(driver, url, retry):
    countRetry = retry
    while True:
        try:
            driver.get(url)
        except Exception as ex:
            print(ex)
            print("Timeout, retrying...")
            countRetry-=1
            if countRetry <= 0:
                print("Maximum number of retry reached")
                break
            time.sleep(30)
            continue
        else:
            break
    return countRetry

def questionCrawler(url):
    #url = "https://app2.sli.do/event/5ob2deqd/ask"

    driver = createBrowserFirefox()
    openUrlWithRetry(driver, url, 10)
    try:
        content = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//div[@ng-if="vm.questionCount"]/div[@class="h1--content"]')))
        questionCount = int(re.findall(r"([0-9]*?)\s\w", content.text)[0])
        print(questionCount)
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight-100);")
        #driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(5)
    except:
        driver.quit()
        print("ERROR: Fail loading page: {}".format(url))
        return

    questionResult = []

    for i in range(10):
        try:    
            htmlBody = driver.page_source
            html = etree.HTML(htmlBody, base_url=driver.current_url)
            if html == '':
                print("Can't get html...")
                return
        except:
            driver.quit()
            print("ERROR: Fail loading page: {}".format(url))
            return
        
        try:
            questionList = html.xpath('//div[@class="card question-item"]')
            if len(questionList) == 0:
                print("no question")
                return
        except NoSuchElementException:
            print("NoSuchElementException")
            return

        print(len(questionList), " <=> ", questionCount)
        if len(questionList) == questionCount:
            break
        else:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight-50);")
            time.sleep(10)

    for question in questionList:
        questionItem = []
        try:
            author = question.xpath('.//div[contains(@class, "question-item__header")]//span[@class="author__name"]')[0].text
            print(author)
            questionItem.append(author)
        except:
            pass
        try:
            postTime = question.xpath('.//div[contains(@class, "question-item__header")]//div[@class="question-item__date"]')[0].attrib['title']
            print(postTime)
            questionItem.append(postTime)
        except:
            pass
        try:
            score = question.xpath('.//div[contains(@class, "score score--card")]//span')[0].text
            print("score: ", score)
            questionItem.append(score)
        except:
            pass
        try:
            textNode = question.xpath('.//div[contains(@class, "question-item__body")]')[0]
            childNodes = textNode.xpath('.//*')
            text = textNode.text
            for child in childNodes:
                text += child.text
            print(text)
            questionItem.append(text)
        except Exception as e:
            print(e)
            pass    
        questionResult.append(questionItem)
    
    driver.quit()
    return questionResult

def save2Csv(result, eventId):
    outfile = eventId + "_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.csv'
    isExist = os.path.exists(outfile)
    with open(outfile, 'a', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        if not isExist:
            fout.write('\ufeff')
            writer.writerow(["Author", "Post Time", "Like", "Question"])
        for item in result:
            writer.writerow(item)

def main(argv):
    try:
        url = sys.argv[1]
        eventId = re.findall(r"event\/(.*?)\/", url)[0]
        print(eventId)
        result = questionCrawler(url)
        save2Csv(result, eventId)
    except getopt.GetoptError:
        print ('slido_crawler.py <URL>')
        sys.exit(2)

if __name__ == "__main__":
   main(sys.argv[1:])
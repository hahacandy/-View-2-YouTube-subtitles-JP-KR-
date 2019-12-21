# 유튜브의 플레이 리스트에 있는 곡들을 captionpop(자막2개보는사이트) 에서 순차적으로 재생하는 프로그램.
# 자막은 일본어, 한국어 로 설정되어 있다.
# 해당 영상이 일본어 자막만 있고 한국어 자막이 없다면 네이버 파파고 번역기로 번역한다

# client_id, client_secret, play_list_url, ran_play, font_size 변수에 알맞은 값을 설정
# JpSong.py 코드를 한번 실행하면 해당 폴더에 driver, files->dataDir 가 생성됨
# driver 폴더에 자신의 크롬 버전과 맞는 chromedriver.exe 파일을 두고 재실행 하면 됨.

import errno

import json
import urllib

from selenium import webdriver
import os
from bs4 import BeautifulSoup
import requests
import re
import time
import random
from _datetime import datetime

# 아이디가 2개인 이유는 하루 할당량 다 떨어지면 2번째로 교체함
client_id = ""  # 개발자센터에서 발급받은 Client ID 값
client_secret = ""  # 개발자센터에서 발급받은 Client Secret 값

client_id2 = ""  # 개발자센터에서 발급받은 Client ID 값
client_secret2 = ""  # 개발자센터에서 발급받은 Client Secret 값

# 유튜브 플레이 리스트 주소
play_list_url = ""
# 랜덤 재생: True(랜덤재생), False(순차재생)
ran_play = True
# 일본어 폰트 사이즈
font_size = 35


# 일본어 문자열을 한국어로 번역한 뒤 리턴 (네이버 파파고 nmt)
def Translate_JPto_KO(_str_jp):
    global client_id, client_secret
    encText = urllib.parse.quote(_str_jp)
    data = "source=ja&target=ko&text=" + encText
    url = "https://openapi.naver.com/v1/papago/n2mt"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    try:
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            temp = str(response_body.decode('utf-8'))
            json_data = json.loads(temp)['message']['result']['translatedText']
            return json_data
        else:
            # 에러코드
            return "Error Code:" + rescode
    except:
        # api 사용량 다떨어져서 2번째 client_id로 번역하기 위함
        client_id = client_id2
        client_secret = client_secret2
        return "네이버 id 정보 변경"


# 프로그램 사용에 필요한 폴더를 중복 확인 후 없으면 생성
def create_folder():
    try:
        path1 = os.getcwd() + "/driver"
        path2 = os.getcwd() + "/files/dataDir"

        if not os.path.exists(path1):
            os.makedirs(path1)
        if not os.path.exists(path2):
            os.makedirs(path2)

    except OSError as e:
        if e.errno != errno.EEXIST:
            print("Failed to create directory!!!!!")
            raise

    return


# 시간이 10미만 숫자라면 2자리로 변환, 9라면 09로 변환
def changeTime(_time):
    c_time = ''
    if _time < 10:
        c_time = "0" + str(_time)
    else:
        c_time = str(_time)
    return str(c_time)


def get_currentTime_str():
    now = datetime.now()
    current_time = "[" + changeTime(now.hour) + ":" + changeTime(now.minute) + ":" + changeTime(now.second) + \
                   "] "
    return current_time


def driver_set():
    option = webdriver.ChromeOptions()

    # option.add_argument('--headless')

    option.add_argument('--disable-infobars')
    option.add_argument('--window-size=100x100')
    option.add_argument('--disable-gpu')

    chrome_prefs = {}
    option.experimental_options["prefs"] = chrome_prefs

    option.add_argument('--user-data-dir=' + os.getcwd() + '/files/dataDir')

    driver = webdriver.Chrome('./driver/chromedriver', options=option)
    # driver.set_window_size(700, 1000)
    return driver


# 해당 주소의 플레이 리스트의 모든 동영상의 주소를 배열에 담아 리턴함
def getPlaylistLinks(url):
    sourceCode = requests.get(url).text
    soup = BeautifulSoup(sourceCode, 'html.parser')
    links = soup.find_all("a", {"dir": "ltr"})

    play_song_url_array = [[0] * 2 for i in range(len(links) - 1)]

    for idx, link in enumerate(links):
        href = link.get('href')

        pattern = r'/watch\?v=\w+-\w+'
        match = re.match(pattern, href)
        if not match:
            pattern = r'/watch\?v=\w+'
            match = re.match(pattern, href)

        if match:
            s = match.group()
            s = s.replace('/watch?v=', '')
            play_song_url_array[idx - 1][0] = link.get_text()  # 곡 이름
            play_song_url_array[idx - 1][1] = s  # 곡 id

    return play_song_url_array


# 동영상 id를 받아와서 동시 2개 자막 사이트에서 재생하고, 노래 끝나면 리턴됨
def Play(_driver, _url):
    _driver.get(_url)

    # 재생 버튼으로 포커스 이동
    iframes = _driver.find_elements_by_tag_name('iframe')
    _driver.switch_to.frame(iframes[0])
    time.sleep(1)

    # 재생 버튼 클릭
    while True:
        try:
            _driver.find_element_by_xpath("/html/body/div/div/div[4]/button").click()
            time.sleep(1)

        except:
            pass

        try:
            driver.find_element_by_class_name("ytp-play-button").get_attribute('title')
            break
        except:
            pass
        time.sleep(1)

    # 포커스 나옴
    _driver.switch_to.default_content()

    # 일본어 폰트 크기 크게 함
    japan_text_elements = driver.find_elements_by_class_name("subtitle-text")
    for idx, japan_text_element in enumerate(japan_text_elements):
        # 자막이 없으면 작동안함
        try:
            japan_text_element = japan_text_element.find_elements_by_class_name("SubtitleText__BlurredText-axonzm-0")
        except:
            continue
        # 일본어 폰트 크기 40px로 변경
        driver.execute_script("arguments[0].setAttribute('style','font-size:" + str(font_size) + "px')",
                              japan_text_element[0])
        # 한국어 자막 흐림 제거
        driver.execute_script("arguments[0].setAttribute('class','SubtitleText__BlurredText-axonzm-0 hiMIor')"
                              , japan_text_element[1])
        # 한국어 자막 없으면 직접 만듬
        try:
            # 한국어 자막 없으면 except 코드 실행
            _driver.find_element_by_xpath("/html/body/div/div/div[1]/div[3]/div[2]/label/input")
        except:
            parse = str(japan_text_element[0].text)
            parse = re.sub('[-=.#/?:$},…!()]', '', parse)
            # parse = re.sub(' ', '', parse)
            if len(parse) > 0:
                temp = Translate_JPto_KO(parse)
                if temp == "네이버 id 정보 변경":  # api 사용량 다떨어져서 2번째 id로 번역함
                    temp = Translate_JPto_KO(parse)
                temp = re.sub('[a-zA-Z]', '', temp)
                script = "arguments[0].innerHTML='" + temp + "'"
                try:
                    # 한국어 자막 추가
                    driver.execute_script(script, japan_text_element[1])
                except:
                    pass

    # 재생 화면으로 포커스 이동
    iframes = _driver.find_elements_by_tag_name('iframe')
    _driver.switch_to.frame(iframes[0])

    time.sleep(3)

    # 동영상이 시작되면 1초마다 동영상이 끝났는지 확인함. 끝났다면 다음노래로 이동
    while True:
        current_stat = driver.find_element_by_class_name("ytp-play-button").get_attribute('title')

        if current_stat == "다시보기":
            break

        time.sleep(1)

    return


if __name__ == "__main__":

    # 프로그램 실행에 필요한 폴더를 생성
    create_folder()

    # 유튜브 플레이 리스트에서 노래들의 정보를 가져옴
    play_song_urls = getPlaylistLinks(play_list_url)

    # 재생 할 곡 랜덤으로 재생 여부를 정함
    if ran_play:
        random.shuffle(play_song_urls)

    if len(play_song_urls) > 0:
        print("전체 " + str(len(play_song_urls)) + "곡")
        driver = driver_set()
        for idx, play_list in enumerate(play_song_urls):
            song_name = str(play_list[0])
            song_name = song_name.replace(" ", "")
            song_name = song_name.replace("\n", "")
            song_all_num = str(len(play_song_urls))
            song_num = str(idx + 1)
            print(get_currentTime_str() + song_name + "  전체 " + song_all_num + "곡 중 " + song_num + "번째 곡 재생")
            song_id = str(play_list[1])
            url = "https://www.captionpop.com/videos/" + song_id + "?nl=ko&tl=ja"
            Play(driver, url)
    else:
        print("재생목록에 노래 없음")

    print("모든 곡 재생 완료")

from PIL import Image
import imagehash
import urllib.request as urlre
import urllib.parse as urlps
from bs4 import BeautifulSoup as bs
import re as regex
import json
import http.client

picurl = "https://img-auth.service.konami.net/captcha/pic/"

## Use For Get Hash
## Only Need Run Once
def getCapchaJsonFile():
    naming = ['blue', 'bomb', 'girl', 'meka', 'rabb']
    caplist = {}
    for name in naming:
        a = "./cap/" + name + ".png"
        key = str(imagehash.average_hash(Image.open(a)))
        caplist[key] = []
        for i in range(1, 6):
            link = "../cap/" + name + "/" + str(i) + ".png"
            caplist[key].append(str(imagehash.average_hash(Image.open(link))))

    with open('hash.json', 'w') as outfile:
        json.dump(caplist, outfile)

# Parse session value and capcha
# Return
def GetCookie():
    islogin = urlre.Request('https://p.eagate.573.jp/gate/p/login.html')
    soup = bs(urlre.urlopen(islogin).read(), 'html.parser')

    idximg = regex.findall(picurl + "(.*?)\"", str(soup.find_all("img", style="border:solid 3px #acacac;border-radius:50%")))[0]
    idximg = str(imagehash.average_hash(Image.open(urlre.urlopen(urlre.Request(picurl + idximg)))))
    capchas = regex.findall("value=\"(.*?)\"", str(soup.find_all("input", style="position:absolute;top:2px;left:2px;width:initial;")))
    hashcapchas = [str(imagehash.average_hash(Image.open(urlre.urlopen(urlre.Request(picurl + img))))) for img in capchas]
    kcsess = regex.findall("value=\"(.*?)\"", str(soup.find_all("input", type="hidden")))[0]

    data = {
        'KID': 'ENTER_YOUR_KONAMI_ID',
        'pass': 'ENTER_YOUR_KONAMI_PASSWD',
        'kcsess': kcsess,
        'OTP': '',
    }
    hashed = json.load(open('hash.json'))
    data.update({'chk_c' + str(key): capchas[key] for ans in hashed[idximg] for key, capcha in enumerate(hashcapchas) if capcha == ans})

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
        "Cache-Control": "max-age=0",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "p.eagate.573.jp",
        "Origin": "https://p.eagate.573.jp",
        "Referer": "https://p.eagate.573.jp/gate/p/login.html",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13"
    }
    conn = http.client.HTTPSConnection('p.eagate.573.jp', 443)
    conn.request("POST", "/gate/p/login.html", urlps.urlencode(data), headers)

    response = conn.getresponse()
    return regex.findall("(.*?);", response.getheader('Set-Cookie'))[0]

if __name__ == "__main__":
    Cookie = GetCookie()
    opener = urlre.build_opener()
    opener.addheaders.append(("Cookie", Cookie))
    login = opener.open("https://p.eagate.573.jp/game/reflec/reflesia/p/profile/index.html")
    with open("result.txt", 'wb') as f:
        f.write(login.read())
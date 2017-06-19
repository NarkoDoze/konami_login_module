from PIL import Image
import imagehash
import urllib.request as urlre
import urllib.parse as urlps
from bs4 import BeautifulSoup as bs
import re as regex
import json
import http.client

picurl = "https://img-auth.service.konami.net/captcha/pic/"
header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "p.eagate.573.jp",
        "Origin": "https://p.eagate.573.jp",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13",
}
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

# Parse session value and capcha and Login
# Return cookie value that can be used for fake session
def GetCookie():
    islogin = urlre.Request('https://p.eagate.573.jp/gate/p/login.html')
    soup = bs(urlre.urlopen(islogin).read(), 'html.parser')

    idximg = regex.findall(picurl + "(.*?)\"", str(soup.find_all("img", style="border:solid 3px #acacac;border-radius:50%")))[0]
    idximg = str(imagehash.average_hash(Image.open(urlre.urlopen(urlre.Request(picurl + idximg)))))
    capchas = regex.findall("value=\"(.*?)\"", str(soup.find_all("input", style="position:absolute;top:2px;left:2px;width:initial;")))
    hashcapchas = [str(imagehash.average_hash(Image.open(urlre.urlopen(urlre.Request(picurl + img))))) for img in capchas]
    kcsess = str(soup.find("input", type="hidden")['value'])

    data = {
        'KID': 'ENTER_YOUR_KONAMI_ID',
        'pass': 'ENTER_YOUR_KONAMI_PASSWD',
        'kcsess': kcsess,
        'OTP': '',
    }
    hashed = json.load(open('hash.json'))
    data.update({'chk_c' + str(key): capchas[key] for ans in hashed[idximg] for key, capcha in enumerate(hashcapchas) if capcha == ans})

    headers = dict(header)
    headers.update({"Referer": "https://p.eagate.573.jp/gate/p/login.html"})

    conn = http.client.HTTPSConnection('p.eagate.573.jp', 443)
    conn.request("POST", "/gate/p/login.html", urlps.urlencode(data), headers)

    response = conn.getresponse()
    return regex.findall("(.*?);", response.getheader('Set-Cookie'))[0]

# Get E-Amusement card code that is attached in this ID
def getCardFromID(Cookie):
    JsonListURL = "http://p.eagate.573.jp/gate/p/eapass/api/eapassinfo_json.html"
    opener = urlre.build_opener()
    opener.addheaders.append(("Cookie", Cookie))
    soup = bs(opener.open(JsonListURL).read(), 'html.parser')
    data = json.loads(soup.text)
    return data['cardnumber']

# Detech E-Amusement card from this ID
def detachCard(Cookie, CardCode):
    detachURL = "http://p.eagate.573.jp/gate/p/eamusement/detach/setting1.html?ucdto=" + CardCode
    opener = urlre.build_opener()
    opener.addheaders.append(("Cookie", Cookie))
    detachHTML = opener.open(detachURL).read()
    headers = dict(header)
    headers.update({
        "Referer": detachURL,
        "Cookie": Cookie
    })
    requestTo = regex.findall("<a href=\"(.*?)\" target=\"_self\" class=\"\">", str(detachHTML))[-1]
    conn = http.client.HTTPSConnection('p.eagate.573.jp', 443)
    conn.request("GET", requestTo, "", headers)
    # TODO : Check It is successfully completed

# Attach E-Amusement card to this ID
def attachCard(Cookie, CardCode, passwd):
    attachURL = "https://p.eagate.573.jp/gate/p/eamusement/attach/index.html"
    opener = urlre.build_opener()
    opener.addheaders.append(("Cookie", Cookie))
    attachHTML = opener.open(attachURL).read()
    soup = bs(attachHTML, 'html.parser')
    data = {
        "ucd": CardCode,
        "pass": passwd,
        "ecprop": "2",
    }
    headers = dict(header)
    headers.update({
        "Referer": attachURL,
        "Cookie": Cookie
    })
    data.update({hidden['name']: hidden['value'] for hidden in soup.find_all("input", type="hidden")})

    conn = http.client.HTTPSConnection('p.eagate.573.jp', 443)
    conn.request("POST", "/gate/p/eamusement/attach/end.html", urlps.urlencode(data), headers)
    # TODO : Check It is successfully completed

# Get played game list from this card
def playedGames(Cookie):
    JsonListURL = "http://p.eagate.573.jp/gate/p/eapass/api/eapassinfo_json.html"
    opener = urlre.build_opener()
    opener.addheaders.append(("Cookie", Cookie))
    soup = bs(opener.open(JsonListURL).read(), 'html.parser')
    data = json.loads(soup.text)
    return [{'title' : data['title'], 'img' : data['img'].replace('myp_icon', 'myp_icon_PC')} for data in data['playdatalist'] if data['title'] != '']

if __name__ == "__main__":
    Cookie = GetCookie()
    attachCard(Cookie, "CARD_CODE_NAMBER", "CARD_PASSWORD")
    detachCard(Cookie, "CARD_CODE_NAMBER")
    getCardFromID(Cookie)
    playedGames(Cookie)
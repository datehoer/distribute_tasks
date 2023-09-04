from curl_cffi import requests
headers = {
        "accept": "text/html,*/*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "device-memory": "8",
        "downlink": "2.4",
        "dpr": "1",
        "ect": "4g",
        "pragma": "no-cache",
        "rtt": "200",
        "sec-ch-device-memory": "8",
        "sec-ch-dpr": "1",
        "sec-ch-ua": "\"Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"115\", \"Chromium\";v=\"115\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-platform-version": "\"10.0.0\"",
        "sec-ch-viewport-width": "2560",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "viewport-width": "2560",
        "x-amazon-rush-fingerprints": "AmazonRushAssetLoader:2469379D1CBACC12CD7D0FC34C44BBA83B7EC9A0|AmazonRushFramework:0D976F77E04718E6518228B05DBFBEA340229576|AmazonRushRouter:3250E8E5C66452AD8DD305E5E5198FAF30EED32B",
        "x-amazon-s-fallback-url": "",
        "x-amazon-s-mismatch-behavior": "ABANDON",
        "x-amazon-s-swrs-version": "4DA86F0F70DBFCBC3D70B34272848467,D41D8CD98F00B204E9800998ECF8427E",
        "x-requested-with": "XMLHttpRequest",
        "cookie": "session-id=462-0189160-3179957; i18n-prefs=CNY; ubid-acbcn=458-5418493-2146955; session-token=paqasAs0OM5Aj2f/6iJYse7N0/DpYjg+rdAFK8u4CKco9enT0PS9PKNgS18/OCkL3uqUnKS9uYN4LvR1oC2E2l80msJRgQKcWrcgjvpl0HJd/Q+WTI6KWtFzbLwRC0mJCX04wzPu6HRVk6I1SazLEVGyb5orAIxT07DMz6muMvukhEaYGQ+VrvJJUO6zKSDkE52vKujvtsmsYsgxw1D785azteQJsyqAr5xc0t92biuf8ygcGmj+llzBbDXKjAVkvK1MhT4CtwcxKp/qWHqV0VRNj4Uwhc3upmPqCkEWcauAWynmwbJ81BPCDjREVhMaetxz9Ih6/o58y3EiNmh3R5LJqXxLJwrn; session-id-time=2082787201l; csm-hit=tb:3TZRZ68W6DXSNS2W2J97+s-MZBXW9V2J702JH8NVDRV|1693558056200&t:1693558056200&adb:adblk_no",
        "Referer": "https://www.amazon.cn/s?k=%E9%A3%9E%E5%88%A9%E6%B5%A6%E7%89%99%E5%88%B7&page=4&__mk_zh_CN=%E4%BA%9A%E9%A9%AC%E9%80%8A%E7%BD%91%E7%AB%99&crid=30SRPZ52ROF43&qid=1693557207&sprefix=%E9%A3%9E%E5%88%A9%E6%B5%A6ya%27shua%2Caps%2C420&ref=sr_pg_4",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

data = {
        "page-content-type": "atf",
        "prefetch-type": "rq",
        "customer-action": "pagination"
    }
url = "https://www.amazon.cn/s/query"
params = {
        "__mk_zh_CN": "亚马逊网站",
        "crid": "30SRPZ52ROF43",
        "k": "Google Pixel 5",
        "page": "1",
        "qid": "1693558038",
        "ref": "sr_pg_4",
        "sprefix": "飞利浦ya'shua,aps,420",
}
res = requests.post(url, params=params, headers=headers, data=data, proxies={'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
print(res.content.decode('utf-8'))
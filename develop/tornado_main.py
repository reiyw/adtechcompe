import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httpserver
import time
import json
import pandas as pd
import badgets as bg
import sys
sys.path.append('../clf')
import predict as pred


ngdomains_list = json.load(open('json/ngdomains.json'))
budgets_df = pd.read_json('json/budgets.json')
cpcs = budgets_df.loc['cpc']
nurl = 'http://104.155.237.141/win/'
alfa_list=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

hashed_ng_domains = {
    k: set(v) for k, v in json.load(open('json/ngdomains.json')).iteritems()}


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("test")
class BidHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("test bid request.")

    def post(self, *args, **kwargs):
        request = self.request.body
        j = json.loads(request)
        auction_id = j['id']

        # floorPrice is optional
        floorprice = 0 if j['floorPrice'] is None else j['floorPrice']

        # fetch all advertiser's budgets

        budgets = bg.get_budgets()

        # check NG domains and budgets, then decide advertiser to join
        advertisers = [
            int(adv[4:]) for adv, ngdomains in hashed_ng_domains.iteritems()
            if j['site'] not in ngdomains and budgets[adv] > 0
        ]

        #no badgets
        if len(advertisers) < 1:
            self.set_status(204)

        bid_user = int(j["user"])
        bid_request_for_predict = [j["browser"], j["site"],bid_user]

        # predict CTR
        ctr_list = pred.predict(bid_request_for_predict, advertisers)
        # cal bidprice
        value_list_from_predict = []
        for (i, ctr) in enumerate(ctr_list):
            value_list_from_predict.append(ctr * budgets_df['adv_'+str(i+1).zfill(2)]['cpc'])

        value_list = []
        for (i, value) in enumerate(value_list_from_predict):
            value_list.append(value*alfa_list[i])

        bidPrice = max(value_list)

        adv_id_ = value_list.index(max(value_list)) + 1
        adv_id = 'adv_' + str(adv_id_).zfill(2)

        bidPrice *= 1000

        # make response
        response = {
            'id' : auction_id,
            'bidPrice' : bidPrice,
            'advertiserId' : adv_id,
            'nurl' : nurl + adv_id
        }

        if floorprice < bidPrice:
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response))
        else:
            self.set_status(204)

        # log data
        with open("/var/log/bid_access.log", "a+") as file:
            file.write(time.ctime())
            file.write("   ")
            file.write(json.dumps(response))
            file.write(' ' + j['site'])
            file.write("\n")
        with open("/var/log/bid_price.log", "a+") as file:
            buf = " bid price = " + str(bidPrice) + "     adv_id = " + adv_id
            file.write(buf)

class Win_Handler(tornado.web.RequestHandler):
    def get(self):
        self.write("test win notice.")
    def post(self, adv_id):
        req = json.loads(self.request.body)

        # consume adv_id's badget
        if req['isClick'] == 1:
            bg.consume(adv_id, float(cpcs[adv_id]))

class DebugHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("debug")

if __name__ == "__main__":
    bg.connect()

    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/bid", BidHandler),
        (r"/win/(.*)", Win_Handler),
        (r"/debug", DebugHandler),
    ])

    server = tornado.httpserver.HTTPServer(application)
    server.bind(80)
    server.start(0)
    tornado.ioloop.IOLoop.current().start()

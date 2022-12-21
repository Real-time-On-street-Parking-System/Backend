import pymongo
from configobj import ConfigObj
from datetime import datetime


class MongoIO:
    def __init__(self) -> None:
        self.__init_mongo_config()
        self.__client = pymongo.MongoClient(
            f'mongodb://{self.__host}:{self.__port}')
        self.__database = self.__client[self.__db]
        self.__parking_space_info = self.__database['parking_space_info']
        self.__parking_space_data = self.__database['parking_space_data']

    def __init_mongo_config(self) -> None:
        """
        讀取 mongoDB config
        """
        mongo_config = ConfigObj('docs/mongo_config.ini', encoding='utf-8')
        self.__host = mongo_config['host']
        self.__port = mongo_config['port']
        self.__db = mongo_config['db']

    def create_parking_space(self, name, parking_loc, parking_volume) -> str:
        """
        建立指定停車場的最大車位數
        :params parking_loc (str): 停車格經緯度, ex: "25.024773,121.527724"
        :params parking_volume (int): 最大車位數
        """

        data = {
            "name": name,
            "loc": parking_loc,
            "volume": parking_volume,
            "online": False
        }
        res = self.__parking_space_info.insert_one(data)

        return res.inserted_id

    def insert_parking_data(self, loc, time, parking_num) -> str:
        """
        存機車停車資料
        :params loc (str): 經緯度, ex: "25.024773,121.527724"
        :params time (str): 時間, ex: "Wed Nov 30 15:01:03 2022"
        :params parking_num (int): 機車數量, ex: "1"
        """

        data = {
            "loc": loc,
            "time": datetime.strptime(time, "%c"),
            "num": parking_num
        }
        res = self.__parking_space_data.insert_one(data)

        return res.inserted_id

    def get_all_parking_info(self) -> list[dict]:
        """
        取得所有的停車地點資訊
        """

        parking_info_list = []
        # 取得上線中的停車地點
        online_parking_space_info = self.__parking_space_info.find({
            "online": True
        })
        for parking_info in online_parking_space_info:
            parking_info_list.append({
                'name': parking_info['name'],
                'loc': parking_info['loc']
            })
        return parking_info_list

    def get_parking_volume(self, loc) -> int:
        """
        取得停車地點的停車格數量
        :params loc (str): 停車格經緯度, ex: "25.024773,121.527724"
        """

        if not self.is_parking_location_online(loc):
            return -1

        res = self.__parking_space_info.find({
            "loc": loc
        })

        return res['volume']

    def get_parking_data(self, loc) -> list[dict]:
        """
        拿指定座標的停車格所有時間的資料
        :params loc (str): 停車格經緯度, ex: "25.024773,121.527724"
        """

        if not self.is_parking_location_online(loc):
            return []

        parking_data = []
        res_data = self.__parking_space_data.aggregate(
            [
                {
                    '$match': {
                        'loc': loc,
                    }
                },
                {
                    '$sort': {
                        'time': -1,
                    }
                }
            ]
        )

        for data in res_data:
            parking_data.append(data)

        return parking_data

    # def GetTrafficFlow(parkingLoc):
    #     """
    #         拿指定座標的停車格五分鐘內的平均車流量
    #         :params parkingLoc(str): 停車格經緯度, ex: "25.024773,121.527724"
    #     """
    #     now = datetime.now()
    #     parkingSpace = GetParkingSpace(parkingLoc)
    #     trafficFlow = 0
    #     numOfData = 0
    #     for data in parkingSpace:
    #         delta = now - data['time']
    #         if delta < timedelta(minutes=5):
    #             numOfData += 1
    #             trafficFlow += int(data['num'])
    #         else:
    #             break
    #     if numOfData > 0:
    #         return trafficFlow / numOfData
    #     return "No Data!"

    def delete_data(self, collection_name, condition) -> int:
        """
        刪除 collection 內的資料
        :params collection_name (str): 欲刪除的 collection
        :params condition (str): 欲刪除的條件 Ex: {}
        """

        collection = self.__database[collection_name]
        res = collection.delete_many(condition)
        print(res.deleted_count, " documents deleted.")
        return res.deleted_count

    def is_parking_location_online(self, loc) -> bool:
        """
        回傳指定地點是否在線上
        :params loc (str): 停車格經緯度, ex: "25.024773,121.527724"
        """

        res = self.__parking_space_info.find({
            'loc': loc
        })

        return res['status']

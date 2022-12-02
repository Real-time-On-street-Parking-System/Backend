import json
import logging
import haversine
from flask import Flask, request

from src.MongoIO import MongoIO

app = Flask(__name__)
mongo_client = MongoIO()


def gen_response_json(status, code, message, data={}) -> dict:
    return {
        'status': status,
        'code': code,
        'message': message,
        'data': data,
    }


def transform_coordinate(loc) -> tuple[float, float]:
    """
    轉換位置為經緯度的 tuple
    :params loc (str): 字串的經緯度
    """

    lat, long = map(lambda cor_str: cor_str.strip(), loc.split(','))
    return (float(lat), float(long))


@app.route('/get_near_parking_location', methods=['POST'])
def get_near_parking_location():
    """
    拿使用者座標方圓兩公里內的所有停車格經緯度
    :params user_loc (str): 使用者所在經緯度, ex: "25.024773,121.527724"
    """

    request_body = request.get_json()
    user_loc = request_body.get('location')
    user_coordinate = transform_coordinate(user_loc)
    all_parking_info = mongo_client.get_parking_info()

    near_parking_loc = []
    for loc in all_parking_info:
        parking_coordinate = transform_coordinate(loc)
        dist = haversine(user_coordinate, parking_coordinate)
        # TODO: distance limit record in config file
        if dist < 2.0:
            near_parking_loc.append({
                'loc': loc,
                'distance': dist
            })

    return gen_response_json(
        status='success',
        code=200,
        message='成功取得資料',
        data=near_parking_loc
    )


@app.route('/get_parking_space_density', methods=['POST'])
def get_parking_space_density():
    """
    拿指定停車場的狀態，紅: 接近滿，黃: 半滿，綠: 空
    :params parking_loc (str): 停車格經緯度, ex: "25.024773,121.527724"
    """

    request_body = request.get_json()
    parking_loc = request_body.get('location')

    volume = mongo_client.get_parking_volume(parking_loc)
    parking_data = mongo_client.get_parking_data(parking_loc)
    if len(parking_data) == 0:
        return "No Data!"

    response = None
    density = int(parking_data[0]['num']) / volume
    if density > 0.8:
        response = 'Red'
    elif 0.5 < density <= 0.8:
        response = 'Yellow'
    else:
        response = 'Green'

    return gen_response_json(
        status='success',
        code=200,
        message='成功取得資料',
        data=response
    )

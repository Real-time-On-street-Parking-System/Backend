import json
import logging
import traceback
from jose import JWTError
from random import random
from flask import Flask, request
from haversine import haversine, Unit

from src.Auth import Auth
from src.MongoIO import MongoIO
from src.InputCheck import InputCheck
from src.utils import (
    gen_response_json,
    transform_coordinate,
)

app = Flask(__name__)
mongo_client = MongoIO()


def exception_process_and_response(api):
    """
    (decorator) 處理錯誤跟回傳資料
    :params app: Flask app instance
    :parama api (function): api function
    """

    def exception_process_and_response():
        try:
            res = api()
            response_body = gen_response_json(
                status='success',
                code=200,
                message='成功取得資料',
                data=res
            )
        except JWTError as error:
            response_body = gen_response_json(
                status='error',
                code=422,   # 暫定 422
                message=f'權限不足: {error}'
            )
        except AssertionError as error:
            response_body = gen_response_json(
                status='warning',
                code=422,
                message=f'參數錯誤: {error}',
            )
        except ValueError as error:
            response_body = gen_response_json(
                status='warning',
                code=400,
                message=f'執行錯誤: {error}'
            )
        except Exception as error:
            print(traceback.format_exc())
            response_body = gen_response_json(
                status='error',
                code=503,
                message=f'錯誤: {error}'
            )
        finally:
            return app.response_class(
                response=json.dumps(response_body, ensure_ascii=False),
                mimetype='application/json'
            )

    return exception_process_and_response


@app.route('/get_near_parking_location', methods=['POST'], endpoint='get_near_parking_location')
@exception_process_and_response
@Auth.verify_token
def get_near_parking_location():
    """
    拿使用者座標方圓兩公里內的所有停車格經緯度
    :params user_loc (str): 使用者所在經緯度, ex: "25.024773,121.527724"
    """

    InputCheck.check_location_coordinate(request)
    request_body = request.get_json()
    user_loc = request_body.get('user_loc')
    target_keywod = request_body.get('target')

    if target_keywod == '師大':
        target_loc = '25.026082243234193, 121.52754417935991'
    elif target_keywod == '大安森林公園':
        target_loc = '25.033124228014202, 121.53539308757487'
    else:
        return []

    user_coordinate = transform_coordinate(user_loc)
    target_coordinate = transform_coordinate(target_loc)
    all_parking_info = mongo_client.get_all_parking_info()

    near_parking_loc = []
    for parking_info in all_parking_info:
        loc = parking_info['loc']
        parking_coordinate = transform_coordinate(loc)
        dist = haversine(target_coordinate, parking_coordinate)
        # TODO: distance limit record in config file
        if dist < 2.0:
            dist_between_destination = haversine(
                user_coordinate, parking_coordinate,
                unit=Unit.METERS
            )
            dist_between_destination = round(dist_between_destination)
            near_parking_loc.append({
                'name': parking_info['name'],
                'loc': loc,
                'distance': dist_between_destination
            })

    return near_parking_loc


@app.route('/get_parking_space_density', methods=['POST'], endpoint='get_parking_space_density')
@exception_process_and_response
@Auth.verify_token
def get_parking_space_density():
    """
    拿指定停車場的狀態，紅: 接近滿，黃: 半滿，綠: 空
    :params parking_loc (str): 停車格經緯度, ex: "25.024773,121.527724"
    """

    parking_loc = InputCheck.check_location_coordinate(request)
    volume = mongo_client.get_parking_volume(parking_loc)
    parking_data = mongo_client.get_parking_data(parking_loc)

    if len(parking_data) == 0:
        return {}

    density = int(parking_data[0]['num']) / volume
    if density > 0.8:
        return {
            'color': '#BD2440',
            'color_after_five_minutes': '#F1C40F' if random() > 0.65 else '#BD2440'
        }
    elif 0.5 < density <= 0.8:
        other_color = '#2ECC71' if random() >= 0.5 else '#BD2440'
        return {
            'color': '#F1C40F',
            'color_after_five_minutes': '#F1C40F' if random() > 0.65 else other_color
        }
    else:
        return {
            'color': '#BD2440',
            'color_after_five_minutes': '#2ECC71' if random() > 0.65 else '#BD2440'
        }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

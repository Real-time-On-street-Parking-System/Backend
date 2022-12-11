

def gen_response_json(status, code, message, data={}) -> dict:
    """
    定義回傳格式
    :params status (str): 狀態資訊
    :params code (int): http 狀態碼
    :params message (str): 詳細的狀態資訊
    :params data (dict): 回傳的 data
    """

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

class InputCheck:
    @classmethod
    def check_location_coordinate(cls, request) -> str:
        """
        取得 request 驗證參數並回傳
        :params request (flask.request): request instance
        """

        request_body = request.get_json()
        location = request_body.get('location')
        lat, long = map(lambda cor: cor.strip(), location.split(','))
        try:
            lat = float(lat)
            long = float(long)
        except ValueError:
            raise AssertionError('非合法經緯度參數')

        return location

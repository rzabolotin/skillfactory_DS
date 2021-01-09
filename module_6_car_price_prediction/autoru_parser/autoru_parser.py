import argparse
from collections import namedtuple, defaultdict
from csv import DictWriter
import json
from pathlib import Path

import requests
from loguru import logger

columns = ['bodyType', 'brand', 'car_url', 'color', 'complectation_dict', 'description', 'engineDisplacement',
           'enginePower', 'location',
           'equipment_dict', 'fuelType', 'image', 'mileage', 'modelDate', 'model_info', 'model_name', 'name',
           'numberOfDoors', 'parsing_unixtime', 'priceCurrency', 'productionDate', 'sell_id', 'super_gen',
           'vehicleConfiguration', 'vehicleTransmission', 'vendor', 'Владельцы', 'Владение', 'ПТС', 'Привод',
           'Руль', 'Состояние', 'Таможня', 'price']

CarInfo = namedtuple('Car', columns)

brand_in_test = {
    'BMW': 4473,
    'VOLKSWAGEN': 4404,
    'NISSAN': 4393,
    'MERCEDES': 4180,
    'TOYOTA': 3913,
    'AUDI': 3421,
    'MITSUBISHI': 2843,
    'SKODA': 2741,
    'VOLVO': 1463,
    'HONDA': 1150,
    'INFINITI': 871,
    'LEXUS': 834
}
cars_in_test = sum(val for val in brand_in_test.values())
proportion_in_test = {key: val / cars_in_test for key, val in brand_in_test.items()}


def get_headers():
    headers = '''
Host: auto.ru
Connection: keep-alive
Content-Length: 99
x-requested-with: fetch
x-client-date: 1603066469874
x-csrf-token: c23073bb4cd65413662a41bd460fd8317459fe3ce6d83db1
x-page-request-id: 3c4800b60eb9e8c568e5a515f5cd4872
content-type: application/json
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36
x-client-app-version: 202010.16.122434
Accept: */*
Origin: https://auto.ru
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: same-origin
Sec-Fetch-Dest: empty
Referer: https://auto.ru/cars/bmw/all/?output_type=list&page=1
Accept-Encoding: gzip, deflate, br
Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7
Cookie: autoru_sid=a%3Ag5f88f7d72b1bif6t0m99h0krigjgs2e.a783a85b576c8a7acaea4faafaa81ffc%7C1602811863959.604800.QhhqH0HWfM4BPWrsvjyfIg.8EXrpUR7Bq1a2gOSCnsb0HnXxvmHbYB9eF5Uz5o_bZE; autoruuid=g5f88f7d72b1bif6t0m99h0krigjgs2e.a783a85b576c8a7acaea4faafaa81ffc; suid=63abf8672f4a9e550bb96dd00b95ad21.8e155bfb838a5227bdd9dea1d2cbdc3e; _ym_uid=1602811867719278329; yuidcs=1; crookie=PZwS3/iYq2PFIw/dbrsqDVB/0e2v79Xe/8RsG6ySC8Djcl+mh/UCjYohgODaSkw7rMa6O9v7+RD56YSQKE2fhSkWxV8=; cmtchd=MTYwMjgyODMxMjMwNQ==; bltsr=1; yuidlt=1; yandexuid=360949521578055883; my=YwA%3D; _ym_isad=1; promo-app-banner-shown=1; promo-header-counter=4; _csrf_token=c23073bb4cd65413662a41bd460fd8317459fe3ce6d83db1; from=direct; X-Vertis-DC=myt; _ym_wasSynced=%7B%22time%22%3A1603066366683%2C%22params%22%3A%7B%22eu%22%3A0%7D%2C%22bkParams%22%3A%7B%7D%7D; gdpr=0; _ym_visorc_22753222=b; from_lifetime=1603066463083; _ym_d=1603066470'''
    headers = {line.split(': ')[0]: line.split(': ')[1] for line in headers.strip().split('\n')}
    return headers


def get_data_from_site(pange_num: int, brand: str) -> dict:
    """ получает данные о тачках БМВ с авто.ру, номер страницы передан в параметре page_num
    возвращает полученный с сайта json """

    base_url = 'https://auto.ru/-/ajax/desktop/listing/'
    params = dict(category='cars', section="all", output_type="list", page=pange_num,
                  catalog_filter=[{'mark': brand}], geo_id=[213], geo_radius=800)
    r = requests.post(base_url, json=params, headers=get_headers())
    r.raise_for_status()
    return r.json()


def add_car_data(car_data: list, data_json: dict):
    """ разбирает данные из переданного объекта data_json
    из массива offers, формирует объекты CarInfo и
    добавляет их в список car_data"""

    if 'offers' not in data_json:
        return

    for car in data_json['offers']:
        if 'configuration' not in car['vehicle_info']:
            continue

        body_type_human = car['vehicle_info']['configuration']['human_name']
        body_type = car['vehicle_info']['configuration']['body_type']
        transmission = car['vehicle_info']['tech_param']['transmission']
        engine_volume = car['vehicle_info']['tech_param']['displacement']
        engine_volume = round(float(engine_volume) / 1000, 1)

        try:
            purchase_date = car['documents']['purchase_date']
        except KeyError:
            purchase_date = None

        try:
            owners_number = car['documents']['owners_number']
        except KeyError:
            owners_number = None

        try:
            description = car['description']
        except KeyError:
            description = None
        try:
            pts = car['documents']['pts']
        except KeyError:
            pts = None
        try:
            price = car['price_info']['RUR']
        except KeyError:
            continue

        brand = car['vehicle_info']['mark_info']['name']
        model = car['vehicle_info']['model_info']['name']
        sell_id = car['saleId']
        section = car['section']
        car_url = f'https://auto.ru/cars/{section}/sale/{brand.lower()}/{model.lower()}/{sell_id}/'

        info = CarInfo(bodyType=body_type_human,
                       brand=brand,
                       car_url=car_url,
                       image=car['state']['image_urls'][0]['sizes']['small'],
                       color=car['color_hex'],
                       complectation_dict=car['vehicle_info']['complectation'],
                       equipment_dict=car['vehicle_info']['equipment'],
                       model_info=car['vehicle_info']['model_info'],
                       model_name=model,
                       location=car['seller']['location']['region_info']['name'],
                       parsing_unixtime=car['additional_info']['fresh_date'],
                       priceCurrency=car['price_info']['currency'],
                       sell_id=sell_id,
                       super_gen=car['vehicle_info']['super_gen'],
                       vendor=car['vehicle_info']['vendor'],
                       fuelType=car['vehicle_info']['tech_param']['engine_type'],
                       modelDate=car['vehicle_info']['super_gen']['year_from'],
                       name=car['vehicle_info']['tech_param']['human_name'],
                       numberOfDoors=car['vehicle_info']['configuration']['doors_count'],
                       productionDate=car['documents']['year'],
                       vehicleConfiguration=body_type + " " + transmission + " " + str(engine_volume),
                       vehicleTransmission=transmission,
                       engineDisplacement=str(engine_volume) + ' LTR',
                       enginePower=str(car['vehicle_info']['tech_param']['power']) + ' N12',
                       description=description,
                       mileage=car['state']['mileage'],
                       Привод=car['vehicle_info']['tech_param']['gear_type'],
                       Руль=car['vehicle_info']['steering_wheel'],
                       Состояние=car['state']['state_not_beaten'],
                       Владельцы=owners_number,
                       ПТС=pts,
                       Таможня=car['documents']['custom_cleared'],
                       Владение=purchase_date,
                       price=price
                       )
        car_data.append(info)


def write_to_csv(car_data: list, output_folder_path: Path, page_num: int):
    """Записывает информацию о машинах из car_data в файл формата csv
    output_folder_path задает папку для сохранения
    page_num - нужен для наименования файла"""

    if not car_data:
        return

    filename = output_folder_path / f'train_{page_num}.csv'
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        logger.info(f'writing {filename}, содержащий {len(car_data)} записей')
        writer = DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows([car._asdict() for car in car_data])


def pickup_brand(brand_stats: dict) -> str:
    cars_count = sum(val for val in brand_stats.values())
    brand_proportion = {key: val / cars_count for key, val in brand_stats.items()}

    proportion_in_test_copy = proportion_in_test.copy()
    for key, val in brand_proportion.items():
        proportion_in_test_copy[key] -= val

    return sorted(proportion_in_test_copy.items(),
                  key=lambda x: x[1],
                  reverse=True)[0][0] # first element, key of pair key:value


def parse_data(n_pages, output_folder, save_json, json_folder):
    """Входная точка в программу. Содержит верхнеуровневую логику.
    Собирает информацию с сайта, парсит и сохраняет в формате csv"""

    logger.info('Starting parse data from auto.ru about cars')

    if save_json:
        json_folder_path = Path(json_folder)
        json_folder_path.mkdir(parents=True, exist_ok=True)

    output_folder_path = Path(output_folder)
    output_folder_path.mkdir(parents=True, exist_ok=True)

    car_data = []
    brand_stats = defaultdict(lambda: 1)

    for page_num in range(1, n_pages + 1):

        brand = pickup_brand(brand_stats)

        logger.info(f'processing page: {page_num} {brand} {brand_stats[brand]}')
        try:
            data_json = get_data_from_site(brand_stats[brand], brand)
        except Exception as e:
            logger.error(f"Error in parsing: {e}")
            continue

        brand_stats[brand] += 1

        if save_json:
            with open(json_folder_path / f'page_{page_num}.json', 'w', encoding='utf-8') as f:
                json.dump(data_json, f)

        add_car_data(car_data, data_json)

        if page_num % 50 == 0:
            write_to_csv(car_data, output_folder_path, page_num)
            car_data = []

    write_to_csv(car_data, output_folder_path, page_num)

    logger.info('parsing successfully finished')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n_pages", help="number of pages to parse", type=int)
    parser.add_argument("-o", "--output_folder", help='folder to save parsed csv files', type=str, default='.')
    parser.add_argument("-j", "--save_json", help="save json files", action="store_true")
    parser.add_argument("--json_folder", help='folder for json files', type=str, default='json')
    args = parser.parse_args()

    parse_data(args.n_pages,
               args.output_folder,
               args.save_json,
               args.json_folder)


if __name__ == '__main__':
    main()

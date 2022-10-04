import requests
import logging
from multiprocessing import Pool, freeze_support
from itertools import repeat
import time
# from fake_useragent import UserAgent

# Search settings
DEVICE = 'xmen'
PLATFORM_ID = 655
ANDROID_VER = '6.0.1'
CURRENT_BUILD = 1316
BUILD_DELTA = 1000
BUILD_FIND = 2  # values: 1: 'upgrade', 2: 'downgrade'

# Advanced settings
workerCount = 300
connectionErrorRetry = 20
connectionErrorRetryDelay = 30
httpNotFoundRetry = 3
httpNotFoundRetryDelay = 30

updateUriTemplate = 'http://ota.cdn.pandora.xiaomi.com/rom/{platformId}/{device}/user/{androidVer}.{otaBuild}/{androidVer}.{currentBuild}/package-{androidVer}.{currentBuild}-{androidVer}.{otaBuild}.zip'


# ua = UserAgent()
myUserAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

_logger= logging.getLogger()
_logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('ota-update-result-{}-{}-{}-{}.txt'.format(DEVICE, PLATFORM_ID, CURRENT_BUILD, BUILD_FIND), 'w', 'utf-8')
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter) 
_logger.addHandler(handler)

def get_try(ob, cb, connectionErrorCount=0, httpNotFoundCount=0):
    if BUILD_FIND == 2:
        u = updateUriTemplate.format(platformId=PLATFORM_ID, device=DEVICE, androidVer=ANDROID_VER, otaBuild=cb, currentBuild=ob) # Downgrade
    else:
        u = updateUriTemplate.format(platformId=PLATFORM_ID, device=DEVICE, androidVer=ANDROID_VER, otaBuild=ob, currentBuild=cb) # Upgrade

    try:
        _logger.debug('start: {}:{}: '.format(cb, ob))
        # myUserAgent = ua.random
        headers = {'User-Agent': myUserAgent}
        res = requests.get(u, headers=headers)

        _logger.debug(res.status_code)

        if res.status_code == 404:
            if httpNotFoundCount < httpNotFoundRetry:
                _logger.debug("NotFoundError retrying")
                httpNotFoundCount += 1
                time.sleep(httpNotFoundRetryDelay)
                return get_try(ob, cb, connectionErrorCount=connectionErrorCount, httpNotFoundCount=httpNotFoundCount)
            else:
                return False

        if res.status_code == 200:
            res_text = 'Found firmware update: {}'.format(u)
            print(res_text)
            _logger.info(res_text)

            return True
    except requests.exceptions.ConnectionError:
        _logger.debug("Connection refused")
        if connectionErrorCount < connectionErrorRetry:
            _logger.debug("ConnectionError retrying")
            connectionErrorCount += 1
            time.sleep(connectionErrorRetryDelay)
            return get_try(ob, cb, connectionErrorCount=connectionErrorCount, httpNotFoundCount=httpNotFoundCount)

    return False


def try_number(ob, cb):
    res = get_try(ob, cb)
    if not res:
        res_text = 'Not found: {}'.format(ob)
        print(res_text)
        _logger.debug(res_text)

    return res


def main():
    with Pool(workerCount) as pool:
        if BUILD_FIND == 2:
            end_build = CURRENT_BUILD-BUILD_DELTA-1
            if end_build < 0:
                end_build = 0
        else:
            end_build = CURRENT_BUILD+BUILD_DELTA+1

        def worker_proccess(cb):
            if BUILD_FIND == 2:
                ranges = range(cb-1, end_build, -1)
            else:
                ranges = range(cb+1, end_build, 1)

            c = 0
            for result in pool.starmap(try_number,  zip(ranges, repeat(cb))):
                if result:
                    worker_proccess(cb)
                c += 1

        worker_proccess(CURRENT_BUILD)


if __name__ == "__main__":
    print('starting...')
    _logger.debug('starting...')

    freeze_support()
    main()

    print('All finished')
    _logger.debug('All finished')

from bluepy.btle import Scanner, DefaultDelegate, BTLEManagementError
from bluepy.btle import ScanEntry
import hashlib
import json
#import redis

# def redis_connection(decode=False):
#     return(redis.Redis(
#         host=settings.REDIS_HOST,
#         port=settings.REDIS_PORT,
#         db=settings.REDIS_DATABASE,
#         decode_responses=decode
#     ))


# LOCK_NAME = 'btle-lock'
# r = redis_connection(decode=True)


# def set_lock(timeout):
#     if r.get(LOCK_NAME):
#         return False
#     else:
#         r.set(LOCK_NAME, 1)
#         r.expire(LOCK_NAME, timeout)
#         return True


# def delete_lock():
#     r.delete(LOCK_NAME)


def log_btle_error():
    btle_error_key = 'btle-error'
    btle_error_key_ttl = 3600

    # if r.get(btle_error_key):
    #     r.incr(btle_error_key)
    #     r.expire(btle_error_key, btle_error_key_ttl)
    # else:
    #     r.set(btle_error_key, 1)
    #     r.expire(btle_error_key, btle_error_key_ttl)


# def lookup_bluetooth_manufacturer(manufacturer):
#     """
#     We need to do a fair bit of juggling here, but the goal is to
#     return the manufacturer based on the data we captured.

#     We need to swap around the result [1] and then convert it to
#     decimal in order to look it up from the Nordic database.

#     [1] https://stackoverflow.com/questions/23626871/list-of-company-ids-for-manufacturer-specific-data-in-ble-advertising-packets#comment36359241_23626871
#     """

#     shuffled_manufacturer = '0x{}{}'.format(manufacturer[2:4], manufacturer[0:2])
#     manufacturer_in_decimal = int(shuffled_manufacturer, 16)
#     redis_key = 'manufacturer-{}'.format(manufacturer_in_decimal)
#     lookup_result = 'Unknown'
#     redis_lookup = r.get(redis_key)

#     if not redis_lookup:
#         with open('company_ids.json', 'r') as company_ids:
#             company_database = json.loads(company_ids.read())

#         for company in company_database:
#             r.set('manufacturer-{}'.format(company['code']), company['name'])
#             if company['code'] == manufacturer_in_decimal:
#                 lookup_result = company['name']
#         return lookup_result
#     else:
#         return redis_lookup


def build_device_fingerprint(device):
    """
    Because BLE devices (type: random), re-generates the MAC address,
    we won't be able to track returning visitors. We need to attempt
    to build a footprint instead based on metadata from the GAP payload [1].

    Some additional insperation can also be found here [2].


    [1] https://www.bluetooth.com/specifications/assigned-numbers/generic-access-profile/
    [2] https://hal.inria.fr/hal-02359914/document
    """

    fingerprint = ''

    # Start by the first two octets of the manufacturer
    if device.getValue(255):
        fingerprint += device.getValueText(255)[0:4]

    # If the device type is public, we know it should be static,
    # so no need to go on. If however it is 'random', we need to
    # feed other random metadata to try to establish a fingerprint.
    if device.addrType == 'public':
        fingerprint += device.addr
        print("Public finger: " + fingerprint)    
    else:
        # Flags
        if device.getValue(1):
            fingerprint += device.getValueText(1)

        # TX Power
        if device.getValue(10):
            fingerprint += device.getValueText(10)

        # Incomplete 16b Services
        if device.getValue(2):
            fingerprint += device.getValueText(2)

        # Incomplete 128b Services
        if device.getValue(6):
            fingerprint += device.getValueText(6)

        # Complete Local Name
        if device.getValue(9):
            fingerprint += device.getValueText(9)

        # Short Local Name
        if device.getValue(8):
            fingerprint += device.getValueText(8)

        print("Random finger: " + fingerprint)    
        print("Random device addr: " + device.addr)
        print("getScanData: ")
        print(device.getScanData())    
        print("Class of device: ")
        print(device.getValueText(11))    


    return hashlib.sha256(fingerprint.encode()).hexdigest()

def scan_for_btle_devices(timeout=30):
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)

    try:
        # if set_lock(timeout+5):
        #     scanner = Scanner().withDelegate(ScanDelegate())
        #     scan_result = scanner.scan(float(timeout), passive=True)
        #     delete_lock()
        #     return(scan_result)
        print("hertil 2")
        scanner = Scanner().withDelegate(ScanDelegate())
        scan_result = scanner.scan(float(timeout), passive=True)
        
        #delete_lock()
        return(scan_result)

        # else:
        #     print('Failed to acquire lock.')
        #     return
    except BTLEManagementError:
        log_btle_error()
        #print('Got BTLEManagementError. Failure counter at {}.'.format(r.get('btle-error')))
        return

def populate_device(device):
    """
    Populates the dataset. If Databat is enabled,
    also submit the payload to Databat's backend.
    """

    payload = {
        #'timestamp': timezone.now(),
        'device_type': device.addrType,
        'rssi': device.rssi,
        'seen_counter': 1,
    }

    """ obj, created = Device.objects.get_or_create(
            device_address=device.addr,
            device_type=device.addrType,
    ) """

    if device.getValue(ScanEntry.MANUFACTURER):
        # manufacturer = lookup_bluetooth_manufacturer(
        #     device.getValueText(ScanEntry.MANUFACTURER)
        # )
        #obj.device_manufacturer = manufacturer
        payload['device_manufacturer'] = device.getValueText(ScanEntry.MANUFACTURER)

        #obj.device_manufacturer_string_raw = device.getValueText(ScanEntry.MANUFACTURER)
        
        #payload['device_manufacturer_string'] = device.getValueText(ScanEntry.MANUFACTURER)
       

    # if not created:
    #     obj.seen_counter = obj.seen_counter + 1
    #     payload['seen_counter'] = obj.seen_counter

    # if int(device.rssi) < settings.SENSITIVITY:
    #     obj.seen_within_geofence = True

    # obj.ignore = obj.seen_counter > settings.DEVICE_IGNORE_THRESHOLD

    device_fingerprint = build_device_fingerprint(device)
    #obj.device_fingerprint = device_fingerprint
    payload['device_fingerprint'] = device_fingerprint

    #obj.seen_last = timezone.now()
    #obj.scanrecord_set.create(rssi=device.rssi)
    #obj.save()

    return payload
    
def scan(timeout=30):
    print("Scan:")

    #if get_error_counter() > 20:
        #print('Hit BTLEManagementError threshold. Rebooting.')
        # if settings.BALENA:
        #     perform_reboot = requests.post(
        #         '{}/v1/reboot'.format(settings.BALENA_SUPERVISOR_ADDRESS),
        #         params={'apikey': settings.BALENA_SUPERVISOR_API_KEY}
        #     )
        #     return perform_reboot
        # else:
        #     print('Reboot for non-Balena is not implemented yet.')

    perform_scan = scan_for_btle_devices(timeout=timeout)
    print("Hertil")
    result = []
    #devices_within_geofence = 0
    if perform_scan:
        for device in scan_for_btle_devices(timeout=timeout):
            result.append(
                populate_device(device)
            )

            # if device.rssi < settings.SENSITIVITY:
            #     devices_within_geofence = devices_within_geofence + 1

        return('Successfully scanned.')
    else:
        return('Unable to scan for devices.')
    
    print(result)


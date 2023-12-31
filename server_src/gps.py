import folium
import webbrowser
import geopy.distance
from PIL import Image
import io
import os
from wifi import in_out_position
from tinydb import TinyDB, Query



def retrieve_position(id):
    print('retrieve position')
    db = TinyDB('mqtt_database.json')
    gps_table = db.table('gps_readings')
    coord = Query()
    print(id)
    all_coord = gps_table.search(coord.client_id.all(id))
    location = all_coord[-1]
    print(location)
    location = location['coord']
    location = location.split(',')
    location = [float(i) for i in location]
    map = folium.Map(location=location, zoom_start=50)
    map.add_child(folium.Marker(location=location, popup='Tughlakabad',
                                icon=folium.Icon(color='green')))

    img_data = map._to_png(5)
    img = Image.open(io.BytesIO(img_data))
    img.save('map' + id + '.png')
    img = os.path.abspath('map' + id + '.png')
    # webbrowser.open('map' +'id'+'.png')
    db.close()
    return img


def gps_operations(id):
    db = TinyDB('mqtt_database.json')
    gps_table = db.table('gps_readings')
    coord = Query()
    all_coord = gps_table.search(coord.client_id.all(id))
    location = all_coord[-1]

    gps_house_coord = db.table('gps_house_coord')
    houde_coord = Query()
    h_location = gps_house_coord.search(houde_coord.client_id.all(id))
    location = location['coord']
    if (len(h_location) == 0) and (location != "0.000000,0.000000"):
        gps_house_coord.insert({'client_id': id, 'coord': location})

    if (len(h_location) != 0) and location != "0.000000,0.000000":
        in_out = in_out_position(id)
        if in_out == 'outside':
            if h_location:
                h_location = h_location[0]['coord']
                clients_table = db.table('clients')
                oos = Query()
                results = clients_table.search(oos.client_id == id)
                oos = results[0]['OOS']
                radius = results[0]['geofence']
                if geofence(h_location, location, int(radius)) and not oos:
                    print('OUT OF Geofence')
                    clients_table = db.table('clients')
                    chat = Query()
                    all_chats = clients_table.search(chat.client_id.all(id))
                    print(all_chats)
                    all_chats = all_chats[0]
                    from bot_code import send
                    print(all_chats['chat_id'])
                    send(all_chats['chat_id'], 'Out of the safe zone! '
                                               'Use the /position command to check the current position')
                    update_flag = Query()
                    clients_table.update({'OOS':True}, (update_flag.client_id == id))

    db.close()


def geofence(house, current, maximum_distance=30):
    print('h_location', house)
    print('location', current)
    house = house.split(',')
    current = current.split(',')

    house = [float(i) for i in house]
    current = [float(i) for i in current]

    distance = geopy.distance.geodesic(house, current).m
    if distance > maximum_distance:
        return True
    return False

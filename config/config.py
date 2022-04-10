class Config:
    INVERTER_SERIAL = 12345678      # WiFi stick serial number
    INVERTER_IP = "192.168.1.1"     # IP address of inverter
    INVERTER_PORT = 8899            # Port number
    MODIFIED_METRICS = True         # Enable modified metrics
    LONGITUDE = -6.259159           # Current location (click on your home in google maps to see your co-ordinates)
    LATITUDE = 53.347681            # Current location
    MQTT_SERVER = "192.168.1.2"     # IP address of MQTT server
    MQTT_PORT = 1883                # Port number of MQTT server
    MQTT_KEEPALIVE = 60             # MQTT keepalive
    MQTT_TOPIC_INVERTER = "solis/METRICS"       # MQTT topic to use for inverter
    MQTT_TOPIC_MYENERGI = "myenergi/METRICS"    # MQTT topic to use for Myenergi
    DB_HOST = "192.168.1.2"         # DB IP
    DB_DATABASE = 'db'              # DB
    DB_USERNAME = 'user'            # DB user
    DB_PASSWORD = 'pass'            # DB password
    MYE_USER = "12341234"                       # Myenergi hub serial number
    MYE_PASSWORD = "asdfasdfasdfasdfd"         # Myenergi API key. See https://myenergi.info/api-keys-t5185.html
    FORECAST_FACTOR_INITIAL = 8     # Only used for first forecast when have no history
  


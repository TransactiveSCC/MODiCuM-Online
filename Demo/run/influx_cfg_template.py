# INFLUX CONFIG
influx_logging = True
influx = "cloud"  # "local"
if influx == "cloud":
    bucket = "mv2"
    org = "<your org e.g. yourname@email.com>"
    token = "<your token, e.g. abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghij>"
    url = "<influx url e.g.https://us-central1-1.gcp.cloud2.influxdata.com/>"
elif influx == "local":
    bucket = "modicumdb"
    org = "modicum"
    token = "<your token, e.g. abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghij>""
    # Store the URL of your InfluxDB instance
    url = "<influx url e.g. http://10.0.0.100:8086>"
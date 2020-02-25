#!/usr/bin/env python3

from websocket import create_connection
import json

CONNECT_STRING = "ws://127.0.0.1:6038/router-info"

MSGS = [('{"router":"::1"}',
        '{"router":  "0000:0000:0000:0001", "muxs": "b827:ebff:fee7:7681", "uri": "ws://0.0.0.0:6038/router-0000:0000:0000:0001"}'),
        ('{"router":"b827:ebff:fee7:7681"}',
        '{"router":  "b827:ebff:fee7:7681", "muxs": "b827:ebff:fee7:7682", "uri": "ws://0.0.0.0:6038/router-0000:0000:0000:0002"}'),
        ('{"router":"2::1"}',
        '{"router": "0002:0000:0000:0001", "error": "Unknown LoRaWAN Radio GTW (0002:0000:0000:0001)"}')]

    
def test_ws_chat(connect_string, msg, answer):
    ws = create_connection(connect_string)

    print("Sending request:" + msg)
    ws.send(msg)
    result =  ws.recv()
    print("Received '%s'" % result)
    recv_data = json.loads(result)
    expected_data = json.loads(answer)
    assert recv_data == expected_data, "Result not as expected"
    ws.close()

for msg, answer in MSGS:
    test_ws_chat(CONNECT_STRING, msg, answer)

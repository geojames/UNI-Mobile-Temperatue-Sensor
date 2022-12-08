# -*- coding: utf-8 -*-
# VERSION  5.4, July 2022
# FOR Circuit Pyhton vers. 6.3 (2021-06-01)

import time
import board
import busio
import displayio
import digitalio
import adafruit_ssd1306
import adafruit_sht4x
import adafruit_mlx90614
import adafruit_bh1750
import adafruit_gps
import neopixel

run = True
i2c = busio.I2C(board.SCL1, board.SDA1)
uart = busio.UART(board.TX, board.RX, baudrate=9600)

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel.fill((255, 0, 0))
log_switch = digitalio.DigitalInOut(board.D1)
log_switch.direction = digitalio.Direction.INPUT
log_switch.pull = digitalio.Pull.DOWN
oled_reset = digitalio.DigitalInOut(board.D0)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3D, reset=oled_reset)
display.fill(1)
display.show()
WIDTH = 128
HEIGHT = 64
text = "GEOTREE TEMP LOGGER\nVers. 0.54 + July21"
display.fill(0)
display.text(text, 7, 7, 1)
display.show()
try:
    sht = adafruit_sht4x.SHT4x(i2c)
    sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
except:
    text = "ERROR:\nTemp Sensor Not Found"
    display.fill(0)
    display.text(text, 7, 0, 1)
    display.show()
try:
    mlx = adafruit_mlx90614.MLX90614(i2c)
except:
    text = "ERROR:\nSurface Not Found"
    display.fill(0)
    display.text(text, 7, 0, 1)
    display.show()
try:
    lux = adafruit_bh1750.BH1750(i2c)
except:
    text = "ERROR:\nLight Not Found"
    display.fill(0)
    display.text(text, 7, 0, 1)
    display.show()
try:
    gps = adafruit_gps.GPS_GtopI2C(i2c)
    gps.send_command(b"PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
    gps.send_command(b"PMTK220,500")
    gps.update()
except:
    text = "ERROR:\nGPS Not Found"
    display.fill(0)
    display.text(text, 7, 0, 1)
    display.show()

last_print = time.monotonic()
while log_switch.value is True:
    text = "!!!!!!\nTurn Log Swictch\nto OFF to continue\n!!!!!!"
    display.fill(0)
    display.text(text, 7, 0, 1)
    display.show()
    pixel.fill((255, 0, 0))
    time.sleep(0.5)
fix_count = 0
while gps.has_fix is False:
    text = "Waiting for GPS fix"
    gps.update()
    current = time.monotonic()
    if current - last_print >= 1:
        last_print = current
        if fix_count == 0:
            display.fill(0)
            display.text(text, 7, 8, 1)
            display.rect(0, 18, int(WIDTH * 0.25), 6, 1)
            display.show()
            pixel.fill((255, 0, 0))
        elif fix_count == 1:
            display.rect(0, 18, int(WIDTH * 0.5), 6, 1)
            display.show()
            pixel.fill((50, 0, 0))
        elif fix_count == 3:
            display.rect(0, 18, int(WIDTH * 0.75), 6, 1)
            display.show()
            pixel.fill((255, 0, 0))
        elif fix_count == 4:
            display.rect(0, 18, int(WIDTH), 6, 1)
            display.show()
            pixel.fill((50, 0, 0))
        fix_count += 1
        if fix_count >= 5:
            fix_count = 0
file_num = 1
ready_sw = 0
print("GPS WAITING: %i" % gps.in_waiting)

while gps.in_waiting > 24:
    data = gps.read(200)
    print("flush...")
while run == True:
    if log_switch.value is False:
        if ready_sw == 0:
            gps.update()
            log_state = 0
            pixel.fill((0, 255, 0))
            display.fill(0)
            text = "GPS READY...\n  Toggle Switch\n  to Start Logging"
            display.text(text, 7, 2, 1)
            display.show()
            time.sleep(1.0)
            ready_sw = 1
    elif log_switch.value is True:
        gps.update()
        current = time.monotonic()
        # print("*** Time *** %0.3f"%(current - last_print))
        if log_state == 0:
            log_state = 1
            ready_sw = 0
            ready_sw = 0
            fname = "%02d%02d%02d%02d.TXT" % (
                int(str(gps.timestamp_utc.tm_year)[-2:]),
                gps.timestamp_utc.tm_mon,
                gps.timestamp_utc.tm_mday,
                file_num,
            )
            uart.write(bytearray("###\r"))
            time.sleep(0.5)
            uart.write(bytearray("ls\r"))
            f_list = uart.read(2000)
            print(f_list)
            if f_list is None:
                display.fill(0)
                text = "NO SD CARD DETECTED\n-Insert card and\n restart unit"
                pixel.fill((255, 0, 0))
                display.text(text, 7, 2, 1)
                display.show()
                run = False
                break

            else:
                while fname in str(f_list):
                    print("Next: %s" % fname)
                    file_num += 1
                    fname = "%02d%02d%02d%02d.TXT" % (
                        int(str(gps.timestamp_utc.tm_year)[-2:]),
                        gps.timestamp_utc.tm_mon,
                        gps.timestamp_utc.tm_mday,
                        file_num,
                    )
                uart.write(bytearray("append " + fname + "\r"))
                time.sleep(0.5)
                print(fname)
                pixel.fill((0, 0, 255))
                display.fill(0)
                text = "Output File = \n \n  " + fname
                display.text(text, 7, 2, 1)
                display.show()
                time.sleep(5.0)
                log_start_time = time.monotonic()
                file_num += 1
                #gps.update()

        data = gps._read_sentence()
        print(data)  # this is a bytearray type
        if data is not None:
            # convert bytearray to string
            # data_string = "".join([chr(b) for b in data])
            # print(data_string, end="")

            uart.write(bytearray(data + "\n"))
            time.sleep(0.1)

            #print('TIME:'+data[7:9]+':'+data[9:11]+':'+data[11:13])
            temp, rel_hum = sht.measurements
            mlx_atemp = mlx.ambient_temperature
            mlx_otemp = mlx.object_temperature
            light = lux.lux
            sens_data = ">,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f\n" % (
                temp,
                rel_hum,
                mlx_atemp,
                mlx_otemp,
					light
            )
            uart.write(bytearray(sens_data))
            time.sleep(0.1)
            print("write...")
            display.fill(0)
            log_cur_time = time.monotonic() - log_start_time
            #print(log_cur_time)
            log_cur_lbl = "Logging Time + %02d:%02d\n" % (
                log_cur_time // 60,
                log_cur_time - (log_cur_time // 60) * 60,
            )
            text = log_cur_lbl + "Temp: %0.1f C\nHum:  %0.1f %%\nSurf: %0.1f C  L:%i" % (
                temp,
                rel_hum,
                mlx_otemp,
					light
            )
            display.text(text, 0, 0, 1)
            display.show()

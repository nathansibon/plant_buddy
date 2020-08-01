# raspberry_pi_plant_datalogger
Datalogger for RPI written in python 3 for monitoring environmental factors important for plant health and growth

Welcome to the setup!

If you were wondering, i did consider automating this with a script, 
but i am... well... bad at programming and would have no way to test my janky code on your machine so we're stuck with a manual install!

Here's the basic setup steps:

0. Set up your Pi and make sure you have uninterrupted internet access (duh)

1. Make sure your default python interpreter is running python 3.7 or later!

2. Install any of the following missing modules (I've noted my current version for troubleshooting purposes):

    pandas        1.0.3     data analysis
    sqlite3       ?         database reading/writing
    numpy         1.16.2    calculations
    pyowm         3.0.0     openweathermap, source for outdoor weather
    matplotlib    3.0.2     creating charts
    flask         1.0.2     basic webserver for python
    flask_wtf	  0.14.3    flask implementation of WTForms (for new features coming soon!) this should auto-install WTForms as well


3. For these two modules, follow the DHT22 setup instructions from adafruit https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup

    board         required module for the adafruit_dht library
    adafruit_dht  reads the dht22 temperature and humidity sensor


4. Also hook up the DHT22 sensor per adafruit's instruction. I'm using the 3v power because i may want the 5v for something else later. 
	It still works fine thanks to some error handling/noise reduction in the read code. You may need to edit the pin called in function_library -> get_indoor_weather()

5. Copy all the files to a new directory of your liking. Mine is in a samba shared folder so i can easily access all the files from 
	my windows laptop but whatever works for you.

6. Edit the config.py file. This is where a lot of important user (you) supplied global variables are kept. 
	These can be edited at any time as you change your setup (such as move to a different room). You'll need to find a few things:

    a) Sign up for an API key on Openweathermap.org (https://openweathermap.org/api)

    b) Get your address' lat and long from either google maps (it's hidden in the address bar after you search your address) or another tool (https://developer.mapquest.com/documentation/tools/latitude-longitude-finder/)

    c) Find your Pi's serial number, it seems weird now but if you were to use multiple Pi's to measure many places at once this will help you decipher which is which. It's written on the motherboard, or you can do something crazy to get it from the shell (https://raspberrypi.stackexchange.com/questions/2086/how-do-i-get-the-serial-number) or by using the function getserial() in the function_library.py file

    d) In the 'Sensors' dictionary, add your sensors information. This is just a list for yourself, the code doesn't actually reference it in any way but I find it's helpful to have everything in one place. The 'Pin' attribute is whatever the data pin is on your GPIO board (the yellow wire)

    e) The rest of the file should (hopefully) be pretty self explanatory. Feel free to keep track of whatever extra info you'd like here, just make sure you put your notes in as python comments (prefix each line with #) to avoid errors.


7. Check that everything is working by running the 'collect data.py' file from the shell. 
	Errors (if any) will be written to a log file stored in /logs/collect_data.log

8. Update your Crontab file with the following lines. Open this file by entering 'crontab -e' into the shell. 
	Be sure to update the path to your directory! 
	This will run the collect_data script every 15 mins, and the process_daily script once a day just after midnight. 
	For more info on using crontab and syntax (https://crontab.guru/)
	The section after >> is the location of the log file. you can skip this i suppose but it makes any troubleshooting down the road a lot easier.

    	*/15 * * * * /usr/bin/python3 /home/pi/share/env_datalogger/collect_data.py >> /home/pi/share/env_datalogger/logs/collect_data.log
    	10 0 * * * /usr/bin/python3 /home/pi/share/env_datalogger/process_daily.py >> /home/pi/share/env_datalogger/logs/process_daily.log

9. Start the Flask webserver. The most reliable way I've found for a headless Pi setup (i.e. no monitor keyboard or mouse connected) is by setting up a VNC connection 
	(start at step 10 https://desertbot.io/blog/headless-raspberry-pi-4-remote-desktop-vnc-setup) and running the script from a new shell window (do not close the window)
	You can also look into writing a custom daemon to wrap the webserver script (good luck) or using other methods from an SSH shell like 'nohup' or 'screen' 
	but i didn't seem to have great luck there and makes it hard to troubleshoot errors when the server crashes from an error.
	
	9.1 another way to auto-start the flask server at boot (that's working for me so far...) is to add another line to your Crontab file. Good for power outages etc.
	
		@reboot /usr/bin/python3 /home/pi/share/env_datalogger/webserver.py &

10. When flask starts, you'll see both the port you'll need to access the data webpage

	'Running on http://0.0.0.0:5000' - 5000 is the port you webserver is running on

11. Find your Pi's LOCAL IP address. Chances are you already know this from setting up SSH, but you can also log into the admin panel of your router, or get it from 
	the shell using 'ifconfig' and looking for addresses starting with '192.168.0.X'

12. Open your webbrowser on your phone/laptop/whatever and navigate to the address and port of your pi's webserver (e.x. 192.168.0.1:5000). 
	Bookmark this page for easy access.



that's it! so far...

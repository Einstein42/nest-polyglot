# nest-polyglot
This is the Nest Poly for the ISY Polyglot interface. 
(c) Einstein.42 aka James Milne. MIT license. 

#Requirements
>sudo pip install python-nest

Install:

1. Go to your polyglot/config/node_servers/ folder.
..* > git clone https://github.com/Einstein42/nest-polyglot.git
..* > cd nest-polyglot
2. Add your username and password to a new file called login.py

> echo USERNAME='"<username>"' >> login.py

> echo PASSWORD='"<password>"' >> login.py
3. Restart Polyglot and add the Nest nodeserver via web interface If you have the Polyglot systemctl script installed do this:
> sudo systemctl restart polyglot
4. Download the profile from the Nest Polyglot configuration page and copy baseURL
5. Add as NodeServer in ISY. Profile Number MUST MATCH what you put in Polyglot
6. Upload profile you download from Polyglot to ISY
7. Reboot ISY
8. Upload Profile again in the node server (quirk of ISY)
9. Reboot ISY again (quirk of ISY)
10. Once ISY is back up, go to Polyglot and restart the Nest nodeserver.
11. All Thermostats will be automatically added as 'Nest <Structure> <Location>'
12. Write programs and enjoy.


I built this on ISY version 5.0.2 and the polyglot unstable-release version 0.0.1 from 
https://github.com/UniversalDevicesInc/Polyglot

# Notes
The Nest Polyglot polls the Nest API every 30 seconds due to Nest anti-flooding mechanisms that
temporarily disable queries to the API. So if anything is updated outside of ISY it could take
up to 30 seconds to be reflected in the ISY interface.

Nest only updates the structure api every 600 seconds (5 minutes). This only affects AWAY state
so if your device is set away or returned from away it will take up to 5 minutes to reflect in
your ISY node.

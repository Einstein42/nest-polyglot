# nest-polyglot

#Requirements
sudo pip install python-nest

Install:

1. Go to your polyglot/config/node_servers/ folder
2. git clone https://github.com/Einstein42/nest-polyglot.git
3. cd nest-polyglot, then add your username and password
4. echo USERNAME='"<username>"' >> login.py
5. echo PASSWORD='"<password>"' >> login.py
6. Restart Polyglot and add the Nest nodeserver via web interface
7. Download profile and copy baseURL from polyglot
8. Add as NodeServer in ISY. Upload profile.
9. Reboot ISY
10. Upload Profile again in the node server (quirk of ISY)
11. Reboot ISY again (quirk of ISY)
12. Once ISY is back up, go to Polyglot and restart the Nest nodeserver.
13. All Thermostats will be automatically added as 'Nest <Structure> <Location>'
14. Write programs and enjoy.


I build this on ISY version 5.0.2 and the current polyglot DEV version from 
https://github.com/UniversalDevicesInc/Polyglot



